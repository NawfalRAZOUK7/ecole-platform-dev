import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EligibilityRulesPage } from '@/features/admin/EligibilityRulesPage';
import { renderWithProviders } from '../../utils/render';
import { apiListResponse, apiResponse, server } from '../../utils/mocks';

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

describe('EligibilityRulesPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the catalog and creates a new rule with parsed JSON params', async () => {
    const user = userEvent.setup();
    let createCalls = 0;
    let listCalls = 0;

    server.use(
      http.get('/api/v1/programs', () =>
        apiListResponse([makeProgram('p1', 'SCI-MATH', 'Sciences Mathématiques')]),
      ),
      http.get('/api/v1/eligibility/rules', () => {
        listCalls += 1;
        return apiListResponse(
          listCalls === 1
            ? []
            : [
                {
                  id: 'r-1',
                  school_id: 'school-1',
                  kind: 'PROMOTION',
                  target_program_id: 'p1',
                  condition_type: 'min_attendance_rate',
                  condition_params: { min_rate: 0.8 },
                  message_key: 'eligibility.attendance.required',
                  is_active: true,
                  created_at: '2026-04-28T00:00:00Z',
                  updated_at: null,
                },
              ],
        );
      }),
      http.post('/api/v1/eligibility/rules', async ({ request }) => {
        createCalls += 1;
        const body = (await request.json()) as {
          kind: string;
          target_program_id: string;
          condition_type: string;
          condition_params: Record<string, unknown>;
          message_key: string;
        };
        expect(body.kind).toBe('PROMOTION');
        expect(body.target_program_id).toBe('p1');
        expect(body.condition_type).toBe('min_attendance_rate');
        expect(body.condition_params).toEqual({ min_rate: 0.8 });
        return apiResponse({
          id: 'r-1',
          school_id: 'school-1',
          kind: body.kind,
          target_program_id: body.target_program_id,
          condition_type: body.condition_type,
          condition_params: body.condition_params,
          message_key: body.message_key,
          is_active: true,
          created_at: '2026-04-28T00:00:00Z',
          updated_at: null,
        });
      }),
    );

    renderWithProviders(<EligibilityRulesPage />, { user: { role: 'ADM' } });

    await screen.findByRole('heading', { name: 'New rule' });

    await user.selectOptions(screen.getByLabelText('Target program'), 'p1');
    await user.selectOptions(screen.getByLabelText('Condition type'), 'min_attendance_rate');
    const params = screen.getByLabelText('Parameters (JSON)');
    await user.clear(params);
    await user.type(params, '{{"min_rate": 0.8}');
    await user.type(screen.getByLabelText('Message key (i18n)'), 'eligibility.attendance.required');
    const buttons = screen.getAllByRole('button', { name: 'Create' });
    await user.click(buttons[buttons.length - 1]);

    await waitFor(() => {
      expect(createCalls).toBe(1);
    });
  });
});
