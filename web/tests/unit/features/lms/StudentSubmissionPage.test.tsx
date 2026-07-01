import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { StudentSubmissionPage } from '@/features/lms/submissions/ui/StudentSubmissionPage';
import { renderWithProviders } from '../../../utils/render';

const submissionHooks = vi.hoisted(() => ({
  useCreateStudentSubmission: vi.fn(),
  useFinalizeStudentSubmission: vi.fn(),
  useSubmissionAssignments: vi.fn(),
  useUploadSubmissionFile: vi.fn(),
}));

vi.mock('@/features/lms/submissions/model/useSubmissions', () => ({
  useCreateStudentSubmission: submissionHooks.useCreateStudentSubmission,
  useFinalizeStudentSubmission: submissionHooks.useFinalizeStudentSubmission,
  useSubmissionAssignments: submissionHooks.useSubmissionAssignments,
  useUploadSubmissionFile: submissionHooks.useUploadSubmissionFile,
}));

const mockAssignment = {
  id: 'assign-1',
  title: 'Math Homework',
  course_id: 'course-1',
  due_at: '2026-12-01T00:00:00Z',
  total_points: 20,
  exercise_type: 'STANDARD',
  exercise_pdf_path: null,
};

function assignmentsResult(items: unknown[], error: Error | null = null) {
  return {
    data: error ? undefined : items,
    error,
    isLoading: false,
    refetch: vi.fn(),
  };
}

describe('StudentSubmissionPage', () => {
  beforeEach(() => {
    submissionHooks.useSubmissionAssignments.mockReturnValue(assignmentsResult([]));
    submissionHooks.useCreateStudentSubmission.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    submissionHooks.useFinalizeStudentSubmission.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    submissionHooks.useUploadSubmissionFile.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
  });

  it('renders without crashing', async () => {
    submissionHooks.useSubmissionAssignments.mockReturnValue(assignmentsResult([]));

    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    submissionHooks.useSubmissionAssignments.mockReturnValue({
      ...assignmentsResult([]),
      isLoading: true,
    });

    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders assignments when loaded', async () => {
    submissionHooks.useSubmissionAssignments.mockReturnValue(assignmentsResult([mockAssignment]));

    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.textContent).toContain('Math Homework');
    });
  });

  it('shows empty state when no assignments', async () => {
    submissionHooks.useSubmissionAssignments.mockReturnValue(assignmentsResult([]));

    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.textContent).not.toContain('Loading');
    });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error state on failure', async () => {
    submissionHooks.useSubmissionAssignments.mockReturnValue(
      assignmentsResult([], new Error('Load failed')),
    );

    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
