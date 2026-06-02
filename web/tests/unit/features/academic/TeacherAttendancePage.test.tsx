import type { ComponentType } from 'react';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { renderWithProviders } from '../../../utils/render';

const mocks = vi.hoisted(() => ({
  createAttendanceSession: vi.fn(),
  classesQuery: {
    data: [
      { id: 'class-1', code: '6A', name: 'Class 6A' },
      { id: 'class-2', code: '6B', name: 'Class 6B' },
    ],
    isLoading: false,
    error: null as Error | null,
    refetch: vi.fn(),
  },
  periodsQuery: {
    data: [{ id: 'period-1', label: 'Term 1', date_start: '2026-09-01', date_end: '2026-12-20' }],
    isLoading: false,
    error: null as Error | null,
    refetch: vi.fn(),
  },
  studentsQuery: {
    data: [
      { id: 'student-1', full_name: 'Alice Example', email: 'alice@test.com' },
      { id: 'student-2', full_name: 'Bob Example', email: 'bob@test.com' },
    ],
    isLoading: false,
    error: null as Error | null,
    refetch: vi.fn(),
  },
  emptyStudentsQuery: {
    data: [],
    isLoading: false,
    error: null as Error | null,
    refetch: vi.fn(),
  },
}));

vi.mock('@/features/lms/teacher/model/useTeacher', () => ({
  useTeacherClasses: () => mocks.classesQuery,
  useTeacherPeriods: () => mocks.periodsQuery,
  useTeacherClassStudents: (classId: string | null | undefined) =>
    classId ? mocks.studentsQuery : mocks.emptyStudentsQuery,
  useCreateAttendanceSession: () => ({
    mutateAsync: mocks.createAttendanceSession,
    isPending: false,
    error: null,
  }),
}));

async function renderPage() {
  const { AttendancePage } = (await import('@/features/academic/teacher/ui/AttendancePage')) as {
    AttendancePage: ComponentType;
  };

  return renderWithProviders(<AttendancePage />, { user: { role: 'TCH' } });
}

describe('TeacherAttendancePage', () => {
  beforeEach(() => {
    mocks.createAttendanceSession.mockReset();
    mocks.createAttendanceSession.mockResolvedValue(undefined);
    mocks.classesQuery.isLoading = false;
    mocks.classesQuery.error = null;
    mocks.periodsQuery.isLoading = false;
    mocks.periodsQuery.error = null;
    mocks.studentsQuery.isLoading = false;
    mocks.studentsQuery.error = null;
  });

  it('renders the attendance form after loading classes and periods', async () => {
    await renderPage();

    expect(await screen.findByRole('heading', { name: 'Take Attendance' })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Select a class' })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Select period' })).toHaveValue('period-1');
  });

  it('shows loading state initially', async () => {
    mocks.classesQuery.isLoading = true;

    await renderPage();

    expect(screen.getByRole('status', { name: 'Loading...' })).toBeInTheDocument();
  });

  it('shows students table after selecting a class', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.selectOptions(
      await screen.findByRole('combobox', { name: 'Select a class' }),
      'class-1',
    );

    expect(await screen.findByText('Alice Example')).toBeInTheDocument();
    expect(screen.getByText('Bob Example')).toBeInTheDocument();
  });

  it('submits attendance records with absence reasons', async () => {
    const user = userEvent.setup();
    await renderPage();

    await user.selectOptions(
      await screen.findByRole('combobox', { name: 'Select a class' }),
      'class-1',
    );
    await user.selectOptions(
      await screen.findAllByRole('combobox', { name: 'Status' }).then((items) => items[1]),
      'absent',
    );
    await user.type(screen.getByRole('textbox', { name: 'Reason' }), 'Sick');
    await user.click(screen.getByRole('button', { name: 'Save Attendance' }));

    expect(mocks.createAttendanceSession).toHaveBeenCalledWith({
      class_id: 'class-1',
      period_id: 'period-1',
      session_date: expect.any(String),
      slot: 'slot_1',
      records: [
        { student_id: 'student-1', status: 'present', absence_reason: null },
        { student_id: 'student-2', status: 'absent', absence_reason: 'Sick' },
      ],
    });
    expect(await screen.findByRole('status')).toHaveTextContent('Attendance saved');
  });

  it('shows error on API failure', async () => {
    mocks.classesQuery.error = new Error('Failed to load classes');

    await renderPage();

    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to load classes');
  });
});
