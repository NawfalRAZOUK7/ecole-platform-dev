import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiClientError } from '@/core/api/client';
import { AssignProgramDialog } from '@/features/academic/programs/ui/AssignProgramDialog';
import { renderWithProviders } from '../../../utils/render';

const hookMocks = vi.hoisted(() => ({
  useProgramsQuery: vi.fn(),
  useAssignProgramMutation: vi.fn(),
  useProgramVersionsQuery: vi.fn(),
}));

vi.mock('@/features/academic/programs/model/usePrograms', () => ({
  useProgramsQuery: hookMocks.useProgramsQuery,
  useAssignProgramMutation: hookMocks.useAssignProgramMutation,
  useProgramVersionsQuery: hookMocks.useProgramVersionsQuery,
}));

function makeProgram(id: string, code: string, name: string) {
  return {
    id,
    school_id: 'school-1',
    code,
    name,
    level: 'lycee',
    description: null,
    is_active: true,
    version_label: '1.0',
    effective_from: null,
    created_at: '2026-04-01T00:00:00Z',
    updated_at: null,
  };
}

function stubHooks(overrides?: {
  programs?: unknown[];
  versions?: unknown[];
  mutation?: Record<string, unknown>;
}) {
  hookMocks.useProgramsQuery.mockReturnValue({
    data: overrides?.programs ?? [],
  });
  hookMocks.useProgramVersionsQuery.mockReturnValue({
    data: overrides?.versions ?? [],
  });
  hookMocks.useAssignProgramMutation.mockReturnValue({
    mutateAsync: vi.fn(),
    reset: vi.fn(),
    error: null,
    isPending: false,
    ...overrides?.mutation,
  });
}

describe('AssignProgramDialog', () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it('renders nothing when closed', () => {
    stubHooks({
      programs: [makeProgram('p1', 'SCI-MATH', 'Sciences Mathématiques')],
    });

    renderWithProviders(
      <AssignProgramDialog open={false} enrollmentId="e1" onClose={() => undefined} />,
      { user: { role: 'ADM' } },
    );

    expect(screen.queryByRole('heading', { name: 'Assign program' })).toBeNull();
  });

  it('lists active programs and calls mutateAsync on submit', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({
      id: 'evt-1',
    });
    stubHooks({
      programs: [
        makeProgram('p1', 'SCI-MATH', 'Sciences Mathématiques'),
        makeProgram('p2', 'LM', 'Lettres Modernes'),
      ],
      mutation: { mutateAsync },
    });

    const onClose = vi.fn();
    const onAssigned = vi.fn();

    renderWithProviders(
      <AssignProgramDialog
        open
        enrollmentId="e1"
        currentProgramId="p1"
        studentId="std-1"
        onClose={onClose}
        onAssigned={onAssigned}
      />,
      { user: { role: 'ADM' } },
    );

    expect(await screen.findByRole('heading', { name: 'Assign program' })).toBeInTheDocument();

    const select = screen.getByLabelText('Program') as HTMLSelectElement;
    expect(within(select).queryByText(/SCI-MATH/)).toBeNull();
    expect(within(select).getByText(/LM/)).toBeInTheDocument();

    fireEvent.change(select, { target: { value: 'p2' } });
    fireEvent.click(screen.getByLabelText('Transfer (mid-period)'));
    fireEvent.click(screen.getByRole('button', { name: 'Assign program' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        enrollmentId: 'e1',
        body: {
          program_id: 'p2',
          program_version_id: null,
          reason_code: 'TRANSFER',
          reason_note: null,
        },
        studentId: 'std-1',
      });
    });
    expect(onAssigned).toHaveBeenCalledWith('evt-1');
    expect(onClose).toHaveBeenCalled();
  });

  it('surfaces a backend conflict already present on the mutation hook', async () => {
    stubHooks({
      programs: [makeProgram('p1', 'SCI-MATH', 'Sciences Mathématiques')],
      mutation: {
        error: new ApiClientError(409, {
          code: 'ERR-SYS-409',
          message: 'Enrollment already assigned to this program',
          category: 'conflict',
          retryable: false,
          timestamp: new Date().toISOString(),
        }),
      },
    });

    renderWithProviders(<AssignProgramDialog open enrollmentId="e1" onClose={() => undefined} />, {
      user: { role: 'ADM' },
    });

    expect(
      await screen.findByText(/Enrollment already assigned to this program/i),
    ).toBeInTheDocument();
  });
});
