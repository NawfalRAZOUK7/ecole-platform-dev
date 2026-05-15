import { screen } from '@testing-library/react';
import { http } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { StudentAcademicHistoryPage } from '@/features/academic/programs/ui/StudentAcademicHistoryPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, apiResponse, server } from '../../../utils/mocks';
import { HttpResponse } from 'msw';

const STUDENT_ID = 'std-1';

function makeTimelineEntry(overrides: Record<string, unknown> = {}) {
  return {
    enrollment_id: 'enr-1',
    academic_year_id: 'ay-2026',
    academic_year_label: '2026-2027',
    academic_year_start: '2026-09-01',
    academic_year_end: '2027-07-15',
    period_id: 'p-1',
    period_label: 'Trimester 1',
    period_start: '2026-09-01',
    period_end: '2026-12-20',
    class_id: 'cls-1',
    class_code: '3A',
    class_name: 'Classe 3A',
    program: { id: 'prog-1', code: 'TC', name: 'Tronc Commun', version_label: '1.0' },
    status: 'active',
    ...overrides,
  };
}

function renderAtRoute(options?: { snapshots?: unknown[] }) {
  server.use(
    http.get(`/api/v1/students/${STUDENT_ID}/snapshots`, () =>
      apiListResponse(options?.snapshots ?? []),
    ),
    http.get('/api/v1/programs', () => apiListResponse([])),
  );

  return renderWithProviders(
    <Routes>
      <Route
        path="/students/:studentId/academic-history"
        element={<StudentAcademicHistoryPage />}
      />
    </Routes>,
    {
      route: `/students/${STUDENT_ID}/academic-history`,
      user: { role: 'ADM' },
    },
  );
}

