/// Direct-to-MinIO upload client (Phase 8, Step 6).
///
/// Flow:
///   1. POST /uploads/init  → returns presigned upload_url (never logged)
///   2. Dio PUT to upload_url with no Authorization header
///   3. POST /uploads/complete
///   4. GET /uploads/{id}/status (poll until terminal)
///
/// Security invariants:
///   - upload_url is used immediately and never stored to disk.
///   - The PUT request is made with a fresh Dio instance carrying NO auth header.
///   - Do not retry the PUT after a partial write — restart from init.
///   - complete() must not be called twice for the same uploadId.
///
/// Background / resume:
///   - expires_at is checked before the PUT; expired → UploadExpiredError.
///   - Callers should restart the full flow (init → put → complete) on expiry.

import 'dart:io';
import 'dart:async';

import 'package:dio/dio.dart';

import 'package:ecole_platform/data/api/api_client.dart';

// ── Constants ────────────────────────────────────────────────────────────────

/// Files larger than this are routed to direct upload.
const int directUploadThresholdBytes = 10 * 1024 * 1024; // 10 MB

const Duration _pollInterval = Duration(seconds: 2);
const Duration _pollTimeout = Duration(minutes: 5);

// ── Enums ────────────────────────────────────────────────────────────────────

/// Mirrors the backend UploadKind enum.
enum UploadKind {
  submissionFile,
  contentAsset,
  video,
  audio,
  assignmentPdf,
}

extension UploadKindJson on UploadKind {
  String get jsonValue => switch (this) {
        UploadKind.submissionFile => 'submission_file',
        UploadKind.contentAsset => 'content_asset',
        UploadKind.video => 'video',
        UploadKind.audio => 'audio',
        UploadKind.assignmentPdf => 'assignment_pdf',
      };
}

/// Mirrors the backend UploadState enum.
enum UploadState {
  preparing,
  uploading,
  processing,
  available,
  failed,
  quarantined,
}

// ── Scope ────────────────────────────────────────────────────────────────────

class UploadScope {
  final String schoolId;
  final String? contentItemId;
  final String? submissionId;

  const UploadScope({
    required this.schoolId,
    this.contentItemId,
    this.submissionId,
  });

  Map<String, dynamic> toJson() => {
        'school_id': schoolId,
        if (contentItemId != null) 'content_item_id': contentItemId,
        if (submissionId != null) 'submission_id': submissionId,
      };
}

// ── Result ───────────────────────────────────────────────────────────────────

class DirectUploadResult {
  final String uploadId;
  final UploadState state;
  final String? targetId;
  final String? targetKind;

  const DirectUploadResult({
    required this.uploadId,
    required this.state,
    this.targetId,
    this.targetKind,
  });
}

// ── Errors ───────────────────────────────────────────────────────────────────

/// The presigned URL has expired before the PUT was attempted.
/// Callers should restart from initUpload.
class UploadExpiredError implements Exception {
  const UploadExpiredError();

  @override
  String toString() => 'UploadExpiredError: presigned URL has expired';
}

/// The PUT to object storage returned a non-2xx status.
class UploadPutError implements Exception {
  final int statusCode;

  const UploadPutError(this.statusCode);

  @override
  String toString() => 'UploadPutError: PUT returned HTTP $statusCode';
}

/// The backend virus scan quarantined the file.
class UploadQuarantinedError implements Exception {
  const UploadQuarantinedError();

  @override
  String toString() =>
      'UploadQuarantinedError: file failed security scan and was quarantined';
}

/// Upload timed out waiting for backend processing.
class UploadTimeoutError implements Exception {
  const UploadTimeoutError();

  @override
  String toString() => 'UploadTimeoutError: backend processing timed out';
}

// ── Routing helper ───────────────────────────────────────────────────────────

/// Returns true when this file/kind must use the direct upload path.
///
/// Video and audio always use direct upload (streaming files).
/// Any file larger than [directUploadThresholdBytes] also uses direct upload.
bool shouldUseDirect(File file, UploadKind kind) {
  if (kind == UploadKind.video || kind == UploadKind.audio) return true;
  return file.lengthSync() > directUploadThresholdBytes;
}

