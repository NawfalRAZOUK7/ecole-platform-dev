/// Dio-based API client with mandatory headers per DEC-E2-022.
///
/// Headers: Authorization, Accept-Language, X-Correlation-Id,
///          X-Client-Version, X-Client-Platform
/// Features: auto-retry with exponential backoff + jitter,
///           401 auto-refresh, cursor pagination.
///
/// Reference: S-091, Pack E2 Chapter 6

import 'dart:io';
import 'dart:math';
import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

import 'package:ecole_platform/shared/secure_storage.dart';

const String _apiBase = '/api/v1';
const String _clientVersion = '0.1.0';
const int _maxRetries = 3;
const _uuid = Uuid();

/// Standard API error shape from backend.
class ApiError {
  final String code;
  final String message;
  final String category;
  final bool retryable;
  final String? correlationId;

  const ApiError({
    required this.code,
    required this.message,
    required this.category,
    required this.retryable,
    this.correlationId,
  });

  factory ApiError.fromJson(Map<String, dynamic> json) {
    return ApiError(
      code: json['code'] as String? ?? 'ERR-SYS-000',
      message: json['message'] as String? ?? 'Unknown error',
      category: json['category'] as String? ?? 'system',
      retryable: json['retryable'] as bool? ?? false,
      correlationId: json['correlation_id'] as String?,
    );
  }
}

class ApiClientError implements Exception {
  final int statusCode;
  final ApiError apiError;

  const ApiClientError(this.statusCode, this.apiError);

  @override
  String toString() => 'ApiClientError($statusCode): ${apiError.message}';
}

/// Paginated API response envelope.
class ApiListResponse<T> {
  final List<T> data;
  final String? nextCursor;
  final bool hasMore;

  const ApiListResponse({
    required this.data,
    this.nextCursor,
    required this.hasMore,
  });
}

/// Single-item API response envelope.
class ApiResponse<T> {
  final T data;

  const ApiResponse({required this.data});
}

/// Metadata returned by backend download endpoints with `?as=metadata`.
class DownloadMetadata {
  final String downloadUrl;
  final DateTime expiresAt;
  final String mimeType;
  final int size;
  final String filename;
  final String? etag;

  const DownloadMetadata({
    required this.downloadUrl,
    required this.expiresAt,
    required this.mimeType,
    required this.size,
    required this.filename,
    this.etag,
  });

  factory DownloadMetadata.fromJson(Map<String, dynamic> json) {
    return DownloadMetadata(
      downloadUrl: json['download_url'] as String,
      expiresAt: DateTime.parse(json['expires_at'] as String).toUtc(),
      mimeType: json['mime_type'] as String? ?? 'application/octet-stream',
      size: (json['size'] as num?)?.toInt() ?? 0,
      filename: json['filename'] as String? ?? 'download',
      etag: json['etag'] as String?,
    );
  }
}

class _MetadataRequest {
  final String path;
  final Map<String, dynamic> queryParameters;

  const _MetadataRequest(this.path, this.queryParameters);
}

/// Central API client — singleton managed by Riverpod.
class ApiClient {
  final Dio _dio;
  final SecureTokenStorage _tokenStorage;
  String _locale;
  String? _accessToken;
  Future<String?>? _refreshPromise;

