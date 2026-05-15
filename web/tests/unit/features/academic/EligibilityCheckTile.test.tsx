import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EligibilityCheckTile } from '@/features/academic/programs/ui/EligibilityCheckTile';
import { renderWithProviders } from '../../../utils/render';
import { apiListResponse, apiResponse, server } from '../../../utils/mocks';

function makeProgram(id: string, code: string, name: string) {
  return {
    id,
    school_id: 'school-1',
    code,
    name,
    level: null,
    description: null,
    is_active: true,
    version_label: '1.0',
    effective_from: null,
    created_at: '2026-04-01T00:00:00Z',
    updated_at: null,
  };
}

describe('EligibilityCheckTile', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('runs the check after selecting a target program and renders the breakdown', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/programs', () =>
        apiListResponse([makeProgram('p1', 'SCI-MATH', 'Sciences Maths')]),
      ),
      http.get('/api/v1/students/std-1/eligibility', ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('kind')).toBe('PROMOTION');
        expect(url.searchParams.get('target_program_id')).toBe('p1');
        return apiResponse({
          student_id: 'std-1',
          target_program_id: 'p1',
          kind: 'PROMOTION',
          eligible: false,
          rules: [
            {
              rule_id: 'r-1',
              condition_type: 'min_attendance_rate',
              message_key: 'eligibility.attendance.required',
              passed: false,
              detail: 'rate=0.50 (required >= 0.80, n=10)',
            },
            {
              rule_id: 'r-2',
              condition_type: 'has_completed_program',
              message_key: 'eligibility.prerequisite.required',
              passed: true,
              detail: null,
            },
          ],
        });
      }),
    );

    renderWithProviders(<EligibilityCheckTile studentId="std-1" />, { user: { role: 'ADM' } });

    expect(await screen.findByText('Pick a target program to run the check.')).toBeInTheDocument();

    await screen.findByRole('option', {
      name: /SCI-MATH — Sciences Maths/,
    });
    await user.selectOptions(screen.getByLabelText('Target program'), 'p1');

    await waitFor(() => {
      expect(screen.getByText('❌ Not eligible')).toBeInTheDocument();
    });
    expect(screen.getByText('min_attendance_rate')).toBeInTheDocument();
    expect(screen.getByText('has_completed_program')).toBeInTheDocument();
  });
});
