import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/core/network/api_client.dart';

import '../helpers/test_services.dart';

typedef _RequestHandler = Future<void> Function(HttpRequest request);

class _RunningServer {
  _RunningServer(this.server, this._subscription);

  final HttpServer server;
  final StreamSubscription<HttpRequest> _subscription;

  String get baseUrl => 'http://${server.address.host}:${server.port}';

  Future<void> close() async {
    await _subscription.cancel();
    await server.close(force: true);
  }
}

Future<_RunningServer> _startServer(_RequestHandler handler) async {
  final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
  final subscription = server.listen((request) async {
    try {
      await handler(request);
    } catch (error) {
      request.response.statusCode = HttpStatus.internalServerError;
      request.response.write(error.toString());
      await request.response.close();
    }
  });
  return _RunningServer(server, subscription);
}

Future<void> _writeJson(
  HttpResponse response,
  int statusCode,
  Object body,
) async {
  response.statusCode = statusCode;
  response.headers.contentType = ContentType.json;
  response.write(jsonEncode(body));
  await response.close();
}

Future<Map<String, dynamic>> _readJsonBody(HttpRequest request) async {
  final body = await utf8.decoder.bind(request).join();
  if (body.isEmpty) {
    return <String, dynamic>{};
  }
  return jsonDecode(body) as Map<String, dynamic>;
}

