import 'dart:io';

import 'package:dio/dio.dart';

import 'package:ecole_platform/core/network/api_client.dart';

class SignedUrlCache {
  final ApiClient _api;
  final DateTime Function() _now;

  final Map<String, _CachedSignedUrl> _cache = {};
  final Map<String, Future<DownloadMetadata>> _inFlight = {};

  SignedUrlCache({
    required ApiClient api,
    DateTime Function()? now,
  })  : _api = api,
        _now = now ?? DateTime.now;

  Future<String> getUrl(String path, {bool forceRefresh = false}) async {
    final metadata = await getMetadata(path, forceRefresh: forceRefresh);
    return metadata.downloadUrl;
  }

  Future<DownloadMetadata> getMetadata(
    String path, {
    bool forceRefresh = false,
  }) async {
    final key = _key(path);
    final cached = _cache[key];
    final now = _now().toUtc();
    if (!forceRefresh && cached != null && cached.usableUntil.isAfter(now)) {
      return cached.metadata;
    }

    if (!forceRefresh && _inFlight.containsKey(key)) {
      return _inFlight[key]!;
    }

    final future = _api.fetchSignedUrl(path).then((metadata) {
      final fetchedAt = _now().toUtc();
      _cache[key] = _CachedSignedUrl(
        metadata: metadata,
        usableUntil: _usableUntil(metadata, fetchedAt),
      );
      return metadata;
    });
    _inFlight[key] = future;

    try {
      return await future;
    } finally {
      if (identical(_inFlight[key], future)) {
        _inFlight.remove(key);
      }
    }
  }

  Future<DownloadMetadata> refresh(String path) {
    return getMetadata(path, forceRefresh: true);
  }

  void invalidate(String path) {
    _cache.remove(_key(path));
  }

  void clearExpired() {
    final now = _now().toUtc();
    _cache.removeWhere((_, cached) => !cached.usableUntil.isAfter(now));
  }

  void clear() {
    _cache.clear();
    _inFlight.clear();
  }

  Future<File> download(
    String path, {
    required String savePath,
    void Function(int received, int total)? onReceiveProgress,
  }) async {
    var metadata = await getMetadata(path);
    try {
      return await _api.downloadSignedUrl(
        metadata.downloadUrl,
        savePath: savePath,
        onReceiveProgress: onReceiveProgress,
      );
    } on DioException catch (error) {
      if (error.response?.statusCode != HttpStatus.forbidden) {
        rethrow;
      }
      invalidate(path);
      metadata = await refresh(path);
      return _api.downloadSignedUrl(
        metadata.downloadUrl,
        savePath: savePath,
        onReceiveProgress: onReceiveProgress,
      );
    }
  }

  DateTime _usableUntil(DownloadMetadata metadata, DateTime fetchedAt) {
    final ttl = metadata.expiresAt.toUtc().difference(fetchedAt);
    if (ttl <= Duration.zero) {
      return fetchedAt;
    }
    return fetchedAt
        .add(Duration(milliseconds: (ttl.inMilliseconds * 0.8).floor()));
  }

  String _key(String path) => path.trim();
}

class _CachedSignedUrl {
  final DownloadMetadata metadata;
  final DateTime usableUntil;

  const _CachedSignedUrl({
    required this.metadata,
    required this.usableUntil,
  });
}
