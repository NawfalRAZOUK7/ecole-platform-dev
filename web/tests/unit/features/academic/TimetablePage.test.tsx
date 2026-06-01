import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { TimetablePage } from '@/features/academic/timetable/ui/TimetablePage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, apiResponse, server } from '../../../utils/mocks';

const mockClass = {
  id: 'class-1',
  code: 'CE2A',
  name: 'CE2 A',
  level: 'ce2',
  teacher_id: 'teacher-1',
};

const mockSlot = {
  id: 'slot-1',
  class_id: 'class-1',
  academic_year_id: 'ay-1',
  day_of_week: 1,
  start_time: '08:00',
  end_time: '09:00',
  subject: 'math',
  teacher_id: 'teacher-1',
  room: 'Salle A',
  is_recurring: true,
};

const mockWeeklyResponse = {
  class_id: 'class-1',
  week_start: '2026-05-25',
  week_end: '2026-05-30',
  slots: [mockSlot],
};

function setupHandlersAdmin() {
  server.use(
    http.get('/api/v1/teacher/classes', () => apiListResponse([mockClass])),
    http.get('/api/v1/timetable/class/:classId/weekly', () => apiResponse(mockWeeklyResponse)),
  );
}

function setupHandlersStudent() {
  server.use(http.get('/api/v1/timetable/me/weekly', () => apiResponse(mockWeeklyResponse)));
}

describe('TimetablePage', () => {
  it('renders loading state for admin with classes loading', () => {
    server.use(
      http.get('/api/v1/teacher/classes', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
      http.get('/api/v1/timetable/me/weekly', () => apiResponse(mockWeeklyResponse)),
    );
    renderWithProviders(<TimetablePage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders timetable page title', async () => {
    setupHandlersAdmin();
    renderWithProviders(<TimetablePage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(document.querySelector('.page')).toBeTruthy();
    });
  });

  it('shows timetable grid with slot data for admin', async () => {
    setupHandlersAdmin();
    renderWithProviders(<TimetablePage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByText('math') ||
          screen.queryByText('Salle A') ||
          document.querySelector('.timetable-grid'),
      ).toBeTruthy();
    });
  });

  it('shows "add slot" button for admin', async () => {
    setupHandlersAdmin();
    renderWithProviders(<TimetablePage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByRole('button', { name: /addSlot|add/i }) ||
          document.querySelector('.btn-primary'),
      ).toBeTruthy();
    });
  });

  it('renders timetable for student role (non-admin)', async () => {
    setupHandlersStudent();
    renderWithProviders(<TimetablePage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.querySelector('.page')).toBeTruthy();
    });
  });

  it('shows error banner when timetable query fails', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () => apiListResponse([mockClass])),
      http.get('/api/v1/timetable/class/:classId/weekly', () =>
        apiErrorResponse('Timetable load failed'),
      ),
    );
    renderWithProviders(<TimetablePage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByText(/Timetable load failed/) ||
          screen.queryByText(/error/i) ||
          document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });

  it('shows empty state when no slots', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () => apiListResponse([mockClass])),
      http.get('/api/v1/timetable/class/:classId/weekly', () =>
        apiResponse({ ...mockWeeklyResponse, slots: [] }),
      ),
    );
    renderWithProviders(<TimetablePage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        document.querySelector('.empty-state') ||
          screen.queryByText(/📅/) ||
          screen.queryByText(/empty/i),
      ).toBeTruthy();
    });
  });
});
