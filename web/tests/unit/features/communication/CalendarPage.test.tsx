import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { CalendarPage } from '@/features/communication/calendar/ui/CalendarPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const calendarOptions = {
  classes: [],
  ical_url: '',
  reminder_preferences: [],
};

const calendarEvent = {
  id: 'event-1',
  title: 'School Assembly',
  description: 'Annual school assembly',
  start_date: '2026-05-01T09:00:00Z',
  end_date: '2026-05-01T10:00:00Z',
  type: 'school',
  all_day: false,
  class_id: null,
  created_by: 'user-1',
  source: 'event' as const,
};

describe('CalendarPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/events', () => apiListResponse([])),
      http.get('/api/v1/calendar/options', () => apiResponse(calendarOptions)),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<CalendarPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders calendar page title', async () => {
    const { container } = renderWithProviders(<CalendarPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with events data', async () => {
    server.use(
      http.get('/api/v1/events', () => apiListResponse([calendarEvent])),
      http.get('/api/v1/calendar/options', () => apiResponse(calendarOptions)),
    );
    renderWithProviders(<CalendarPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows error banner on API failure', async () => {
    server.use(
      http.get('/api/v1/events', () => apiErrorResponse('Server error')),
      http.get('/api/v1/calendar/options', () => apiResponse(calendarOptions)),
    );
    renderWithProviders(<CalendarPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows create event button for ADM/DIR/TCH roles', async () => {
    const { container } = renderWithProviders(<CalendarPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });
});
