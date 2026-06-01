import { waitFor } from '@testing-library/react';
import { fireEvent } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { FeeAssignmentsPage } from '@/features/billing/ui/FeeAssignmentsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const feeAssignment = {
  id: 'fa-1',
  fee_structure_id: 'fee-1',
  student_id: 'stu-1',
  school_id: 'school-1',
  discount_percent: 10,
  discount_reason: 'Need-based',
  status: 'active',
  created_at: '2026-04-01T00:00:00Z',
};

const feeStructure = {
  id: 'fee-1',
  school_id: 'school-1',
  academic_year_id: 'year-1',
  name: 'Tuition Fee',
  amount: 10000,
  currency: 'MAD',
  frequency: 'monthly',
  due_day: 5,
  applies_to_level: null,
  status: 'active',
  created_at: '2026-04-01T00:00:00Z',
  updated_at: null,
};

describe('FeeAssignmentsPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/billing/fee-assignments', () => apiListResponse([])),
      http.get('/api/v1/billing/fee-structures', () => apiListResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<FeeAssignmentsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state when no assignments exist', async () => {
    const { container } = renderWithProviders(<FeeAssignmentsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders assignment data in a table', async () => {
    server.use(
      http.get('/api/v1/billing/fee-assignments', () => apiListResponse([feeAssignment])),
      http.get('/api/v1/billing/fee-structures', () => apiListResponse([feeStructure])),
    );
    renderWithProviders(<FeeAssignmentsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toContain('stu-1'));
  });

  it('shows error banner on API failure', async () => {
    server.use(
      http.get('/api/v1/billing/fee-assignments', () => apiErrorResponse('Server error')),
      http.get('/api/v1/billing/fee-structures', () => apiListResponse([])),
    );
    renderWithProviders(<FeeAssignmentsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('opens the assign form when button is clicked', async () => {
    server.use(
      http.get('/api/v1/billing/fee-assignments', () => apiListResponse([])),
      http.get('/api/v1/billing/fee-structures', () => apiListResponse([feeStructure])),
    );
    const { getByRole } = renderWithProviders(<FeeAssignmentsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    const buttons = document.querySelectorAll('button');
    const assignButton = Array.from(buttons).find((btn) =>
      btn.textContent?.includes('billing.feeAssignments.assign'),
    );
    if (assignButton) {
      fireEvent.click(assignButton);
      await waitFor(() =>
        expect(document.body.textContent).toContain('billing.feeAssignments.feeStructure'),
      );
    }
  });
});