// ── Internal: init ───────────────────────────────────────────────────────────

class _InitResponse {
  final String uploadId;
  final String uploadUrl;
  final String objectKey;
  final DateTime expiresAt;
  final int maxSizeBytes;

  const _InitResponse({
    required this.uploadId,
    required this.uploadUrl,
    required this.objectKey,
    required this.expiresAt,
    required this.maxSizeBytes,
  });

  factory _InitResponse.fromJson(Map<String, dynamic> json) {
    return _InitResponse(
      uploadId: json['upload_id'] as String,
      uploadUrl: json['upload_url'] as String,
      objectKey: json['object_key'] as String,
      expiresAt: DateTime.parse(json['expires_at'] as String).toUtc(),
      maxSizeBytes: (json['max_size_bytes'] as num).toInt(),
    );
  }
}

Future<_InitResponse> _initUpload({
  required ApiClient api,
  required UploadKind kind,
  required UploadScope scope,
  required File file,
}) async {
  final filename = file.path.split('/').last;
  final sizeBytes = file.lengthSync();

  final body = <String, dynamic>{
    'kind': kind.jsonValue,
    'filename': filename,
    'size_bytes': sizeBytes,
    ...scope.toJson(),
  };

  final resp = await api.post('/uploads/init', body: body);
  return _InitResponse.fromJson(resp.data);
}

// ── Internal: PUT to object storage ─────────────────────────────────────────

/// PUT the file to the presigned URL.
///
/// A fresh Dio instance is used intentionally: it carries NO Authorization
/// header, no app interceptors, and no retry logic (partial PUT must restart
/// from init).
Future<void> _putToStorage(
  String url,
  File file, {
  void Function(int sent, int total)? onSendProgress,
}) async {
  final externalDio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(minutes: 10),
    ),
  );

  try {
    final response = await externalDio.put(
      url,
      data: file.openRead(),
      options: Options(
        headers: {
          'Content-Type': _mimeTypeOf(file.path),
          'Content-Length': file.lengthSync(),
        },
        // Validate only 2xx; anything else is a hard failure.
        validateStatus: (status) => status != null && status >= 200 && status < 300,
      ),
      onSendProgress: onSendProgress,
    );

    final status = response.statusCode ?? 0;
    if (status < 200 || status >= 300) {
      throw UploadPutError(status);
    }
  } on DioException catch (e) {
    final status = e.response?.statusCode;
    if (status != null && (status < 200 || status >= 300)) {
      throw UploadPutError(status);
    }
    rethrow;
  }
}

String _mimeTypeOf(String path) {
  final ext = path.split('.').last.toLowerCase();
  return switch (ext) {
    'mp4' || 'mov' || 'avi' || 'mkv' => 'video/mp4',
    'mp3' => 'audio/mpeg',
    'wav' => 'audio/wav',
    'aac' => 'audio/aac',
    'pdf' => 'application/pdf',
    'jpg' || 'jpeg' => 'image/jpeg',
    'png' => 'image/png',
    _ => 'application/octet-stream',
  };
}

// ── Internal: complete ───────────────────────────────────────────────────────

Future<void> _completeUpload({
  required ApiClient api,
  required String uploadId,
  required int sizeBytes,
}) async {
  const maxRetries = 3;
  var delay = const Duration(milliseconds: 500);

  for (var attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      await api.post(
        '/uploads/complete',
        body: {
          'upload_id': uploadId,
          'size_bytes': sizeBytes,
        },
      );
      return;
    } on ApiClientError catch (e) {
      // Do not retry 4xx — client-side problem (bad state, wrong size, etc.)
      if (e.statusCode >= 400 && e.statusCode < 500) rethrow;
      if (attempt == maxRetries) rethrow;
    } catch (_) {
      if (attempt == maxRetries) rethrow;
    }
    await Future<void>.delayed(delay);
    delay = delay * 2 > const Duration(seconds: 4)
        ? const Duration(seconds: 4)
        : delay * 2;
  }
}

