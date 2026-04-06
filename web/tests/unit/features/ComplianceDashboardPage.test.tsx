import { fireEvent, screen, waitFor } from '@testing-library/react';
import { delay, http } from 'msw';
import { describe, expect, it } from 'vitest';
import { ComplianceDashboardPage } from '@/features/compliance/ComplianceDashboardPage';
import { renderWithProviders } from '../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../utils/mocks';

const dashboard = {
  school_id: 'school-1',
  academic_year_id: '2025-2026',
  curriculum_count: 1,
  total_objectives: 40,
  mapped_objectives: 33,
  overall_compliance_percent: 82,
  items: [
    {
      curriculum_id: 'curriculum-1',
      level: 'Primary',
      grade: 'Grade 6',
      subject: 'Mathematics',
      academic_year: '2025-2026',
      total_objectives: 40,
      mapped_objectives: 33,
      unmapped_objectives: 7,
      compliance_percent: 82,
    },
  ],
};

describe('ComplianceDashboardPage', () => {
  it('loads compliance data and renders metrics', async () => {
    server.use(http.get('/api/v1/compliance/dashboard', () => apiResponse(dashboard)));

    renderWithProviders(<ComplianceDashboardPage />, {
      user: { role: 'ADM' },
    });

    fireEvent.change(screen.getAllByRole('textbox')[0], {
      target: { value: '2025-2026' },
    });

    expect((await screen.findAllByText('Mathematics')).length).toBeGreaterThan(0);
    expect(screen.getAllByText('82%').length).toBeGreaterThan(0);
    expect(screen.getByText('Gap analysis')).toBeInTheDocument();
  });

  it('shows an error banner when compliance data fails to load', async () => {
    server.use(
      http.get('/api/v1/compliance/dashboard', () =>
        apiErrorResponse('Unable to load compliance dashboard')
      )
    );

    renderWithProviders(<ComplianceDashboardPage />, {
      user: { role: 'ADM' },
    });

    fireEvent.change(screen.getAllByRole('textbox')[0], {
      target: { value: '2025-2026' },
    });

    expect(await screen.findByText('Unable to load compliance dashboard')).toBeInTheDocument();
  });

  it('shows a loading state while compliance metrics are loading', async () => {
    server.use(
      http.get('/api/v1/compliance/dashboard', async () => {
        await delay(200);
        return apiResponse(dashboard);
      })
    );

    renderWithProviders(<ComplianceDashboardPage />, {
      user: { role: 'ADM' },
    });

    fireEvent.change(screen.getAllByRole('textbox')[0], {
      target: { value: '2025-2026' },
    });

    await waitFor(() => {
      expect(screen.getByRole('status', { name: 'Loading...' })).toBeInTheDocument();
    });
  });
});
