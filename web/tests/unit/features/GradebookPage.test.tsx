import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { delay, http } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { GradebookPage } from '@/features/gradebook/GradebookPage';
import { gradebookService } from '@/features/gradebook/gradebook.service';
import { renderWithProviders } from '../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../utils/mocks';

const backendGradebook = {
  class_id: 'class-1',
  class_name: 'Class 6A',
  categories: [
    {
      id: 'cat-quiz',
      name: 'Quiz',
      weight: 0.4,
    },
    {
      id: 'cat-exam',
      name: 'Exam',
      weight: 0.6,
    },
  ],
  assignments: [
    {
      assignment_id: 'assessment-quiz',
      title: 'Quiz 1',
      category_id: 'cat-quiz',
      total_points: 20,
      due_at: '2026-04-01',
    },
    {
      assignment_id: 'assessment-exam',
      title: 'Exam 1',
      category_id: 'cat-exam',
      total_points: 20,
      due_at: '2026-04-04',
    },
  ],
  rows: [
    {
      student_id: 'student-1',
      student_name: 'Amine Student',
      assignments: [
        {
          assignment_id: 'assessment-quiz',
          score: 16,
        },
        {
          assignment_id: 'assessment-exam',
          score: 18,
        },
      ],
      weighted_average: 17.2,
    },
    {
      student_id: 'student-2',
      student_name: 'Salma Student',
      assignments: [
        {
          assignment_id: 'assessment-quiz',
          score: 14,
        },
        {
          assignment_id: 'assessment-exam',
          score: 15,
        },
      ],
      weighted_average: 14.6,
    },
  ],
};

describe('GradebookPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads the grid, validates grade entry, and saves valid grades', async () => {
    const user = userEvent.setup();
    const updateGrades = vi.spyOn(gradebookService, 'updateGrades').mockResolvedValue({
      data: {
        updated: 4,
      },
      meta: {
        timestamp: '2026-04-08T09:00:00.000Z',
        version: 'test',
      },
    });

    server.use(
      http.get('/api/v1/gradebook/:classId/:periodId', () => apiResponse(backendGradebook)),
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
      }),
    );
    expect(await screen.findByText('Grades saved')).toBeInTheDocument();
  });

  it('shows an error banner when the gradebook query fails', async () => {
    server.use(
      http.get('/api/v1/gradebook/:classId/:periodId', () =>
        apiErrorResponse('Unable to load gradebook'),
      ),
    );

    renderWithProviders(<GradebookPage />, {
      user: { role: 'TCH' },
    });

    expect(await screen.findByText('Unable to load gradebook')).toBeInTheDocument();
  });

  it('shows loading skeletons while the gradebook is loading', async () => {
    server.use(
      http.get('/api/v1/gradebook/:classId/:periodId', async () => {
        await delay(200);
        return apiResponse(backendGradebook);
      }),
    );

    const { container } = renderWithProviders(<GradebookPage />, {
      user: { role: 'TCH' },
    });

    await waitFor(() => {
      expect(container.querySelectorAll('.skeleton--table-row').length).toBeGreaterThan(0);
    });
  });
});
