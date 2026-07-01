/// Unit tests for upload_client.dart (Phase 8 — direct-to-MinIO upload).
///
/// Strategy mirrors api_client_test.dart: each test spins up a real
/// HttpServer on a random port so we test actual HTTP behaviour with no mocks.
///
/// Tests covered:
///   shouldUseDirect — routing logic
///   directUpload    — happy path, quarantined, init failure, expired URL guard

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/core/network/upload_client.dart';

import '../helpers/test_services.dart';

// ── Server helpers (same pattern as api_client_test.dart) ────────────────────

typedef _Handler = Future<void> Function(HttpRequest request);

class _Server {
  _Server(this._server, this._sub);

  final HttpServer _server;
  final StreamSubscription<HttpRequest> _sub;

  String get baseUrl => 'http://${_server.address.host}:${_server.port}';

  Future<void> close() async {
    await _sub.cancel();
    await _server.close(force: true);
  }
}

Future<_Server> _startServer(_Handler handler) async {
  final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
  final sub = server.listen((request) async {
    try {
      await handler(request);
    } catch (e) {
      request.response.statusCode = HttpStatus.internalServerError;
      request.response.write(e.toString());
      await request.response.close();
    }
  });
  return _Server(server, sub);
}

Future<void> _json(HttpResponse res, int status, Object body) async {
  res.statusCode = status;
  res.headers.contentType = ContentType.json;
  res.write(jsonEncode(body));
  await res.close();
}

Future<Map<String, dynamic>> _readBody(HttpRequest req) async {
  final raw = await utf8.decoder.bind(req).join();
  if (raw.isEmpty) return {};
  return jsonDecode(raw) as Map<String, dynamic>;
}

// ── File helpers ─────────────────────────────────────────────────────────────

/// Create a real temp file of [sizeBytes] bytes.
Future<File> _makeFile(int sizeBytes, {String name = 'test.bin'}) async {
  final dir = await Directory.systemTemp.createTemp('upload_test_');
  final file = File('${dir.path}/$name');
  await file.writeAsBytes(List.filled(sizeBytes, 0));
  return file;
}

// ── Tests ────────────────────────────────────────────────────────────────────