void main() {
  group('ApiClient', () {
    late TestSecureTokenStorage tokenStorage;

    setUp(() {
      tokenStorage = TestSecureTokenStorage();
    });

    test('adds auth and locale headers and unwraps response data', () async {
      late _RunningServer server;
      server = await _startServer((request) async {
        expect(request.uri.path, '/api/v1/profile');
        expect(request.headers.value('authorization'), 'Bearer access-123');
        expect(request.headers.value('accept-language'), 'ar');
        expect(request.headers.value('x-client-version'), isNotEmpty);
        expect(request.headers.value('x-client-platform'), 'android');
        await _writeJson(
          request.response,
          HttpStatus.ok,
          {
            'data': {'ok': true},
          },
        );
      });

      final client = ApiClient(
        tokenStorage: tokenStorage,
        baseUrl: server.baseUrl,
      )
        ..setLocale('ar')
        ..setAccessToken('access-123');

      final response = await client.get('/profile');

      expect(response.data, {'ok': true});
      await server.close();
    });

    test('retries structured retryable errors and returns the later success',
        () async {
      var requestCount = 0;
      late _RunningServer server;
      server = await _startServer((request) async {
        requestCount += 1;
        if (requestCount == 1) {
          await _writeJson(
            request.response,
            HttpStatus.serviceUnavailable,
            {
              'error': {
                'code': 'ERR-TEMP-001',
                'message': 'Try again',
                'category': 'system',
                'retryable': true,
              },
            },
          );
          return;
        }

        await _writeJson(
          request.response,
          HttpStatus.ok,
          {
            'data': {'attempt': requestCount},
          },
        );
      });

      final client = ApiClient(
        tokenStorage: tokenStorage,
        baseUrl: server.baseUrl,
      );

      final response = await client.get('/retry');

      expect(response.data['attempt'], 2);
      expect(requestCount, 2);
      await server.close();
    });

    test('refreshes the access token on 401 and saves the new refresh token',
        () async {
      await tokenStorage.saveRefreshToken('refresh-1');

      var meCalls = 0;
      late _RunningServer server;
      server = await _startServer((request) async {
        if (request.uri.path == '/api/v1/auth/refresh') {
          final body = await _readJsonBody(request);
          expect(body['refresh_token'], 'refresh-1');
          await _writeJson(
            request.response,
            HttpStatus.ok,
            {
              'data': {
                'access_token': 'fresh-access',
                'refresh_token': 'refresh-2',
              },
            },
          );
          return;
        }

        if (request.uri.path == '/api/v1/auth/me') {
          meCalls += 1;
          final authHeader = request.headers.value('authorization');
          if (authHeader == 'Bearer expired-access') {
            await _writeJson(
              request.response,
              HttpStatus.unauthorized,
              {
                'error': {
                  'code': 'ERR-AUTH-401',
                  'message': 'Expired token',
                  'category': 'auth',
                  'retryable': false,
                },
              },
            );
            return;
          }

          expect(authHeader, 'Bearer fresh-access');
          await _writeJson(
            request.response,
            HttpStatus.ok,
            {
              'data': {'id': 'user-1'},
            },
          );
          return;
        }

        fail('Unexpected route ${request.uri.path}');
      });

      final client = ApiClient(
        tokenStorage: tokenStorage,
        baseUrl: server.baseUrl,
      )..setAccessToken('expired-access');

      final response = await client.get('/auth/me');

      expect(response.data['id'], 'user-1');
      expect(client.accessToken, 'fresh-access');
      expect(await tokenStorage.getRefreshToken(), 'refresh-2');
      expect(meCalls, 2);
      await server.close();
    });

    test('fetchSignedUrl calls metadata variant and parses raw JSON', () async {
      late _RunningServer server;
      server = await _startServer((request) async {
        expect(
          request.uri.path,
          '/api/v1/content-items/content-1/assets/asset-1',
        );
        expect(request.uri.queryParameters['foo'], 'bar');
        expect(request.uri.queryParameters['as'], 'metadata');
        expect(request.headers.value('authorization'), 'Bearer access-123');
        await _writeJson(
          request.response,
          HttpStatus.ok,
          {
            'download_url': 'https://minio.test/bucket/object?X-Amz=1',
            'expires_at': '2026-05-05T12:10:00Z',
            'mime_type': 'video/mp4',
            'size': 1234,
            'filename': 'lesson.mp4',
            'etag': 'abc123',
          },
        );
      });

      final client = ApiClient(
        tokenStorage: tokenStorage,
        baseUrl: server.baseUrl,
      )..setAccessToken('access-123');

      final metadata = await client.fetchSignedUrl(
        '/content-items/content-1/assets/asset-1?foo=bar',
      );

      expect(metadata.downloadUrl, startsWith('https://minio.test/'));
      expect(metadata.expiresAt, DateTime.utc(2026, 5, 5, 12, 10));
      expect(metadata.mimeType, 'video/mp4');
      expect(metadata.size, 1234);
      expect(metadata.filename, 'lesson.mp4');
      expect(metadata.etag, 'abc123');
      await server.close();
    });

    test('fetchSignedUrl normalizes absolute backend URLs and refreshes auth',
        () async {
      await tokenStorage.saveRefreshToken('refresh-1');
      var metadataCalls = 0;
      late _RunningServer server;
      server = await _startServer((request) async {
        if (request.uri.path == '/api/v1/auth/refresh') {
          await _writeJson(
            request.response,
            HttpStatus.ok,
            {
              'data': {
                'access_token': 'fresh-access',
              },
            },
          );
          return;
        }

        expect(request.uri.path, '/api/v1/documents/doc-1/download');
        expect(request.uri.queryParameters['as'], 'metadata');
        metadataCalls += 1;
        if (request.headers.value('authorization') == 'Bearer expired') {
          await _writeJson(
            request.response,
            HttpStatus.unauthorized,
            {
              'error': {
                'code': 'ERR-AUTH-401',
                'message': 'Expired token',
                'category': 'auth',
                'retryable': false,
              },
            },
          );
          return;
        }

        expect(request.headers.value('authorization'), 'Bearer fresh-access');
        await _writeJson(
          request.response,
          HttpStatus.ok,
          {
            'download_url': 'https://minio.test/doc.pdf?X-Amz=1',
            'expires_at': '2026-05-05T12:10:00Z',
            'mime_type': 'application/pdf',
            'size': 42,
            'filename': 'doc.pdf',
            'etag': null,
          },
        );
      });

      final client = ApiClient(
        tokenStorage: tokenStorage,
        baseUrl: server.baseUrl,
      )..setAccessToken('expired');

      final metadata = await client.fetchSignedUrl(
        'https://api.example.test/api/v1/documents/doc-1/download',
      );

      expect(metadata.filename, 'doc.pdf');
      expect(client.accessToken, 'fresh-access');
      expect(metadataCalls, 2);
      await server.close();
    });

    test('throws ApiClientError for structured API errors', () async {
      late _RunningServer server;
      server = await _startServer((request) async {
        await _writeJson(
          request.response,
          HttpStatus.badRequest,
          {
            'error': {
              'code': 'ERR-VAL-001',
              'message': 'Invalid field',
              'category': 'validation',
              'retryable': false,
              'correlation_id': 'corr-1',
            },
          },
        );
      });

      final client = ApiClient(
        tokenStorage: tokenStorage,
        baseUrl: server.baseUrl,
      );

      await expectLater(
        client.get('/broken'),
        throwsA(
          isA<ApiClientError>()
              .having((e) => e.statusCode, 'statusCode', HttpStatus.badRequest)
              .having((e) => e.apiError.code, 'code', 'ERR-VAL-001')
              .having((e) => e.apiError.category, 'category', 'validation')
              .having(
                (e) => e.apiError.correlationId,
                'correlationId',
                'corr-1',
              ),
        ),
      );

      await server.close();
    });

    test('wraps unstructured server failures as network-style ApiClientError',
        () async {
      late _RunningServer server;
      server = await _startServer((request) async {
        request.response.statusCode = HttpStatus.badGateway;
        request.response.write('Bad gateway');
        await request.response.close();
      });

      final client = ApiClient(
        tokenStorage: tokenStorage,
        baseUrl: server.baseUrl,
      );

      await expectLater(
        client.get('/upstream'),
        throwsA(
          isA<ApiClientError>()
              .having((e) => e.statusCode, 'statusCode', HttpStatus.badGateway)
              .having((e) => e.apiError.code, 'code', 'ERR-NET-000')
              .having((e) => e.apiError.category, 'category', 'network')
              .having((e) => e.apiError.retryable, 'retryable', true),
        ),
      );

      await server.close();
    });
  });
}
