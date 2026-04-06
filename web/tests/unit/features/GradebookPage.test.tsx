import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { delay, http } from 'msw';
import { describe, expect, it, vi } from 'vitest';
import { GradebookPage } from '@/features/gradebook/GradebookPage';
import { renderWithProviders } from '../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../utils/mocks';

const gradebookGrid = {
  class_id: 'class-1',
  class_name: 'Class 6A',
  columns: [
    {
      assessment_id: 'assessment-quiz',
      title: 'Quiz 1',
      weight: 0.4,
      max_score: 20 as const,
      date: '2026-04-01',
      type: 'quiz' as const,
    },
    {
      assessment_id: 'assessment-exam',
      title: 'Exam 1',
      weight: 0.6,
      max_score: 20 as const,
      date: '2026-04-04',
      type: 'exam' as const,
    },
  ],
  entries: [
    {
      student_id: 'student-1',
      student_name: 'Amine Student',
      grades: {
        'assessment-quiz': 16,
        'assessment-exam': 18,
      },
      weighted_average: 17.2,
    },
    {
      student_id: 'student-2',
      student_name: 'Salma Student',
      grades: {
        'assessment-quiz': 14,
        'assessment-exam': 15,
      },
      weighted_average: 14.6,
    },
  ],
};

const weightedSummary = {
  class_id: 'class-1',
  class_average: 15.9,
  pass_rate: 100,
  highest_average: 17.2,
  lowest_average: 14.6,
};

describe('GradebookPage', () => {
  it('loads the grid, validates grade entry, and saves valid grades', async () => {
    const user = userEvent.setup();
    const updateGrades = vi.fn();

    server.use(
      http.get('/api/v1/gradebook/class/:id', () => apiResponse(gradebookGrid)),
      http.get('/api/v1/gradebook/class/:id/weighted-summary', () =>
        apiResponse(weightedSummary)
      ),
      http.put('/api/v1/gradebook/class/:id/grades', async ({ request }) => {
        updateGrades(await request.json());
        return apiResponse({});
      })
    );

    renderWithProviders(<GradebookPage />, {
      user: { role: 'TCH' },
    });

    expect(await screen.findByText('Amine Student')).toBeInTheDocument();

    const firstGradeInput = screen.getAllByRole('spinbutton')[0];
    await user.clear(firstGradeInput);
    await user.type(firstGradeInput, '25');
    await user.click(screen.getByRole('button', { name: 'Save All' }));

    await waitFor(() => {
      expect(updateGrades).not.toHaveBeenCalled();
    });

    await user.clear(firstGradeInput);
    await user.type(firstGradeInput, '19.5');
    await user.click(screen.getByRole('button', { name: 'Save All' }));

    await waitFor(() => {
      expect(updateGrades).toHaveBeenCalledTimes(1);
    });

    expect(updateGrades).toHaveBeenCalledWith(
      expect.objectContaining({
        grades: expect.arrayContaining([
          expect.objectContaining({
            student_id: 'student-1',
            assessment_id: 'assessment-quiz',
            value: 19.5,
          }),
        ]),
      })
    );
    expect(await screen.findByText('Grades saved')).toBeInTheDocument();
  });

  it('shows an error banner when the gradebook query fails', async () => {
    server.use(
      http.get('/api/v1/gradebook/class/:id', () => apiErrorResponse('Unable to load gradebook'))
    );

    renderWithProviders(<GradebookPage />, {
      user: { role: 'TCH' },
    });

    expect(await screen.findByText('Unable to load gradebook')).toBeInTheDocument();
  });

  it('shows loading skeletons while the gradebook is loading', async () => {
    server.use(
      http.get('/api/v1/gradebook/class/:id', async () => {
        await delay(200);
        return apiResponse(gradebookGrid);
      }),
      http.get('/api/v1/gradebook/class/:id/weighted-summary', async () => {
        await delay(200);
        return apiResponse(weightedSummary);
      })
    );

    const { container } = renderWithProviders(<GradebookPage />, {
      user: { role: 'TCH' },
    });

    await waitFor(() => {
      expect(container.querySelectorAll('.skeleton--table-row').length).toBeGreaterThan(0);
    });
  });
});
