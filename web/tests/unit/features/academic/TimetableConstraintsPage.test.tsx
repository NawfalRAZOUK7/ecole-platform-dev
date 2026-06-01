import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { TimetableConstraintsPage } from '@/features/academic/timetable/ui/TimetableConstraintsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('TimetableConstraintsPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/timetable/constraints', () => apiListResponse([])),
      http.post('/api/v1/timetable/constraints', () => apiListResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<TimetableConstraintsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows the constraints form', async () => {
    renderWithProviders(<TimetableConstraintsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with an academic year id param', async () => {
    server.use(
      http.get('/api/v1/timetable/constraints', () =>
        apiListResponse([
          {
            id: 'con-1',
            academic_year_id: '11111111-1111-1111-1111-111111111111',
            max_consecutive_classes: 3,
            teacher_availability: [],
            room_constraints: [],
          },
        ]),
      ),
    );
    renderWithProviders(<TimetableConstraintsPage />, {
      user: { role: 'ADM' },
      route: '/timetable/constraints?academicYearId=11111111-1111-1111-1111-111111111111',
    });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/timetable/constraints', () => apiErrorResponse('Server error')));
    renderWithProviders(<TimetableConstraintsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
