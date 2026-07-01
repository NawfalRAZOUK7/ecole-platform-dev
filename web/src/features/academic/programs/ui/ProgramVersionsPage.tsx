/**
 * Admin Program Versions page — Phase 3.1 follow-up.
 *
 * Per-program CRUD on curriculum versions. Operational model: annual+manual
 * editing — admins typically create one new version when curriculum is
 * revised, retire the previous one (set is_active=false, set retired_at),
 * and otherwise leave things alone.
 *
 * Route: /admin/programs/:programId/versions
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, Link } from 'react-router-dom';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState, ErrorBanner, LoadingState, toBannerError } from '@/shared/ui';
import {
  useCreateProgramVersionMutation,
  useProgramQuery,
  useProgramVersionsQuery,
  useUpdateProgramVersionMutation,
} from '../model/usePrograms';
import type { ProgramVersion } from '../api/programs.api';

export function ProgramVersionsPage() {
  const { t } = useTranslation();
  const { programId = '' } = useParams<{ programId: string }>();

  const programQuery = useProgramQuery(programId || undefined);
  const versionsQuery = useProgramVersionsQuery(programId || undefined);
  const createMutation = useCreateProgramVersionMutation();
  const updateMutation = useUpdateProgramVersionMutation();

  const [versionLabel, setVersionLabel] = useState('');
  const [description, setDescription] = useState('');
  const [effectiveFrom, setEffectiveFrom] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          versionsQuery.error ?? createMutation.error ?? updateMutation.error,
          t('app.error'),
        ),
      [createMutation.error, t, updateMutation.error, versionsQuery.error],
    ),
  );

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!programId || !versionLabel.trim()) return;
    await createMutation.mutateAsync({
      programId,
      body: {
        version_label: versionLabel.trim(),
        description: description.trim() || null,
        effective_from: effectiveFrom || null,
      },
    });
    setVersionLabel('');
    setDescription('');
    setEffectiveFrom('');
  }

  async function handleToggleActive(version: ProgramVersion) {
    setActionLoading(version.id);
    await updateMutation.mutateAsync({
      programId,
      versionId: version.id,
      body: {
        is_active: !version.is_active,
        // When deactivating without a retired_at, default it to today.
        retired_at:
          !version.is_active === false && !version.retired_at
            ? new Date().toISOString().slice(0, 10)
            : version.retired_at,
      },
    });
    setActionLoading(null);
  }

  if (versionsQuery.isLoading || programQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">
          {t('admin.versions.title', { defaultValue: 'Program versions' })}
        </h1>
        <p className="page-subtitle">
          <Link to="/admin/programs">← {t('nav.adminPrograms', { defaultValue: 'Programs' })}</Link>
          {programQuery.data ? (
            <>
              {' '}
              · <code>{programQuery.data.code}</code> — {programQuery.data.name}
            </>
          ) : null}
        </p>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void versionsQuery.refetch()}
      />

      <form
        className="card"
        style={{ maxWidth: 720, marginBottom: 24, padding: 16 }}
        onSubmit={handleCreate}
      >
        <h2 style={{ marginTop: 0 }}>
          {t('admin.versions.create', { defaultValue: 'Add a version' })}
        </h2>
        <div className="form-field">
          <label htmlFor="ver-label">
            {t('admin.versions.label', { defaultValue: 'Version label' })}
          </label>
          <input
            id="ver-label"
            className="input"
            value={versionLabel}
            onChange={(e) => setVersionLabel(e.target.value)}
            placeholder="2.0"
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="ver-effective">
            {t('admin.versions.effectiveFrom', {
              defaultValue: 'Effective from',
            })}
          </label>
          <input
            id="ver-effective"
            type="date"
            className="input"
            value={effectiveFrom}
            onChange={(e) => setEffectiveFrom(e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="ver-description">
            {t('admin.versions.description', { defaultValue: 'Description' })}
          </label>
          <textarea
            id="ver-description"
            className="input"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!versionLabel.trim() || createMutation.isPending}
        >
          {createMutation.isPending
            ? t('app.loading')
            : t('admin.versions.create', { defaultValue: 'Add version' })}
        </button>
      </form>

      {(versionsQuery.data?.length ?? 0) === 0 ? (
        <EmptyState
          message={t('admin.versions.empty', {
            defaultValue: 'No versions yet — add the first one above.',
          })}
          icon="📑"
        />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('admin.versions.label', { defaultValue: 'Version' })}</th>
                <th>
                  {t('admin.versions.effectiveFrom', {
                    defaultValue: 'Effective from',
                  })}
                </th>
                <th>{t('admin.versions.retiredAt', { defaultValue: 'Retired' })}</th>
                <th>{t('admin.programs.status', { defaultValue: 'Status' })}</th>
                <th>{t('admin.programs.actions', { defaultValue: 'Actions' })}</th>
              </tr>
            </thead>
            <tbody>
              {(versionsQuery.data ?? []).map((version) => (
                <tr key={version.id}>
                  <td>
                    <code>v{version.version_label}</code>
                  </td>
                  <td>{version.effective_from ?? '—'}</td>
                  <td>{version.retired_at ?? '—'}</td>
                  <td>
                    <span
                      className="status-badge"
                      style={{
                        color: version.is_active
                          ? 'var(--color-success)'
                          : 'var(--color-text-secondary)',
                        borderColor: version.is_active
                          ? 'var(--color-success)'
                          : 'var(--color-text-secondary)',
                      }}
                    >
                      {version.is_active
                        ? t('admin.programs.statusActive')
                        : t('admin.programs.statusInactive')}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => void handleToggleActive(version)}
                      disabled={actionLoading === version.id}
                    >
                      {version.is_active
                        ? t('admin.versions.retire', { defaultValue: 'Retire' })
                        : t('admin.programs.activate')}
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
