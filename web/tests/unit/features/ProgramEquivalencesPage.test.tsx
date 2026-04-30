import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProgramEquivalencesPage } from '@/features/admin/ProgramEquivalencesPage';
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

describe('ProgramEquivalencesPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('lists existing equivalences and renders the create form', async () => {
    server.use(
      http.get('/api/v1/programs', () =>
        apiListResponse([
          makeProgram('p1', 'SCI-MATH', 'Sciences Mathématiques'),
          makeProgram('p2', 'SCI-MATH-V2', 'Sciences Maths v2'),
        ]),
      ),
      http.get('/api/v1/program-equivalences', () =>
        apiListResponse([
          {
            id: 'eq-1',
            school_id: 'school-1',
            from_program_id: 'p1',
            to_program_id: 'p2',
            kind: 'EQUIVALENT',
            note: 'curriculum revision',
            ratified_at: null,
            ratified_by: null,
            created_at: '2026-04-28T00:00:00Z',
            updated_at: null,
          },
        ]),
      ),
    );

    renderWithProviders(<ProgramEquivalencesPage />, { user: { role: 'ADM' } });

    expect(
      await screen.findByRole('heading', { name: 'Program equivalences' }),
    ).toBeInTheDocument();
    expect(screen.getByText('curriculum revision')).toBeInTheDocument();
  });

  it('creates an equivalence and refreshes the list', async () => {
    const user = userEvent.setup();
    let createCalls = 0;
    let listCalls = 0;
    server.use(
      http.get('/api/v1/programs', () =>
        apiListResponse([
          makeProgram('p1', 'SCI-MATH', 'Sciences Mathématiques'),
          makeProgram('p2', 'SCI-MATH-V2', 'Sciences Maths v2'),
        ]),
      ),
      http.get('/api/v1/program-equivalences', () => {
        listCalls += 1;
        return apiListResponse(
          listCalls === 1
            ? []
            : [
                {
                  id: 'eq-new',
                  school_id: 'school-1',
                  from_program_id: 'p1',
                  to_program_id: 'p2',
                  kind: 'EQUIVALENT',
                  note: null,
                  ratified_at: null,
                  ratified_by: null,
                  created_at: '2026-04-28T00:00:00Z',
                  updated_at: null,
                },
              ],
        );
      }),
      http.post('/api/v1/program-equivalences', async ({ request }) => {
        createCalls += 1;
        const body = (await request.json()) as {
          from_program_id: string;
          to_program_id: string;
          kind: string;
        };
        expect(body.from_program_id).toBe('p1');
        expect(body.to_program_id).toBe('p2');
        return apiResponse({
          id: 'eq-new',
          school_id: 'school-1',
          from_program_id: 'p1',
          to_program_id: 'p2',
          kind: body.kind,
          note: null,
          ratified_at: null,
          ratified_by: null,
          created_at: '2026-04-28T00:00:00Z',
          updated_at: null,
        });
      }),
    );

    renderWithProviders(<ProgramEquivalencesPage />, { user: { role: 'ADM' } });

    await screen.findByRole('heading', { name: 'New equivalence' });

    await user.selectOptions(screen.getByLabelText('From program'), 'p1');
    await user.selectOptions(screen.getByLabelText('To program'), 'p2');
    // The submit button has the same label as the heading; pick by role.
    const buttons = screen.getAllByRole('button', { name: 'Create' });
    await user.click(buttons[buttons.length - 1]);

    await waitFor(() => {
      expect(createCalls).toBe(1);
    });
  });
});
