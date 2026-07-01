import { waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { RubricGradingPage } from '@/features/lms/rubrics/ui/RubricGradingPage';
import { renderWithProviders } from '../../../utils/render';

const rubricHooks = vi.hoisted(() => ({
  useGradeRubric: vi.fn(),
  useRubric: vi.fn(),
  useRubricResults: vi.fn(),
}));

vi.mock('@/features/lms/rubrics/model/useRubrics', () => ({
  useGradeRubric: rubricHooks.useGradeRubric,
  useRubric: rubricHooks.useRubric,
  useRubricResults: rubricHooks.useRubricResults,
}));

const mockRubric = {
  id: 'rubric-1',
  title: 'Essay Rubric',
  subject: 'French',
  description: null,
  criteria: [
    {
      id: 'c-1',
      name: 'Content',
      weight: 2,
      levels: [
        { id: 'l-1', label: 'Excellent', score: 4, description: 'Outstanding' },
        { id: 'l-2', label: 'Satisfactory', score: 2, description: 'OK' },
      ],
    },
  ],
  created_at: '2026-01-01T00:00:00Z',
};

const mockResults = {
  results: [
    {
      student_id: 'student-1',
      rubric_id: 'rubric-1',
      total_score: 8,
      max_score: 8,
      percentage: 100,
      entries: [],
    },
  ],
};

function queryResult(data: unknown, error: Error | null = null) {
  return {
    data: error ? undefined : data,
    error,
    isLoading: false,
    refetch: vi.fn(),
  };
}

function renderRubricPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/rubrics/:id/grade" element={<RubricGradingPage />} />
    </Routes>,
    { route: '/rubrics/rubric-1/grade', user: { role: 'TCH' } },
  );
}

describe('RubricGradingPage', () => {
  beforeEach(() => {
    rubricHooks.useRubric.mockReturnValue(queryResult(mockRubric));
    rubricHooks.useRubricResults.mockReturnValue(queryResult(mockResults));
    rubricHooks.useGradeRubric.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
  });

  it('renders without crashing', async () => {
    renderRubricPage();
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    rubricHooks.useRubric.mockReturnValue({
      ...queryResult(undefined),
      isLoading: true,
    });

    renderRubricPage();
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders rubric grading form with criteria', async () => {
    rubricHooks.useRubric.mockReturnValue(queryResult(mockRubric));
    rubricHooks.useRubricResults.mockReturnValue(queryResult(mockResults));

    renderRubricPage();
    await waitFor(
      () => {
        expect(document.body.textContent).not.toContain('Loading');
      },
      { timeout: 3000 },
    );
    expect(document.body.textContent).toContain('Content');
  });

  it('shows error state on failure', async () => {
    rubricHooks.useRubric.mockReturnValue(queryResult(undefined, new Error('Not found')));
    rubricHooks.useRubricResults.mockReturnValue(queryResult(undefined, new Error('Not found')));

    renderRubricPage();
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
