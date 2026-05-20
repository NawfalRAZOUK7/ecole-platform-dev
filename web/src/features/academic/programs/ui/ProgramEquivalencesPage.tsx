/**
 * Admin Program Equivalences page — Phase 3.2.
 *
 * Lists every declared equivalence in the school. Lets admins add a new
 * one (from-program, to-program, kind) and delete one. Equivalences are
 * directional and used by transcript code to reconcile program rename /
 * curriculum revisions.
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState, ErrorBanner, LoadingState, toBannerError } from '@/shared/ui';
import {
  useCreateEquivalenceMutation,
  useDeleteEquivalenceMutation,
  useProgramEquivalencesQuery,
  useProgramsQuery,
} from '../model/usePrograms';

const KINDS = ['EQUIVALENT', 'SUPERSEDES', 'PARTIAL'] as const;

export function ProgramEquivalencesPage() {
  const { t } = useTranslation();
  const programsQuery = useProgramsQuery(true);
  const equivalencesQuery = useProgramEquivalencesQuery();
  const createMutation = useCreateEquivalenceMutation();
  const deleteMutation = useDeleteEquivalenceMutation();

  const [fromProgramId, setFromProgramId] = useState('');
  const [toProgramId, setToProgramId] = useState('');
  const [kind, setKind] = useState<(typeof KINDS)[number]>('EQUIVALENT');
  const [note, setNote] = useState('');

  const programNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const p of programsQuery.data ?? []) {
      map.set(p.id, `${p.code} — ${p.name}`);
    }
    return map;
  }, [programsQuery.data]);

  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          equivalencesQuery.error ?? createMutation.error ?? deleteMutation.error,
          t('app.error'),
        ),
      [createMutation.error, deleteMutation.error, equivalencesQuery.error, t],
    ),
  );

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!fromProgramId || !toProgramId || fromProgramId === toProgramId) {
      return;
    }
    await createMutation.mutateAsync({
      from_program_id: fromProgramId,
      to_program_id: toProgramId,
      kind,
      note: note.trim() || null,
    });
    setFromProgramId('');
    setToProgramId('');
    setKind('EQUIVALENT');
    setNote('');
  }

  if (equivalencesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">
        {t('admin.equivalences.title', { defaultValue: 'Program equivalences' })}
      </h1>
      <p className="page-subtitle">
        {t('admin.equivalences.subtitle', {
          defaultValue:
            'Declare that one program is equivalent to another for transcript and history purposes.',
        })}
      </p>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void equivalencesQuery.refetch()}
      />

      <form
        className="card"
        style={{ maxWidth: 720, marginBottom: 24, padding: 16 }}
        onSubmit={handleCreate}
      >
        <h2 style={{ marginTop: 0 }}>
          {t('admin.equivalences.create', { defaultValue: 'New equivalence' })}
        </h2>
        <div className="form-field">
          <label htmlFor="eq-from">
            {t('admin.equivalences.from', { defaultValue: 'From program' })}
          </label>
          <select
            id="eq-from"
            className="filter-select"
            value={fromProgramId}
            onChange={(e) => setFromProgramId(e.target.value)}
            required
          >
            <option value="">—</option>
            {(programsQuery.data ?? []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.code} — {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="eq-to">
            {t('admin.equivalences.to', { defaultValue: 'To program' })}
          </label>
          <select
            id="eq-to"
            className="filter-select"
            value={toProgramId}
            onChange={(e) => setToProgramId(e.target.value)}
            required
          >
            <option value="">—</option>
            {(programsQuery.data ?? [])
              .filter((p) => p.id !== fromProgramId)
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code} — {p.name}
                </option>
              ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="eq-kind">{t('admin.equivalences.kind', { defaultValue: 'Kind' })}</label>
          <select
            id="eq-kind"
            className="filter-select"
            value={kind}
            onChange={(e) => setKind(e.target.value as (typeof KINDS)[number])}
          >
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="eq-note">
            {t('admin.equivalences.note', { defaultValue: 'Note (optional)' })}
          </label>
          <textarea
            id="eq-note"
            className="input"
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={
            !fromProgramId ||
            !toProgramId ||
            fromProgramId === toProgramId ||
            createMutation.isPending
          }
        >
          {createMutation.isPending
            ? t('app.loading')
            : t('admin.equivalences.create', { defaultValue: 'Create' })}
        </button>
      </form>

      {(equivalencesQuery.data?.length ?? 0) === 0 ? (
        <EmptyState
          message={t('admin.equivalences.empty', {
            defaultValue: 'No equivalences declared yet.',
          })}
          icon="🔗"
        />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('admin.equivalences.from', { defaultValue: 'From' })}</th>
                <th>{t('admin.equivalences.to', { defaultValue: 'To' })}</th>
                <th>{t('admin.equivalences.kind', { defaultValue: 'Kind' })}</th>
                <th>{t('admin.equivalences.note', { defaultValue: 'Note' })}</th>
                <th>{t('admin.programs.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {(equivalencesQuery.data ?? []).map((eq) => (
                <tr key={eq.id}>
                  <td>
                    {programNameById.get(eq.from_program_id) ?? eq.from_program_id.slice(0, 8)}
                  </td>
                  <td>{programNameById.get(eq.to_program_id) ?? eq.to_program_id.slice(0, 8)}</td>
                  <td>
                    <code>{eq.kind}</code>
                  </td>
                  <td>{eq.note ?? '—'}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => void deleteMutation.mutateAsync(eq.id)}
                      disabled={deleteMutation.isPending}
                    >
                      {t('admin.equivalences.delete', {
                        defaultValue: 'Delete',
                      })}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
