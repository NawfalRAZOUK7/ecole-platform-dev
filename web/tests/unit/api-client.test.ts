import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { server } from '../utils/mocks';

describe('API Client', () => {
  it('should be importable', async () => {
    const mod = await import('@/services/api/client');

    expect(mod.api).toBeDefined();
  });

  it('fetches raw download metadata through the backend metadata endpoint', async () => {
    const requests: string[] = [];
    server.use(
      http.get('/api/v1/content-items/content-1/stream', ({ request }) => {
        const url = new URL(request.url);
        requests.push(url.toString());

        return HttpResponse.json({
          download_url: 'https://minio.example.test/bucket/video.mp4?X-Amz-Signature=abc',
          expires_at: '2026-05-05T12:10:00.000Z',
          mime_type: 'video/mp4',
          size: 1024,
          filename: 'video.mp4',
          etag: 'etag-1',
        });
      }),
    );

    const { getDownloadUrl } = await import('@/services/api/client');
    const metadata = await getDownloadUrl(
      '/api/v1/content-items/content-1/stream?disposition=inline',
    );

    expect(metadata.download_url).toContain('https://minio.example.test/');
    expect(requests).toHaveLength(1);
    expect(new URL(requests[0]).searchParams.get('as')).toBe('metadata');
    expect(new URL(requests[0]).searchParams.get('disposition')).toBe('inline');
  });
});
