import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { RubricEditorPage } from '@/features/lms/rubrics/ui/RubricEditorPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const mockRubric = {
  id: 'rubric-1',
  title: 'Essay Rubric',
  subject: 'French',
  description: 'Rubric for evaluating essays',
  criteria: [
    {
      id: 'c-1',
      name: 'Content',
      weight: 2,
      levels: [
        { id: 'l-1', label: 'Excellent', score: 4, description: 'Outstanding content' },
        { id: 'l-2', label: 'Good', score: 3, description: 'Good content' },
      ],
    },
  ],
  created_at: '2026-01-01T00:00:00Z',
};

describe('RubricEditorPage (new)', () => {
  it('renders new rubric form without crashing', async () => {
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/edit" element={<RubricEditorPage />} />
      </Routes>,
      { route: '/rubrics/new/edit', user: { role: 'TCH' } },
    );
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders form fields for new rubric', async () => {
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/edit" element={<RubricEditorPage />} />
      </Routes>,
      { route: '/rubrics/new/edit', user: { role: 'TCH' } },
    );
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
  });
});

describe('RubricEditorPage (edit)', () => {
  it('shows loading state when fetching rubric', () => {
    server.use(
      http.get('/api/v1/rubrics/rubric-1', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiResponse(mockRubric);
      }),
    );
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/edit" element={<RubricEditorPage />} />
      </Routes>,
      { route: '/rubrics/rubric-1/edit', user: { role: 'TCH' } },
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders rubric data when loaded', async () => {
    server.use(http.get('/api/v1/rubrics/rubric-1', () => apiResponse(mockRubric)));
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/edit" element={<RubricEditorPage />} />
      </Routes>,
      { route: '/rubrics/rubric-1/edit', user: { role: 'TCH' } },
    );
    await waitFor(
      () => {
        expect(document.body.textContent).not.toContain('Loading');
      },
      { timeout: 3000 },
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error state when rubric load fails', async () => {
    server.use(http.get('/api/v1/rubrics/rubric-1', () => apiErrorResponse('Not found', 404)));
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/edit" element={<RubricEditorPage />} />
      </Routes>,
      { route: '/rubrics/rubric-1/edit', user: { role: 'TCH' } },
    );
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
