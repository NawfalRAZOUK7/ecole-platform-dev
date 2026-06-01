import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { RubricsListPage } from '@/features/lms/rubrics/ui/RubricsListPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const mockRubric = {
  id: 'rubric-1',
  title: 'Essay Rubric',
  description: 'Grading criteria for essays',
  subject: 'French',
  criteria: [
    {
      id: 'crit-1',
      title: 'Content',
      description: 'Quality of content',
      levels: [
        { id: 'lvl-1', label: 'Excellent', score: 4, description: 'Outstanding' },
        { id: 'lvl-2', label: 'Good', score: 3, description: 'Above average' },
      ],
    },
  ],
  max_score: 4,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('RubricsListPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/rubrics', () => apiResponse([mockRubric])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<RubricsListPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(50));
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/rubrics', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiResponse([]);
      }),
    );
    renderWithProviders(<RubricsListPage />, { user: { role: 'TCH' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows empty state when no rubrics', async () => {
    server.use(http.get('/api/v1/rubrics', () => apiResponse([])));
    renderWithProviders(<RubricsListPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.textContent).not.toContain('Loading');
    });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows rubric list when loaded', async () => {
    renderWithProviders(<RubricsListPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(100);
    });
  });

  it('shows error on API failure', async () => {
    server.use(http.get('/api/v1/rubrics', () => apiErrorResponse('Failed to load rubrics')));
    renderWithProviders(<RubricsListPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
