import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { HolidayManagerPage } from '@/features/communication/calendar/ui/HolidayManagerPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../../utils/mocks';

const mockHoliday = {
  id: 'hol-1',
  name: 'Eid Al-Fitr',
  start_date: '2026-03-30',
  end_date: '2026-04-01',
  type: 'national' as const,
  description: 'National holiday',
};

describe('HolidayManagerPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/calendar/holidays', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiResponse([mockHoliday]);
      }),
    );
    renderWithProviders(<HolidayManagerPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders holidays successfully', async () => {
    server.use(http.get('/api/v1/calendar/holidays', () => apiResponse([mockHoliday])));
    renderWithProviders(<HolidayManagerPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('Eid Al-Fitr')).toBeInTheDocument();
  });

  it('shows empty state when no holidays', async () => {
    server.use(http.get('/api/v1/calendar/holidays', () => apiResponse([])));
    renderWithProviders(<HolidayManagerPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByText(/empty/i) || document.querySelector('.empty-state__icon'),
      ).toBeTruthy();
    });
  });

  it('shows error when holidays fail to load', async () => {
    server.use(
      http.get('/api/v1/calendar/holidays', () => apiErrorResponse('Failed to load holidays')),
    );
    renderWithProviders(<HolidayManagerPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load holidays/)).toBeInTheDocument();
  });
});