void main() {
  // ── shouldUseDirect ────────────────────────────────────────────────────────

  group('shouldUseDirect', () {
    late File tinyFile;

    setUpAll(() async {
      tinyFile = await _makeFile(1024, name: 'tiny.pdf');
    });

    tearDownAll(() async {
      await tinyFile.parent.delete(recursive: true);
    });

    test('returns true for video regardless of size', () {
      expect(shouldUseDirect(tinyFile, UploadKind.video), isTrue);
    });

    test('returns true for audio regardless of size', () {
      expect(shouldUseDirect(tinyFile, UploadKind.audio), isTrue);
    });

    test('returns false for small content_asset below threshold', () {
      expect(shouldUseDirect(tinyFile, UploadKind.contentAsset), isFalse);
    });

    test('returns false when size equals threshold exactly', () async {
      final f = await _makeFile(directUploadThresholdBytes, name: 'exact.pdf');
      addTearDown(() => f.parent.delete(recursive: true));
      expect(shouldUseDirect(f, UploadKind.submissionFile), isFalse);
    });

    test('returns true when size exceeds threshold', () async {
      final f =
          await _makeFile(directUploadThresholdBytes + 1, name: 'large.pdf');
      addTearDown(() => f.parent.delete(recursive: true));
      expect(shouldUseDirect(f, UploadKind.submissionFile), isTrue);
    });
  });

  // ── directUpload — integration ─────────────────────────────────────────────

  group('directUpload', () {
    late TestSecureTokenStorage tokenStorage;

    setUp(() {
      tokenStorage = TestSecureTokenStorage();
    });

    // Helper: build an ApiClient pointing at the test server.
    ApiClient makeClient(String baseUrl) => ApiClient(
          tokenStorage: tokenStorage,
          baseUrl: baseUrl,
        )..setAccessToken('test-token');

    test('happy path: init → PUT (no auth header) → complete → poll available',
        () async {
      const uploadId = 'uid-happy-1';
      // We'll start a put server later; capture its URL after binding.
      // Strategy: start the put server first, then the API server.
      late _Server putServer;
      bool putAuthHeaderPresent = false;
      bool putCalled = false;

      // PUT server — receives the file bytes directly.
      putServer = await _startServer((req) async {
        expect(req.method, 'PUT');
        // Security invariant: no Authorization header on PUT to MinIO.
        putAuthHeaderPresent = req.headers.value('authorization') != null;
        putCalled = true;
        await req.drain<void>();
        await _json(req.response, 200, {});
      });

      int statusCallCount = 0;

      final apiServer = await _startServer((req) async {
        if (req.uri.path == '/api/v1/uploads/init') {
          await _json(req.response, 200, {
            'data': {
              'upload_id': uploadId,
              'upload_url': '${putServer.baseUrl}/bucket/object',
              'object_key': 'schools/s1/content/obj',
              'expires_at': DateTime.now()
                  .add(const Duration(hours: 1))
                  .toUtc()
                  .toIso8601String(),
              'max_size_bytes': 524288000,
            },
          });
        } else if (req.uri.path == '/api/v1/uploads/complete') {
          final body = await _readBody(req);
          expect(body['upload_id'], uploadId);
          await _json(req.response, 200, {'data': {}});
        } else if (req.uri.path == '/api/v1/uploads/$uploadId/status') {
          statusCallCount++;
          await _json(req.response, 200, {
            'data': {
              'upload_id': uploadId,
              'state': 'available',
              'target_id': 'asset-abc',
              'target_kind': 'content_asset',
              'error_message': null,
            },
          });
        } else {
          req.response.statusCode = 404;
          await req.response.close();
        }
      });

      final file = await _makeFile(512, name: 'doc.pdf');
      addTearDown(() async {
        await file.parent.delete(recursive: true);
        await apiServer.close();
        await putServer.close();
      });

      final states = <UploadState>[];
      final result = await directUpload(
        api: makeClient(apiServer.baseUrl),
        kind: UploadKind.contentAsset,
        scope: const UploadScope(schoolId: 'school-1'),
        file: file,
        onStateChange: states.add,
      );

      expect(result.state, UploadState.available);
      expect(result.targetId, 'asset-abc');
      expect(putCalled, isTrue);
      expect(
        putAuthHeaderPresent,
        isFalse,
        reason: 'PUT to MinIO must carry no Authorization header',
      );
      expect(statusCallCount, greaterThanOrEqualTo(1));
      expect(
        states,
        containsAll([
          UploadState.preparing,
          UploadState.uploading,
          UploadState.processing,
          UploadState.available,
        ]),
      );
    });

    test('quarantined file: status=quarantined → throws UploadQuarantinedError',
        () async {
      const uploadId = 'uid-quarantine-1';
      late _Server putServer;
      putServer = await _startServer((req) async {
        await req.drain<void>();
        await _json(req.response, 200, {});
      });

      final apiServer = await _startServer((req) async {
        if (req.uri.path == '/api/v1/uploads/init') {
          await _json(req.response, 200, {
            'data': {
              'upload_id': uploadId,
              'upload_url': '${putServer.baseUrl}/bucket/object',
              'object_key': 'schools/s1/content/obj',
              'expires_at': DateTime.now()
                  .add(const Duration(hours: 1))
                  .toUtc()
                  .toIso8601String(),
              'max_size_bytes': 524288000,
            },
          });
        } else if (req.uri.path == '/api/v1/uploads/complete') {
          await _json(req.response, 200, {'data': {}});
        } else if (req.uri.path == '/api/v1/uploads/$uploadId/status') {
          await _json(req.response, 200, {
            'data': {
              'upload_id': uploadId,
              'state': 'quarantined',
              'target_id': null,
              'target_kind': null,
              'error_message': 'virus detected',
            },
          });
        } else {
          req.response.statusCode = 404;
          await req.response.close();
        }
      });

      final file = await _makeFile(512, name: 'virus.pdf');
      addTearDown(() async {
        await file.parent.delete(recursive: true);
        await apiServer.close();
        await putServer.close();
      });

      expect(
        () => directUpload(
          api: makeClient(apiServer.baseUrl),
          kind: UploadKind.contentAsset,
          scope: const UploadScope(schoolId: 'school-1'),
          file: file,
        ),
        throwsA(isA<UploadQuarantinedError>()),
      );
    });

    test('init failure (422): throws ApiClientError without calling PUT',
        () async {
      bool putCalled = false;
      late _Server putServer;
      putServer = await _startServer((req) async {
        putCalled = true;
        await req.drain<void>();
        await _json(req.response, 200, {});
      });

      final apiServer = await _startServer((req) async {
        if (req.uri.path == '/api/v1/uploads/init') {
          await _json(req.response, 422, {
            'error': {
              'code': 'ERR-VAL-422',
              'message': 'Unsupported mime type',
              'category': 'validation',
              'retryable': false,
            },
          });
        } else {
          req.response.statusCode = 404;
          await req.response.close();
        }
      });

      final file = await _makeFile(512, name: 'bad.exe');
      addTearDown(() async {
        await file.parent.delete(recursive: true);
        await apiServer.close();
        await putServer.close();
      });

      await expectLater(
        directUpload(
          api: makeClient(apiServer.baseUrl),
          kind: UploadKind.submissionFile,
          scope: const UploadScope(schoolId: 'school-1'),
          file: file,
        ),
        throwsA(isA<ApiClientError>()),
      );

      expect(
        putCalled,
        isFalse,
        reason: 'PUT must not be attempted after init failure',
      );
    });

    test('expired presigned URL: throws UploadExpiredError before PUT',
        () async {
      bool putCalled = false;
      late _Server putServer;
      putServer = await _startServer((req) async {
        putCalled = true;
        await req.drain<void>();
        await _json(req.response, 200, {});
      });

      final apiServer = await _startServer((req) async {
        if (req.uri.path == '/api/v1/uploads/init') {
          await _json(req.response, 200, {
            'data': {
              'upload_id': 'uid-expired-1',
              // expires_at in the past
              'upload_url': '${putServer.baseUrl}/bucket/obj',
              'object_key': 'schools/s1/obj',
              'expires_at': DateTime.now()
                  .subtract(const Duration(minutes: 5))
                  .toUtc()
                  .toIso8601String(),
              'max_size_bytes': 524288000,
            },
          });
        } else {
          req.response.statusCode = 404;
          await req.response.close();
        }
      });

      final file = await _makeFile(512, name: 'doc.pdf');
      addTearDown(() async {
        await file.parent.delete(recursive: true);
        await apiServer.close();
        await putServer.close();
      });

      await expectLater(
        directUpload(
          api: makeClient(apiServer.baseUrl),
          kind: UploadKind.contentAsset,
          scope: const UploadScope(schoolId: 'school-1'),
          file: file,
        ),
        throwsA(isA<UploadExpiredError>()),
      );

      expect(
        putCalled,
        isFalse,
        reason: 'PUT must not be attempted when URL is already expired',
      );
    });

    test('PUT non-2xx: throws UploadPutError', () async {
      late _Server putServer;
      putServer = await _startServer((req) async {
        await req.drain<void>();
        req.response.statusCode = 403;
        await req.response.close();
      });

      final apiServer = await _startServer((req) async {
        if (req.uri.path == '/api/v1/uploads/init') {
          await _json(req.response, 200, {
            'data': {
              'upload_id': 'uid-put-fail-1',
              'upload_url': '${putServer.baseUrl}/bucket/obj',
              'object_key': 'schools/s1/obj',
              'expires_at': DateTime.now()
                  .add(const Duration(hours: 1))
                  .toUtc()
                  .toIso8601String(),
              'max_size_bytes': 524288000,
            },
          });
        } else {
          req.response.statusCode = 404;
          await req.response.close();
        }
      });

      final file = await _makeFile(512, name: 'doc.pdf');
      addTearDown(() async {
        await file.parent.delete(recursive: true);
        await apiServer.close();
        await putServer.close();
      });

      await expectLater(
        directUpload(
          api: makeClient(apiServer.baseUrl),
          kind: UploadKind.contentAsset,
          scope: const UploadScope(schoolId: 'school-1'),
          file: file,
        ),
        throwsA(isA<UploadPutError>()),
      );
    });
  });
}
