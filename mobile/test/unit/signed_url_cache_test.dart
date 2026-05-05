import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/services/signed_url_cache.dart';

import '../helpers/test_mocks.dart';

DownloadMetadata _metadata({
  required String url,
  required DateTime expiresAt,
}) {
  return DownloadMetadata(
    downloadUrl: url,
    expiresAt: expiresAt,
    mimeType: 'video/mp4',
    size: 10,
    filename: 'lesson.mp4',
    etag: null,
  );
}

void main() {
  group('SignedUrlCache', () {
    late MockApiClient api;
    late DateTime now;
    late SignedUrlCache cache;

    setUp(() {
      api = MockApiClient();
      now = DateTime.utc(2026, 5, 5, 12);
      cache = SignedUrlCache(api: api, now: () => now);
    });

    test('caches signed URLs until 80 percent of the TTL', () async {
      var calls = 0;
      when(() => api.fetchSignedUrl('/content/asset')).thenAnswer((_) async {
        calls += 1;
        return _metadata(
          url: 'https://minio.test/url-$calls',
          expiresAt: now.add(const Duration(minutes: 10)),
        );
      });

      expect(await cache.getUrl('/content/asset'), 'https://minio.test/url-1');
      now = now.add(const Duration(minutes: 7, seconds: 59));
      expect(await cache.getUrl('/content/asset'), 'https://minio.test/url-1');
      now = now.add(const Duration(seconds: 2));
      expect(await cache.getUrl('/content/asset'), 'https://minio.test/url-2');
      expect(calls, 2);
    });

    test('force refresh and invalidate bypass cached metadata', () async {
      var calls = 0;
      when(() => api.fetchSignedUrl('/documents/doc-1')).thenAnswer((_) async {
        calls += 1;
        return _metadata(
          url: 'https://minio.test/doc-$calls',
          expiresAt: now.add(const Duration(minutes: 10)),
        );
      });

      expect(
        await cache.getUrl('/documents/doc-1'),
        'https://minio.test/doc-1',
      );
      expect(
        await cache.getUrl('/documents/doc-1', forceRefresh: true),
        'https://minio.test/doc-2',
      );
      cache.invalidate('/documents/doc-1');
      expect(
        await cache.getUrl('/documents/doc-1'),
        'https://minio.test/doc-3',
      );
      expect(calls, 3);
    });

    test('deduplicates concurrent metadata fetches', () async {
      final completer = Completer<DownloadMetadata>();
      when(() => api.fetchSignedUrl('/content/video')).thenAnswer(
        (_) => completer.future,
      );

      final first = cache.getUrl('/content/video');
      final second = cache.getUrl('/content/video');

      completer.complete(
        _metadata(
          url: 'https://minio.test/video',
          expiresAt: now.add(const Duration(minutes: 10)),
        ),
      );

      expect(await first, 'https://minio.test/video');
      expect(await second, 'https://minio.test/video');
      verify(() => api.fetchSignedUrl('/content/video')).called(1);
    });
  });
}
