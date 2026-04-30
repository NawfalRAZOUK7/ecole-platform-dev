import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProgramsPage } from '@/features/admin/ProgramsPage';
import { renderWithProviders } from '../../utils/render';
import { apiErrorResponse, apiListResponse, apiResponse, server } from '../../utils/mocks';

interface BackendProgram {
  id: string;
  school_id: string;
  code: string;
  name: string;
  level: string | null;
  description: string | null;
  is_active: boolean;
  version_label: string;
  effective_from: string | null;
  created_at: string;
  updated_at: string | null;
}

function makeProgram(overrides: Partial<BackendProgram> = {}): BackendProgram {
  return {
    id: overrides.id ?? 'prog-1',
    school_id: 'school-1',
    code: overrides.code ?? 'SCI-MATH',
    name: overrides.name ?? 'Sciences Mathématiques',
    level: overrides.level ?? 'lycee',
    description: overrides.description ?? null,
    is_active: overrides.is_active ?? true,
    version_label: overrides.version_label ?? '1.0',
    effective_from: overrides.effective_from ?? null,
    created_at: '2026-04-01T00:00:00Z',
    updated_at: overrides.updated_at ?? null,
  };
}

describe('ProgramsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the program catalog and the create form', async () => {
    server.use(
      http.get('/api/v1/programs', () =>
        apiListResponse([
          makeProgram({ id: 'p1', code: 'SCI-MATH' }),
          makeProgram({ id: 'p2', code: 'LM', name: 'Lettres Modernes' }),
        ]),
      ),
    );

    renderWithProviders(<ProgramsPage />, { user: { role: 'ADM' } });

    expect(await screen.findByText('SCI-MATH')).toBeInTheDocument();
    expect(screen.getByText('LM')).toBeInTheDocument();
    expect(screen.getByText('Lettres Modernes')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Create program' })).toBeInTheDocument();
  });

  it('creates a new program via the inline form', async () => {
    const user = userEvent.setup();
    let createCalls = 0;
    let listCalls = 0;
    const created = makeProgram({ id: 'p-new', code: 'PHILO', name: 'Philosophie' });

    server.use(
      http.get('/api/v1/programs', () => {
        listCalls += 1;
        return apiListResponse(listCalls === 1 ? [] : [created]);
      }),
      http.post('/api/v1/programs', async ({ request }) => {
        createCalls += 1;
        const body = (await request.json()) as { code: string; name: string };
        expect(body.code).toBe('PHILO');
        expect(body.name).toBe('Philosophie');
        return apiResponse(created);
      }),
    );

    renderWithProviders(<ProgramsPage />, { user: { role: 'ADM' } });

    await screen.findByRole('heading', { name: 'Create program' });

    await user.type(screen.getByLabelText('Code'), 'PHILO');
    await user.type(screen.getByLabelText('Name'), 'Philosophie');
    await user.click(screen.getByRole('button', { name: 'Create program' }));

    expect(await screen.findByText('PHILO')).toBeInTheDocument();
    expect(createCalls).toBe(1);
  });

  it('toggles a program active/inactive via the row action', async () => {
    const user = userEvent.setup();
    let listCalls = 0;
    let patchCalls = 0;
    const program = makeProgram({ id: 'p1', code: 'SCI-MATH', is_active: true });

    server.use(
      http.get('/api/v1/programs', () => {
        listCalls += 1;
        return apiListResponse([listCalls === 1 ? program : { ...program, is_active: false }]);
      }),
      http.patch('/api/v1/programs/:id', async ({ request, params }) => {
        patchCalls += 1;
        expect(params.id).toBe('p1');
        const body = (await request.json()) as { is_active?: boolean };
        expect(body.is_active).toBe(false);
        return apiResponse({ ...program, is_active: false });
      }),
    );

    renderWithProviders(<ProgramsPage />, { user: { role: 'ADM' } });

    await screen.findByText('SCI-MATH');
    await user.click(screen.getByRole('button', { name: 'Deactivate' }));

    await waitFor(() => {
      expect(patchCalls).toBe(1);
    });
  });

  it('shows an error banner when the backend returns an error', async () => {
    server.use(http.get('/api/v1/programs', () => apiErrorResponse('Boom', 500)));

    renderWithProviders(<ProgramsPage />, { user: { role: 'ADM' } });

    expect(await screen.findByText(/Boom/i)).toBeInTheDocument();
  });
});