// ── Internal: poll ───────────────────────────────────────────────────────────

class _StatusResponse {
  final String uploadId;
  final UploadState state;
  final String? targetId;
  final String? targetKind;
  final String? errorMessage;

  const _StatusResponse({
    required this.uploadId,
    required this.state,
    this.targetId,
    this.targetKind,
    this.errorMessage,
  });

  factory _StatusResponse.fromJson(Map<String, dynamic> json) {
    final stateStr = json['state'] as String? ?? 'processing';
    final state = switch (stateStr) {
      'preparing' => UploadState.preparing,
      'uploading' => UploadState.uploading,
      'processing' => UploadState.processing,
      'available' => UploadState.available,
      'failed' => UploadState.failed,
      'quarantined' => UploadState.quarantined,
      _ => UploadState.processing,
    };
    return _StatusResponse(
      uploadId: json['upload_id'] as String,
      state: state,
      targetId: json['target_id'] as String?,
      targetKind: json['target_kind'] as String?,
      errorMessage: json['error_message'] as String?,
    );
  }
}

const _terminalStates = {
  UploadState.available,
  UploadState.failed,
  UploadState.quarantined,
};

Future<DirectUploadResult> _pollUntilDone({
  required ApiClient api,
  required String uploadId,
  void Function(UploadState)? onStateChange,
}) async {
  final deadline = DateTime.now().add(_pollTimeout);
  Duration interval = _pollInterval;
  const maxInterval = Duration(seconds: 10);

  while (DateTime.now().isBefore(deadline)) {
    await Future.delayed(interval);

    final resp = await api.get('/uploads/$uploadId/status');
    final status = _StatusResponse.fromJson(resp.data);

    onStateChange?.call(status.state);

    if (_terminalStates.contains(status.state)) {
      if (status.state == UploadState.quarantined) {
        throw const UploadQuarantinedError();
      }
      if (status.state == UploadState.failed) {
        throw Exception(
          status.errorMessage ?? 'Upload processing failed',
        );
      }
      return DirectUploadResult(
        uploadId: status.uploadId,
        state: status.state,
        targetId: status.targetId,
        targetKind: status.targetKind,
      );
    }

    // Exponential back-off (2 s → 4 s → … → 10 s max)
    final nextMs = (interval.inMilliseconds * 1.5).round();
    interval = Duration(milliseconds: nextMs) < maxInterval
        ? Duration(milliseconds: nextMs)
        : maxInterval;
  }

  throw const UploadTimeoutError();
}

// ── Public orchestrator ──────────────────────────────────────────────────────

/// Orchestrate a full direct upload: init → PUT → complete → poll.
///
/// [onStateChange] is called with each [UploadState] transition so the UI can
/// display preparing / uploading / processing / available states.
///
/// [onProgress] receives (bytesUploaded, totalBytes) during the PUT phase.
Future<DirectUploadResult> directUpload({
  required ApiClient api,
  required UploadKind kind,
  required UploadScope scope,
  required File file,
  void Function(UploadState)? onStateChange,
  void Function(int sent, int total)? onProgress,
}) async {
  onStateChange?.call(UploadState.preparing);

  // Step 1: init
  final init = await _initUpload(api: api, kind: kind, scope: scope, file: file);

  // Guard: check expiry before attempting PUT (important after background resume)
  if (DateTime.now().toUtc().isAfter(init.expiresAt)) {
    throw const UploadExpiredError();
  }

  // Step 2: PUT (no auth header, fresh Dio)
  onStateChange?.call(UploadState.uploading);
  await _putToStorage(
    init.uploadUrl,
    file,
    onSendProgress: onProgress,
  );

  // Step 3: complete (do not call twice — no retry on network error here)
  onStateChange?.call(UploadState.processing);
  await _completeUpload(
    api: api,
    uploadId: init.uploadId,
    sizeBytes: file.lengthSync(),
  );

  // Step 4: poll
  final result = await _pollUntilDone(
    api: api,
    uploadId: init.uploadId,
    onStateChange: onStateChange,
  );

  return result;
}
