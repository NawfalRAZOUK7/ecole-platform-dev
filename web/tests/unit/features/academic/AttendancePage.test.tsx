import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { delay, http } from 'msw';
import { describe, expect, it, vi } from 'vitest';
import { AttendancePage } from '@/features/academic/attendance/ui/AttendancePage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../../utils/mocks';

const attendanceRecords = [
  {
    id: 'attendance-1',
    student_id: 'student-1',
    student_name: 'Amine Student',
    class_id: 'class-1',
    date: '2026-04-06',
    status: 'present' as const,
    justified: false,
    marked_by: 'teacher-1',
  },
  {
    id: 'attendance-2',
    student_id: 'student-2',
    student_name: 'Salma Student',
    class_id: 'class-1',
    date: '2026-04-06',
    status: 'absent' as const,
    justified: true,
    justification: 'Medical note',
    marked_by: 'teacher-1',
  },
];

describe('AttendancePage', () => {
  it('loads student list, toggles status, and submits attendance', async () => {
    const user = userEvent.setup();
    const markAttendance = vi.fn();

    server.use(
      http.get('/api/v1/teacher/classes', () =>
        apiResponse([{ id: 'class-1', code: '6A', name: 'Class 6A' }]),
      ),
      http.get('/api/v1/attendance/class/:id', () =>
        apiResponse({
          class_id: 'class-1',
          stats: { total_students: 2, attendance_rate: 100, absent_count: 0, late_count: 0 },
          records: attendanceRecords,
        }),
      ),
      http.post('/api/v1/attendance/class/:id', async ({ request }) => {
        markAttendance(await request.json());
        return apiResponse({});
      }),
    );

    renderWithProviders(<AttendancePage />, {
      user: { role: 'TCH' },
    });

    expect(await screen.findByText('Amine Student')).toBeInTheDocument();

    await user.click(screen.getAllByRole('button', { name: 'Late' })[0]);
    await user.click(screen.getByRole('button', { name: 'Save attendance' }));

    await waitFor(() => {
      expect(markAttendance).toHaveBeenCalledTimes(1);
    });

    expect(markAttendance).toHaveBeenCalledWith(
      expect.objectContaining({
        records: expect.arrayContaining([
          expect.objectContaining({
            student_id: 'student-1',
            status: 'late',
          }),
        ]),
      }),
    );
    expect(await screen.findByText('Attendance saved')).toBeInTheDocument();
  });

  it('shows an error banner when attendance loading fails', async () => {
    server.use(
      http.get('/api/v1/attendance/class/:id', () => apiErrorResponse('Unable to load attendance')),
    );

    renderWithProviders(<AttendancePage />, {
      user: { role: 'TCH' },
    });

    expect(await screen.findByText('Unable to load attendance')).toBeInTheDocument();
  });

  it('shows loading skeletons while attendance is loading', async () => {
    server.use(
      http.get('/api/v1/attendance/class/:id', async () => {
        await delay(200);
        return apiResponse(attendanceRecords);
      }),
    );

    const { container } = renderWithProviders(<AttendancePage />, {
      user: { role: 'TCH' },
    });

    await waitFor(() => {
      expect(container.querySelectorAll('.skeleton--table-row').length).toBeGreaterThan(0);
    });
  });
});
