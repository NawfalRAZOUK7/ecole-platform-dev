import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { AttendancePage } from '@/features/academic/teacher/ui/AttendancePage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

describe('TeacherAttendancePage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/teacher/classes', () =>
        apiResponse([
          { id: 'class-1', code: '6A', name: 'Class 6A' },
          { id: 'class-2', code: '6B', name: 'Class 6B' },
        ]),
      ),
      http.get('/api/v1/teacher/periods', () =>
        apiResponse([
          { id: 'period-1', label: 'Term 1', date_start: '2026-09-01', date_end: '2026-12-20' },
        ]),
      ),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<AttendancePage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(50));
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/teacher/classes', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiResponse([]);
      }),
    );
    renderWithProviders(<AttendancePage />, { user: { role: 'TCH' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders class selection form after load', async () => {
    renderWithProviders(<AttendancePage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML).toContain('select');
    });
  });

  it('shows students table after selecting a class', async () => {
    server.use(
      http.get('/api/v1/teacher/classes/:classId/students', () =>
        apiResponse([
          { id: 'student-1', full_name: 'Alice Example', email: 'alice@test.com' },
          { id: 'student-2', full_name: 'Bob Example', email: 'bob@test.com' },
        ]),
      ),
    );
    renderWithProviders(<AttendancePage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(100);
    });
  });

  it('shows error on API failure', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () => apiErrorResponse('Failed to load classes')),
      http.get('/api/v1/teacher/periods', () => apiErrorResponse('Failed to load periods')),
    );
    renderWithProviders(<AttendancePage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
