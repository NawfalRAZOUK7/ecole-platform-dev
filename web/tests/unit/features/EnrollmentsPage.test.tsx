import userEvent from '@testing-library/user-event';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EnrollmentsPage } from '@/features/admin/EnrollmentsPage';
import { renderWithProviders } from '../../utils/render';
import { apiListResponse, server } from '../../utils/mocks';

vi.mock('@/features/admin/AssignProgramDialog', () => ({
  AssignProgramDialog: ({ open }: { open: boolean }) => (open ? <h2>Assign program</h2> : null),
}));

interface BackendEnrollment {
  id: string;
  school_id: string;
  status: string;
  created_at: string | null;
  student: { id: string; full_name: string; email: string };
  class_: { id: string; code: string; name: string };
  period: {
    id: string;
    label: string | null;
    date_start: string;
    date_end: string;
  };
  academic_year: { id: string; label: string | null };
  program: {
    id: string;
    code: string;
    name: string;
    version_label: string;
  } | null;
}

function makeRow(overrides: Partial<BackendEnrollment> = {}): BackendEnrollment {
  return {
    id: overrides.id ?? 'enr-1',
    school_id: 'school-1',
    status: overrides.status ?? 'active',
    created_at: overrides.created_at ?? '2026-09-01T00:00:00Z',
    student: overrides.student ?? {
      id: 'std-1',
      full_name: 'Yassine Alaoui',
      email: 'yassine@school.test',
    },
    class_: overrides.class_ ?? {
      id: 'cls-1',
      code: '3A',
      name: 'Classe 3A',
    },
    period: overrides.period ?? {
      id: 'p-1',
      label: 'Trimester 1',
      date_start: '2026-09-01',
      date_end: '2026-12-20',
    },
    academic_year: overrides.academic_year ?? { id: 'ay-1', label: '2026-2027' },
    program:
      overrides.program === undefined
        ? { id: 'prog-1', code: 'TC', name: 'Tronc Commun', version_label: '1.0' }
        : overrides.program,
  };
}

describe('EnrollmentsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the school-wide enrollment list', async () => {
    server.use(
      http.get('/api/v1/admin/enrollments', () =>
        apiListResponse([
          makeRow(),
          makeRow({
            id: 'enr-2',
            student: {
              id: 'std-2',
              full_name: 'Salma Benani',
              email: 'salma@school.test',
            },
            program: null,
          }),
        ]),
      ),
    );

    renderWithProviders(<EnrollmentsPage />, { user: { role: 'ADM' } });

    expect(await screen.findByText('Yassine Alaoui')).toBeInTheDocument();
    expect(screen.getByText('Salma Benani')).toBeInTheDocument();
    // The programless row shows the "No program" badge.
    expect(screen.getByText('No program')).toBeInTheDocument();
  });

  it('toggles the missing_program filter and re-fetches with the right param', async () => {
    const user = userEvent.setup();
    let lastCallParams: URLSearchParams | null = null;
    server.use(
      http.get('/api/v1/admin/enrollments', ({ request }) => {
        lastCallParams = new URL(request.url).searchParams;
        return apiListResponse(
          lastCallParams.get('missing_program') === '1'
            ? [makeRow({ id: 'enr-2', program: null })]
            : [makeRow(), makeRow({ id: 'enr-2', program: null })],
        );
      }),
    );

    renderWithProviders(<EnrollmentsPage />, { user: { role: 'ADM' } });

    expect((await screen.findAllByText('Yassine Alaoui')).length).toBeGreaterThan(0);

    await user.click(screen.getByLabelText('Show only enrollments without a program'));

    await waitFor(() => {
      expect(lastCallParams?.get('missing_program')).toBe('1');
    });
  });

  it('opens AssignProgramDialog when clicking Assign program on an active row', async () => {
    server.use(
      http.get('/api/v1/admin/enrollments', () => apiListResponse([makeRow({ program: null })])),
    );

    renderWithProviders(<EnrollmentsPage />, { user: { role: 'ADM' } });

    await screen.findByText('Yassine Alaoui');
    fireEvent.click(screen.getByRole('button', { name: 'Assign program' }));

    expect(await screen.findByRole('heading', { name: 'Assign program' })).toBeInTheDocument();
  });

  it('does not show Assign program for non-active rows', async () => {
    server.use(
      http.get('/api/v1/admin/enrollments', () =>
        apiListResponse([makeRow({ status: 'transferred' })]),
      ),
    );

    renderWithProviders(<EnrollmentsPage />, { user: { role: 'ADM' } });

    await screen.findByText('Yassine Alaoui');
    expect(screen.queryByRole('button', { name: 'Assign program' })).toBeNull();
  });
});
