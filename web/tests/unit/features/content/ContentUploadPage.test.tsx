import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { CmsContentUploadPage } from '@/features/content/cms/ui/ContentUploadPage';
import { renderWithProviders } from '../../../utils/render';
import { server } from '../../../utils/mocks';

describe('CmsContentUploadPage', () => {
  it('renders the upload form', () => {
    server.use(
      http.get(
        '/api/v1/levels',
        () => new Response(JSON.stringify({ data: [], meta: { timestamp: '', version: '' } })),
      ),
    );
    renderWithProviders(<CmsContentUploadPage />, { user: { role: 'ADM' } });
    // The upload form should render immediately (no initial loading)
    expect(
      document.querySelector('form') ||
        screen.queryByRole('button') ||
        document.querySelector('input'),
    ).toBeTruthy();
  });

  it('renders content type selector', async () => {
    renderWithProviders(<CmsContentUploadPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(document.querySelector('select') || screen.queryByRole('combobox')).toBeTruthy();
    });
  });

  it('renders title input', async () => {
    renderWithProviders(<CmsContentUploadPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        document.querySelector('input[name="title"]') || screen.queryByPlaceholderText(/title/i),
      ).toBeTruthy();
    });
  });
});
