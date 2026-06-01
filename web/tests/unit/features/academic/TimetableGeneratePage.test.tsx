import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { TimetableGeneratePage } from '@/features/academic/timetable/ui/TimetableGeneratePage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('TimetableGeneratePage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/timetable/constraints', () => apiListResponse([])),
      http.post('/api/v1/timetable/generate', () => apiListResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<TimetableGeneratePage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows the generation form', async () => {
    renderWithProviders(<TimetableGeneratePage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with academic year query param', async () => {
    server.use(
      http.get('/api/v1/timetable/constraints', () =>
        apiListResponse([
          {
            id: 'con-1',
            academic_year_id: '22222222-2222-2222-2222-222222222222',
            max_consecutive_classes: 3,
            teacher_availability: [],
            room_constraints: [],
          },
        ]),
      ),
    );
    renderWithProviders(<TimetableGeneratePage />, {
      user: { role: 'ADM' },
      route: '/timetable/generate?academicYearId=22222222-2222-2222-2222-222222222222',
    });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/timetable/constraints', () => apiErrorResponse('Server error')));
    renderWithProviders(<TimetableGeneratePage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
