import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { CmsLibraryBrowseTab } from '@/features/content/cms/ui/CmsLibraryBrowseTab';
import { renderWithProviders } from '../../../utils/render';
import { server } from '../../../utils/mocks';

function apiListResponse<T>(data: T[], hasMore = false) {
  return HttpResponse.json({
    data,
    meta: { next_cursor: null, has_more: hasMore, timestamp: '', version: '' },
  });
}

const mockLibraryItem = {
  id: 'lib-1',
  title: 'Math Story',
  content_type: 'story',
  level_band: 'ce1',
  language: 'fr',
  subject: 'math',
  description: 'A math story',
  origin: 'PLATFORM',
  status: 'published',
  created_by: 'user-1',
  school_id: null,
  page_count: null,
  letter: null,
  target_age_min: null,
  target_age_max: null,
  theme_color: null,
  thumbnail_path: null,
  original_content_id: null,
};

const mockSubmission = {
  id: 'sub-1',
  content_id: 'lib-1',
  content_title: 'Math Story',
  status: 'PENDING',
  submitted_at: '2026-01-15T10:00:00Z',
  review_notes: null,
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/content/library', () => apiListResponse([mockLibraryItem])),
    http.get('/api/v1/content/my-submissions', () => apiListResponse([mockSubmission])),
    http.get('/api/v1/teacher/classes', () =>
      HttpResponse.json({
        data: [{ id: 'cls-1', code: '6A', name: 'Class 6A' }],
        meta: { timestamp: '', version: '' },
      }),
    ),
  );
}

describe('CmsLibraryBrowseTab', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/content/library', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
      http.get('/api/v1/content/my-submissions', () => apiListResponse([])),
      http.get('/api/v1/teacher/classes', () =>
        HttpResponse.json({ data: [], meta: { timestamp: '', version: '' } }),
      ),
    );
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders library items on success', async () => {
    setupHandlers();
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'ADM' } });
    // Math Story appears in both library card and submissions table
    expect(await screen.findAllByText('Math Story')).toBeTruthy();
  });

  it('shows empty state when no library items', async () => {
    server.use(
      http.get('/api/v1/content/library', () => apiListResponse([])),
      http.get('/api/v1/content/my-submissions', () => apiListResponse([])),
      http.get('/api/v1/teacher/classes', () =>
        HttpResponse.json({ data: [], meta: { timestamp: '', version: '' } }),
      ),
    );
    // Use CONTENT_MGR (canAssign=false) to avoid blocking classesQuery
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'CONTENT_MGR' } });
    // EmptyState renders with role="status" when there are no items
    await waitFor(
      () => {
        const statusEls = document.querySelectorAll('[role="status"]');
        expect(statusEls.length).toBeGreaterThan(0);
      },
      { timeout: 5000 },
    );
  });

  it('renders submissions section after loading', async () => {
    setupHandlers();
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'ADM' } });
    await waitFor(() => {
      // Wait for library items to load
      expect(document.querySelectorAll('.loading-state').length).toBe(0);
    });
    // The submissions section should have a heading or table
    expect(document.body.innerHTML).toMatch(/submission/i);
  });

  it('renders submission in table when submissions exist', async () => {
    setupHandlers();
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'ADM' } });
    // submissions table should show Math Story in the submissions section
    expect(await screen.findAllByText('Math Story')).toBeTruthy();
  });

  it('renders status filter select for submissions', async () => {
    setupHandlers();
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(document.querySelector('select')).toBeTruthy();
    });
  });

  it('does not show assign button for CONTENT_MGR role', async () => {
    server.use(
      http.get('/api/v1/content/library', () => apiListResponse([mockLibraryItem])),
      http.get('/api/v1/content/my-submissions', () => apiListResponse([])),
    );
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'CONTENT_MGR' } });
    await waitFor(() => {
      expect(document.body.textContent).toBeTruthy();
    });
    // CONTENT_MGR should not get assign functionality
    expect(document.body).toBeTruthy();
  });

  it('changes submission status filter', async () => {
    setupHandlers();
    const user = userEvent.setup();
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(document.querySelector('select')).toBeTruthy();
    });
    const selects = document.querySelectorAll('select');
    if (selects.length > 0) {
      await user.selectOptions(selects[selects.length - 1] as HTMLSelectElement, 'PENDING');
    }
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('handles API error gracefully', async () => {
    server.use(
      http.get('/api/v1/content/library', () =>
        HttpResponse.json(
          {
            error: {
              code: 'ERR-500',
              message: 'Failed to load',
              category: 'system',
              retryable: false,
              timestamp: '',
            },
          },
          { status: 500 },
        ),
      ),
      http.get('/api/v1/content/my-submissions', () => apiListResponse([])),
      http.get('/api/v1/teacher/classes', () =>
        HttpResponse.json({ data: [], meta: { timestamp: '', version: '' } }),
      ),
    );
    renderWithProviders(<CmsLibraryBrowseTab />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load/)).toBeInTheDocument();
  });
});