describe('StudentAcademicHistoryPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders current program, timeline, and history when present', async () => {
    server.use(
      http.get(`/api/v1/students/${STUDENT_ID}/current-program`, () =>
        apiResponse({
          student_id: STUDENT_ID,
          academic_year_id: 'ay-2026',
          period_id: 'p-1',
          enrollment_id: 'enr-1',
          program: {
            id: 'prog-2',
            code: 'SCI-MATH',
            name: 'Sciences Mathématiques',
            version_label: '1.0',
          },
        }),
      ),
      http.get(`/api/v1/students/${STUDENT_ID}/academic-timeline`, () =>
        apiListResponse([
          makeTimelineEntry({ status: 'transferred' }),
          makeTimelineEntry({
            enrollment_id: 'enr-2',
            program: {
              id: 'prog-2',
              code: 'SCI-MATH',
              name: 'Sciences Mathématiques',
              version_label: '1.0',
            },
          }),
        ]),
      ),
      http.get(`/api/v1/students/${STUDENT_ID}/program-history`, () =>
        apiListResponse([
          {
            id: 'evt-2',
            school_id: 'school-1',
            student_id: STUDENT_ID,
            academic_year_id: 'ay-2026',
            period_id: 'p-1',
            from_program_id: 'prog-1',
            to_program_id: 'prog-2',
            from_enrollment_id: 'enr-1',
            to_enrollment_id: 'enr-2',
            reason_code: 'TRANSFER',
            reason_note: 'parent request',
            actor_user_id: 'user-1',
            occurred_at: '2026-10-01T00:00:00Z',
          },
          {
            id: 'evt-1',
            school_id: 'school-1',
            student_id: STUDENT_ID,
            academic_year_id: 'ay-2026',
            period_id: 'p-1',
            from_program_id: null,
            to_program_id: 'prog-1',
            from_enrollment_id: 'enr-1',
            to_enrollment_id: 'enr-1',
            reason_code: 'INITIAL',
            reason_note: null,
            actor_user_id: 'user-1',
            occurred_at: '2026-09-01T00:00:00Z',
          },
        ]),
      ),
    );

    renderAtRoute({
      snapshots: [
        {
          id: 'snap-1',
          school_id: 'school-1',
          student_id: STUDENT_ID,
          academic_year_id: 'ay-2026',
          snapshot_kind: 'MANUAL',
          snapshot_data: {},
          taken_at: '2026-10-01T00:00:00Z',
          taken_by: 'user-1',
        },
      ],
    });

    // Current program card
    expect((await screen.findAllByText(/Sciences Mathématiques/)).length).toBeGreaterThanOrEqual(2);

    // Timeline group header (academic year label) and both rows
    expect(screen.getByText('2026-2027')).toBeInTheDocument();
    expect(screen.getAllByText(/3A/).length).toBeGreaterThanOrEqual(2);

    // History event log: both reasons render
    expect(screen.getByText('Transfer (mid-period)')).toBeInTheDocument();
    expect(screen.getByText('Initial assignment')).toBeInTheDocument();

    // The transfer note is rendered
    expect(screen.getByText(/parent request/)).toBeInTheDocument();
  });

  it('opens a real transcript preview modal from the live preview action', async () => {
    const user = userEvent.setup();
    const printSpy = vi.fn();
    const focusSpy = vi.fn();
    const contentWindowDescriptor = Object.getOwnPropertyDescriptor(
      HTMLIFrameElement.prototype,
      'contentWindow',
    );
    Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
      configurable: true,
      get() {
        return {
          focus: focusSpy,
          print: printSpy,
        };
      },
    });

    try {
      server.use(
        http.get(`/api/v1/students/${STUDENT_ID}/current-program`, () =>
          apiResponse({
            student_id: STUDENT_ID,
            academic_year_id: 'ay-2026',
            period_id: 'p-1',
            enrollment_id: 'enr-1',
            program: {
              id: 'prog-2',
              code: 'SCI-MATH',
              name: 'Sciences Mathématiques',
              version_label: '1.0',
            },
          }),
        ),
        http.get(`/api/v1/students/${STUDENT_ID}/academic-timeline`, () =>
          apiListResponse([makeTimelineEntry()]),
        ),
        http.get(`/api/v1/students/${STUDENT_ID}/program-history`, () => apiListResponse([])),
        http.get(
          `/api/v1/students/${STUDENT_ID}/transcript/html`,
          () =>
            new HttpResponse('<html><body><h1>Live transcript</h1></body></html>', {
              headers: { 'Content-Type': 'text/html' },
            }),
        ),
      );

      renderAtRoute();

      await user.click(await screen.findByRole('button', { name: /Live transcript preview/i }));
      expect(
        await screen.findByRole('dialog', { name: /Live transcript preview/i }),
      ).toBeInTheDocument();
      expect(screen.getByTitle(/Live transcript preview/i)).toHaveAttribute(
        'srcdoc',
        expect.stringContaining('Live transcript'),
      );

      await user.click(screen.getByRole('button', { name: 'Print' }));
      expect(focusSpy).toHaveBeenCalled();
      expect(printSpy).toHaveBeenCalled();
    } finally {
      if (contentWindowDescriptor) {
        Object.defineProperty(
          HTMLIFrameElement.prototype,
          'contentWindow',
          contentWindowDescriptor,
        );
      }
    }
  });

  it('shows the empty timeline + empty history empty states when nothing exists', async () => {
    server.use(
      http.get(`/api/v1/students/${STUDENT_ID}/current-program`, () =>
        apiResponse({
          student_id: STUDENT_ID,
          academic_year_id: null,
          period_id: null,
          enrollment_id: null,
          program: null,
        }),
      ),
      http.get(`/api/v1/students/${STUDENT_ID}/academic-timeline`, () => apiListResponse([])),
      http.get(`/api/v1/students/${STUDENT_ID}/program-history`, () => apiListResponse([])),
    );

    renderAtRoute();

    expect(await screen.findByText('No active program assigned yet.')).toBeInTheDocument();
    expect(screen.getByText('No enrollments recorded yet.')).toBeInTheDocument();
    expect(screen.getByText('No program changes recorded yet.')).toBeInTheDocument();
  });

  it('surfaces a 404 (scope-masked student) via the error banner', async () => {
    server.use(
      http.get(`/api/v1/students/${STUDENT_ID}/current-program`, () =>
        apiErrorResponse('Resource not found', 404),
      ),
      http.get(`/api/v1/students/${STUDENT_ID}/academic-timeline`, () =>
        apiErrorResponse('Resource not found', 404),
      ),
      http.get(`/api/v1/students/${STUDENT_ID}/program-history`, () =>
        apiErrorResponse('Resource not found', 404),
      ),
    );

    renderAtRoute();

    await screen.findByText('Loading...');
    expect(await screen.findByRole('alert')).toHaveTextContent(/Resource not found/i);
  });
});
