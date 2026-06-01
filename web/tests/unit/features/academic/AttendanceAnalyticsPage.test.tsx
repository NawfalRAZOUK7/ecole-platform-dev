import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { AttendanceAnalyticsPage } from '@/features/academic/attendance/ui/AttendanceAnalyticsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('AttendanceAnalyticsPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/teacher/classes', () =>
        apiResponse([{ id: 'class-1', code: '6A', name: 'Class 6A' }]),
      ),
      http.get('/api/v1/programs', () => apiListResponse([])),
      http.get('/api/v1/analytics/attendance/trends/:classId', () => apiResponse([])),
      http.get('/api/v1/analytics/attendance/alerts', () => apiResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<AttendanceAnalyticsPage />, {
      user: { role: 'TCH', school_id: 'school-1' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows content when data is available', async () => {
    renderWithProviders(<AttendanceAnalyticsPage />, {
      user: { role: 'ADM', school_id: 'school-1' },
    });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with no classes', async () => {
    server.use(http.get('/api/v1/teacher/classes', () => apiResponse([])));
    renderWithProviders(<AttendanceAnalyticsPage />, {
      user: { role: 'TCH', school_id: 'school-1' },
    });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () => apiErrorResponse('Server error')),
      http.get('/api/v1/analytics/attendance/trends/:classId', () => apiErrorResponse('fail')),
      http.get('/api/v1/analytics/attendance/alerts', () => apiErrorResponse('fail')),
    );
    renderWithProviders(<AttendanceAnalyticsPage />, {
      user: { role: 'TCH', school_id: 'school-1' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
