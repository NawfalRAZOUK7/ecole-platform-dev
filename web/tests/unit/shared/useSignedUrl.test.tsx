import { fireEvent, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { getSignedUrlStaleTime, useSignedUrl } from '@/shared/hooks/useSignedUrl';
import type { DownloadMetadata } from '@/core/api/client';
import { renderWithProviders } from '../../utils/render';
import { server } from '../../utils/mocks';

function SignedUrlProbe({ path }: { path: string }) {
  const signedUrl = useSignedUrl(path);

  if (signedUrl.isLoading) {
    return <span>loading</span>;
  }

  return (
    <div>
      <span data-testid="signed-url">{signedUrl.url}</span>
      <button type="button" onClick={() => void signedUrl.refresh()}>
        refresh
      </button>
    </div>
  );
}

describe('useSignedUrl', () => {
  it('computes stale time at 80 percent of the signed URL TTL', () => {
    const fetchedAt = Date.parse('2026-05-05T12:00:00.000Z');
    const metadata: DownloadMetadata = {
      download_url: 'https://minio.example.test/file.pdf?X-Amz-Signature=abc',
      expires_at: '2026-05-05T12:10:00.000Z',
      mime_type: 'application/pdf',
      size: 1024,
      filename: 'file.pdf',
      etag: null,
    };

    expect(getSignedUrlStaleTime(metadata, fetchedAt)).toBe(480_000);
  });

  it('refreshes cached metadata on demand', async () => {
    let calls = 0;
    server.use(
      http.get('/api/v1/content-items/content-1/stream', () => {
        calls += 1;
        return HttpResponse.json({
          download_url: `https://minio.example.test/video.mp4?X-Amz-Signature=${calls}`,
          expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
          mime_type: 'video/mp4',
          size: 2048,
          filename: 'video.mp4',
          etag: null,
        });
      }),
    );

    renderWithProviders(<SignedUrlProbe path="/content-items/content-1/stream" />);

    expect(await screen.findByTestId('signed-url')).toHaveTextContent('X-Amz-Signature=1');

    fireEvent.click(screen.getByRole('button', { name: 'refresh' }));

    await waitFor(() => {
      expect(screen.getByTestId('signed-url')).toHaveTextContent('X-Amz-Signature=2');
    });
  });
});
