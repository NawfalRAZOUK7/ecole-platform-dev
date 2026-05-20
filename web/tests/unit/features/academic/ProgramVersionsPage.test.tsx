import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProgramVersionsPage } from '@/features/academic/programs/ui/ProgramVersionsPage';
import { renderWithProviders } from '../../../utils/render';
import { apiListResponse, apiResponse, server } from '../../../utils/mocks';

const PROGRAM_ID = 'prog-1';

function makeVersion(overrides: Record<string, unknown> = {}) {
  return {
    id: 'v-1',
    school_id: 'school-1',
    program_id: PROGRAM_ID,
    version_label: '1.0',
    description: null,
    effective_from: null,
    retired_at: null,
    is_active: true,
    created_at: '2026-04-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function renderAtRoute() {
  return renderWithProviders(
    <Routes>
      <Route path="/admin/programs/:programId/versions" element={<ProgramVersionsPage />} />
    </Routes>,
    {
      route: `/admin/programs/${PROGRAM_ID}/versions`,
      user: { role: 'ADM' },
    },
  );
}

describe('ProgramVersionsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders existing versions and lets admin create a new one', async () => {
    const user = userEvent.setup();
    let createCalls = 0;
    let listCalls = 0;

    server.use(
      http.get(`/api/v1/programs/${PROGRAM_ID}`, () =>
        apiResponse({
          id: PROGRAM_ID,
          school_id: 'school-1',
          code: 'SCI-MATH',
          name: 'Sciences Mathématiques',
          level: null,
          description: null,
          is_active: true,
          version_label: '1.0',
          effective_from: null,
          created_at: '2026-04-01T00:00:00Z',
          updated_at: null,
        }),
      ),
      http.get(`/api/v1/programs/${PROGRAM_ID}/versions`, () => {
        listCalls += 1;
        return apiListResponse(
          listCalls === 1
            ? [makeVersion()]
            : [makeVersion(), makeVersion({ id: 'v-2', version_label: '2.0' })],
        );
      }),
      http.post(`/api/v1/programs/${PROGRAM_ID}/versions`, async ({ request }) => {
        createCalls += 1;
        const body = (await request.json()) as { version_label: string };
        return apiResponse(makeVersion({ id: 'v-2', version_label: body.version_label }));
      }),
    );

    renderAtRoute();

    expect(await screen.findByText('v1.0')).toBeInTheDocument();

    await user.type(screen.getByLabelText('Version label'), '2.0');
    await user.click(screen.getByRole('button', { name: 'Add version' }));

    await waitFor(() => {
      expect(createCalls).toBe(1);
    });
    expect(await screen.findByText('v2.0')).toBeInTheDocument();
  });

  it('toggles a version to retired via PATCH', async () => {
    const user = userEvent.setup();
    let patchCalls = 0;

    server.use(
      http.get(`/api/v1/programs/${PROGRAM_ID}`, () =>
        apiResponse({
          id: PROGRAM_ID,
          school_id: 'school-1',
          code: 'SCI-MATH',
          name: 'Sciences Mathématiques',
          level: null,
          description: null,
          is_active: true,
          version_label: '1.0',
          effective_from: null,
          created_at: '2026-04-01T00:00:00Z',
          updated_at: null,
        }),
      ),
      http.get(`/api/v1/programs/${PROGRAM_ID}/versions`, () => apiListResponse([makeVersion()])),
      http.patch(`/api/v1/programs/${PROGRAM_ID}/versions/v-1`, async ({ request }) => {
        patchCalls += 1;
        const body = (await request.json()) as { is_active: boolean };
        expect(body.is_active).toBe(false);
        return apiResponse(makeVersion({ is_active: false }));
      }),
    );

    renderAtRoute();

    await screen.findByText('v1.0');
    await user.click(screen.getByRole('button', { name: 'Retire' }));

    await waitFor(() => {
      expect(patchCalls).toBe(1);
    });
  });
});
