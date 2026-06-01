import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { SchoolSettingsPage } from '@/features/school/settings/ui/SchoolSettingsPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../../utils/mocks';

const mockSchool = {
  id: 'school-1',
  name: 'Institut El Firdaws',
  code: 'IEF',
  address: '123 Rue Mohammed V',
  city: 'Rabat',
  phone: '+212522000000',
  email: 'contact@elfirdaws.ma',
  timezone: 'Africa/Casablanca',
  default_language: 'fr',
};

describe('SchoolSettingsPage', () => {
  it('renders loading state when school is loading', () => {
    server.use(
      http.get('/api/v1/schools/:schoolId', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiResponse(mockSchool);
      }),
    );
    renderWithProviders(<SchoolSettingsPage />, {
      user: { role: 'ADM', school_id: 'school-1' },
    });
    // Loading state should show while fetching
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders school settings form with data', async () => {
    server.use(http.get('/api/v1/schools/:schoolId', () => apiResponse(mockSchool)));
    renderWithProviders(<SchoolSettingsPage />, {
      user: { role: 'ADM', school_id: 'school-1' },
    });
    expect(await screen.findByDisplayValue('Institut El Firdaws')).toBeInTheDocument();
  });

  it('shows address and city fields populated', async () => {
    server.use(http.get('/api/v1/schools/:schoolId', () => apiResponse(mockSchool)));
    renderWithProviders(<SchoolSettingsPage />, {
      user: { role: 'ADM', school_id: 'school-1' },
    });
    await waitFor(() => {
      expect(screen.getByDisplayValue('123 Rue Mohammed V')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Rabat')).toBeInTheDocument();
    });
  });

  it('renders nothing when user is null', () => {
    const { container } = renderWithProviders(<SchoolSettingsPage />, { user: null });
    expect(container.firstChild).toBeNull();
  });

  it('shows error banner when school query fails', async () => {
    server.use(
      http.get('/api/v1/schools/:schoolId', () => apiErrorResponse('School not found', 404)),
    );
    renderWithProviders(<SchoolSettingsPage />, {
      user: { role: 'ADM', school_id: 'school-1' },
    });
    await waitFor(() => {
      expect(
        screen.queryByText(/not found/i) ||
          screen.queryByText(/error/i) ||
          document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });

  it('has a save button', async () => {
    server.use(http.get('/api/v1/schools/:schoolId', () => apiResponse(mockSchool)));
    renderWithProviders(<SchoolSettingsPage />, {
      user: { role: 'ADM', school_id: 'school-1' },
    });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });
  });

  it('shows school code as read-only info', async () => {
    server.use(http.get('/api/v1/schools/:schoolId', () => apiResponse(mockSchool)));
    renderWithProviders(<SchoolSettingsPage />, {
      user: { role: 'ADM', school_id: 'school-1' },
    });
    await waitFor(() => {
      expect(screen.queryByText(/IEF/)).toBeTruthy();
    });
  });
});