  ApiClient({
    required SecureTokenStorage tokenStorage,
    required String baseUrl,
    String locale = 'fr',
  })  : _tokenStorage = tokenStorage,
        _locale = locale,
        _dio = Dio(BaseOptions(
          baseUrl: '$baseUrl$_apiBase',
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 15),
        ));

  void setLocale(String locale) => _locale = locale;
  void setAccessToken(String? token) => _accessToken = token;
  String? get accessToken => _accessToken;

  String resolveUrl(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }

    final normalizedPath =
        path.startsWith(_apiBase) ? path.substring(_apiBase.length) : path;
    final baseUrl = _dio.options.baseUrl.endsWith('/')
        ? _dio.options.baseUrl.substring(0, _dio.options.baseUrl.length - 1)
        : _dio.options.baseUrl;
    final absolutePath =
        normalizedPath.startsWith('/') ? normalizedPath : '/$normalizedPath';
    return '$baseUrl$absolutePath';
  }

  /// Build mandatory headers per E2 Chapter 6.
  Map<String, String> _headers({bool skipAuth = false}) {
    final headers = <String, String>{
      'Accept': 'application/json',
      'Accept-Language': _locale,
      'X-Correlation-Id': _uuid.v4(),
      'X-Client-Version': _clientVersion,
      'X-Client-Platform': Platform.isIOS ? 'ios' : 'android',
    };
    if (!skipAuth && _accessToken != null) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }
    return headers;
  }

  /// Generic request with retry + 401 refresh.
  Future<Response<dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? queryParameters,
    dynamic data,
    bool skipAuth = false,
    int retryCount = 0,
  }) async {
    try {
      final resp = await _dio.request(
        path,
        options: Options(
          method: method,
          headers: _headers(skipAuth: skipAuth),
        ),
        queryParameters: queryParameters,
        data: data,
      );
      return resp;
    } on DioException catch (e) {
      final statusCode = e.response?.statusCode;

      // 401 — try refresh once
      if (statusCode == 401 && !skipAuth && retryCount == 0) {
        final newToken = await _ensureRefresh();
        if (newToken != null) {
          return _request(method, path,
              queryParameters: queryParameters,
              data: data,
              skipAuth: skipAuth,
              retryCount: 1);
        }
      }

      // Extract API error
      final errorBody = e.response?.data;
      if (errorBody is Map<String, dynamic> && errorBody.containsKey('error')) {
        final apiError =
            ApiError.fromJson(errorBody['error'] as Map<String, dynamic>);

        // Retry on retryable errors with exponential backoff + jitter
        if (apiError.retryable && retryCount < _maxRetries) {
          final delay = _backoffDelay(retryCount);
          await Future.delayed(delay);
          return _request(method, path,
              queryParameters: queryParameters,
              data: data,
              skipAuth: skipAuth,
              retryCount: retryCount + 1);
        }

        throw ApiClientError(statusCode ?? 500, apiError);
      }

      throw ApiClientError(
          statusCode ?? 500,
          ApiError(
            code: 'ERR-NET-000',
            message: e.message ?? 'Network error',
            category: 'network',
            retryable: true,
          ));
    }
  }

  /// Exponential backoff with jitter per DEC-E2-022.
  Duration _backoffDelay(int retry) {
    final baseMs = min(1000 * pow(2, retry).toInt(), 10000);
    final jitter = Random().nextInt(500);
    return Duration(milliseconds: baseMs + jitter);
  }

  /// Deduplicated token refresh.
  Future<String?> _ensureRefresh() {
    _refreshPromise ??= _refreshAccessToken().whenComplete(() {
      _refreshPromise = null;
    });
    return _refreshPromise!;
  }

  Future<String?> _refreshAccessToken() async {
    try {
      final refreshToken = await _tokenStorage.getRefreshToken();
      if (refreshToken == null) {
        _accessToken = null;
        return null;
      }

      final resp = await _dio.post(
        '/auth/refresh',
        options: Options(headers: {
          'Content-Type': 'application/json',
          'X-Correlation-Id': _uuid.v4(),
          'X-Client-Version': _clientVersion,
          'X-Client-Platform': Platform.isIOS ? 'ios' : 'android',
        }),
        data: {'refresh_token': refreshToken},
      );

      final body = resp.data as Map<String, dynamic>;
      final newToken = body['data']?['access_token'] as String?;
      if (newToken != null) {
        _accessToken = newToken;
        // Store new refresh token if returned
        final newRefresh = body['data']?['refresh_token'] as String?;
        if (newRefresh != null) {
          await _tokenStorage.saveRefreshToken(newRefresh);
        }
        return newToken;
      }
      _accessToken = null;
      return null;
    } catch (_) {
      _accessToken = null;
      return null;
    }
  }

  // ── Convenience methods ──

  Future<ApiResponse<Map<String, dynamic>>> get(String path,
      {Map<String, dynamic>? params}) async {
    final resp = await _request('GET', path, queryParameters: params);
    final body = resp.data as Map<String, dynamic>;
    return ApiResponse(data: body['data'] as Map<String, dynamic>);
  }

  Future<ApiListResponse<Map<String, dynamic>>> list(String path,
      {Map<String, dynamic>? params}) async {
    final resp = await _request('GET', path, queryParameters: params);
    final body = resp.data as Map<String, dynamic>;
    final items = (body['data'] as List<dynamic>).cast<Map<String, dynamic>>();
    final meta = body['meta'] as Map<String, dynamic>?;
    return ApiListResponse(
      data: items,
      nextCursor: meta?['next_cursor'] as String?,
      hasMore: meta?['has_more'] as bool? ?? false,
    );
  }

  Future<ApiResponse<Map<String, dynamic>>> post(String path,
      {dynamic body, bool skipAuth = false}) async {
    final resp = await _request('POST', path, data: body, skipAuth: skipAuth);
    final respBody = resp.data as Map<String, dynamic>;
    return ApiResponse(data: respBody['data'] as Map<String, dynamic>);
  }

  Future<ApiResponse<Map<String, dynamic>>> put(String path,
      {dynamic body}) async {
    final resp = await _request('PUT', path, data: body);
    final respBody = resp.data as Map<String, dynamic>;
    return ApiResponse(data: respBody['data'] as Map<String, dynamic>);
  }

  Future<ApiResponse<Map<String, dynamic>>> patch(String path,
      {dynamic body}) async {
    final resp = await _request('PATCH', path, data: body);
    final respBody = resp.data as Map<String, dynamic>;
    return ApiResponse(data: respBody['data'] as Map<String, dynamic>);
  }

  Future<ApiListResponse<Map<String, dynamic>>> postList(
    String path, {
    dynamic body,
  }) async {
    final resp = await _request('POST', path, data: body);
    final respBody = resp.data as Map<String, dynamic>;
    final items =
        (respBody['data'] as List<dynamic>).cast<Map<String, dynamic>>();
    final meta = respBody['meta'] as Map<String, dynamic>?;
    return ApiListResponse(
      data: items,
      nextCursor: meta?['next_cursor'] as String?,
      hasMore: meta?['has_more'] as bool? ?? false,
    );
  }

  Future<ApiResponse<Map<String, dynamic>>> delete(String path) async {
    final resp = await _request('DELETE', path);
    final respBody = resp.data as Map<String, dynamic>;
    return ApiResponse(data: respBody['data'] as Map<String, dynamic>);
  }

  Future<File> download(String path, {required String savePath}) async {
    final normalizedPath =
        path.startsWith('$_apiBase/') ? path.substring(_apiBase.length) : path;
    await _dio.download(
      normalizedPath,
      savePath,
      options: Options(headers: _headers()),
    );
    return File(savePath);
  }

  Future<DownloadMetadata> fetchSignedUrl(String path) async {
    final request = _metadataRequest(path);
    final resp = await _request(
      'GET',
      request.path,
      queryParameters: request.queryParameters,
    );
    final body = resp.data;
    if (body is! Map<String, dynamic>) {
      throw const ApiClientError(
        500,
        ApiError(
          code: 'ERR-DOWNLOAD-METADATA',
          message: 'Invalid download metadata response',
          category: 'system',
          retryable: false,
        ),
      );
    }
    return DownloadMetadata.fromJson(body);
  }

  Future<File> downloadSignedUrl(
    String signedUrl, {
    required String savePath,
    void Function(int received, int total)? onReceiveProgress,
  }) async {
    await _dio.download(
      signedUrl,
      savePath,
      options: Options(headers: const <String, String>{}),
      onReceiveProgress: onReceiveProgress,
    );
    return File(savePath);
  }

  _MetadataRequest _metadataRequest(String rawPath) {
    final trimmed = rawPath.trim();
    if (trimmed.isEmpty) {
      throw ArgumentError.value(rawPath, 'path', 'Path must not be empty');
    }

    final uri = Uri.parse(trimmed);
    final apiBaseUri = Uri.parse(_dio.options.baseUrl);
    String requestPath;
    final query = <String, dynamic>{};

    if (uri.hasScheme) {
      final sameBackend = uri.scheme == apiBaseUri.scheme &&
          uri.host == apiBaseUri.host &&
          uri.port == apiBaseUri.port;
      final apiPath = uri.path.startsWith(_apiBase);
      if (!sameBackend && !apiPath) {
        throw ArgumentError.value(
          rawPath,
          'path',
          'Signed URL metadata must be fetched from the backend API',
        );
      }
      requestPath = uri.path;
      query.addAll(_flattenQuery(uri.queryParametersAll));
    } else {
      requestPath = uri.path.isEmpty ? trimmed : uri.path;
      query.addAll(_flattenQuery(uri.queryParametersAll));
    }

    if (requestPath.startsWith(_apiBase)) {
      requestPath = requestPath.substring(_apiBase.length);
    }
    if (requestPath.isEmpty) {
      requestPath = '/';
    }
    if (!requestPath.startsWith('/')) {
      requestPath = '/$requestPath';
    }

    query['as'] = 'metadata';
    return _MetadataRequest(requestPath, query);
  }

  Map<String, dynamic> _flattenQuery(Map<String, List<String>> source) {
    return source.map((key, values) {
      if (values.length == 1) {
        return MapEntry(key, values.first);
      }
      return MapEntry(key, values);
    });
  }

  Future<ApiResponse<Map<String, dynamic>>> uploadFile(
    String path, {
    required File file,
    String fileField = 'file',
    Map<String, dynamic>? fields,
    void Function(int sent, int total)? onProgress,
  }) async {
    final formData = FormData();

    if (fields != null) {
      for (final entry in fields.entries) {
        if (entry.value == null) continue;
        formData.fields.add(MapEntry(entry.key, entry.value.toString()));
      }
    }

    formData.files.add(
      MapEntry(
        fileField,
        MultipartFile.fromFileSync(
          file.path,
          filename: file.path.split('/').last,
        ),
      ),
    );

    try {
      final resp = await _dio.post(
        path,
        data: formData,
        options: Options(headers: _headers()),
        onSendProgress: onProgress,
      );
      final body = resp.data as Map<String, dynamic>;
      return ApiResponse(data: body['data'] as Map<String, dynamic>);
    } on DioException catch (e) {
      final statusCode = e.response?.statusCode ?? 500;
      final errorBody = e.response?.data;
      if (errorBody is Map<String, dynamic> &&
          errorBody['error'] is Map<String, dynamic>) {
        throw ApiClientError(
          statusCode,
          ApiError.fromJson(errorBody['error'] as Map<String, dynamic>),
        );
      }
      throw ApiClientError(
        statusCode,
        ApiError(
          code: 'ERR-NET-000',
          message: e.message ?? 'Network error',
          category: 'network',
          retryable: false,
        ),
      );
    }
  }

  /// Upload files with multipart form data and progress tracking.
  Future<ApiResponse<Map<String, dynamic>>> uploadFiles(
    String path, {
    required List<File> files,
    Map<String, dynamic>? fields,
    void Function(int sent, int total)? onProgress,
  }) async {
    final formData = FormData();

    // Add fields
    if (fields != null) {
      for (final entry in fields.entries) {
        formData.fields.add(MapEntry(entry.key, entry.value.toString()));
      }
    }

    // Add files
    for (final file in files) {
      final fileName = file.path.split('/').last;
      formData.files.add(MapEntry(
        'files',
        await MultipartFile.fromFile(file.path, filename: fileName),
      ));
    }

    final resp = await _dio.post(
      '$_apiBase$path',
      data: formData,
      onSendProgress: onProgress,
    );

    final body = resp.data as Map<String, dynamic>;
    return ApiResponse(data: body['data'] as Map<String, dynamic>);
  }
}
