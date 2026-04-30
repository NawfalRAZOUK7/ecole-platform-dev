/**
 * Admin Programs page — CRUD for academic programs (filières) — G49 Phase 2.
 *
 * Calls:
 *   GET   /programs
 *   POST  /programs
 *   PATCH /programs/:id
 *
 * Permissions:
 *   Read   — PERM-ERP:program:read   (ADM, DIR, TCH, STD, PAR)
 *   Manage — PERM-ERP:program:manage (ADM, DIR)
 *   Mount this page under a ProtectedRoute roles={['ADM','DIR']}.
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState, ErrorBanner, LoadingState, toBannerError } from '@/shared/ui';
import {
  useCreateProgramMutation,
  useProgramsQuery,
  useUpdateProgramMutation,
} from './usePrograms';
import type { Program, ProgramCreatePayload } from './programs.service';

// ---------------------------------------------------------------------------
// Inline create form (no modal — keeps the page simple, matches the existing
// SchoolSettingsPage and BadgesPage idioms)
// ---------------------------------------------------------------------------
interface CreateFormState {
  code: string;
  name: string;
  level: string;
  description: string;
  version_label: string;
  effective_from: string;
}

const EMPTY_CREATE: CreateFormState = {
  code: '',
  name: '',
  level: '',
  description: '',
  version_label: '1.0',
  effective_from: '',
};

function payloadFromForm(form: CreateFormState): ProgramCreatePayload {
  return {
    code: form.code.trim(),
    name: form.name.trim(),
    level: form.level.trim() || null,
    description: form.description.trim() || null,
    version_label: form.version_label.trim() || '1.0',
    effective_from: form.effective_from || null,
  };
}

export function ProgramsPage() {
  const { t } = useTranslation();
  const [showInactive, setShowInactive] = useState(false);
  const [createForm, setCreateForm] = useState<CreateFormState>(EMPTY_CREATE);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editLevel, setEditLevel] = useState('');
  const [editVersion, setEditVersion] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const programsQuery = useProgramsQuery(!showInactive);
  const createMutation = useCreateProgramMutation();
  const updateMutation = useUpdateProgramMutation();

  const items = useMemo<Program[]>(() => programsQuery.data ?? [], [programsQuery.data]);

  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          programsQuery.error ?? createMutation.error ?? updateMutation.error,
          t('app.error'),
        ),
      [createMutation.error, programsQuery.error, t, updateMutation.error],
    ),
  );

  function updateCreateField<K extends keyof CreateFormState>(key: K, value: CreateFormState[K]) {
    setCreateForm((current) => ({ ...current, [key]: value }));
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!createForm.code.trim() || !createForm.name.trim()) {
      return;
    }
    await createMutation.mutateAsync(payloadFromForm(createForm));
    setCreateForm(EMPTY_CREATE);
  }

  function startEdit(program: Program) {
    setEditingId(program.id);
    setEditName(program.name);
    setEditLevel(program.level ?? '');
    setEditVersion(program.version_label);
  }

  function cancelEdit() {
    setEditingId(null);
  }

  async function saveEdit(program: Program) {
    setActionLoading(program.id);
    await updateMutation.mutateAsync({
      programId: program.id,
      body: {
        name: editName.trim() || program.name,
        level: editLevel.trim() || null,
        version_label: editVersion.trim() || program.version_label,
      },
    });
    setEditingId(null);
    setActionLoading(null);
  }

  async function toggleActive(program: Program) {
    setActionLoading(program.id);
    await updateMutation.mutateAsync({
      programId: program.id,
      body: { is_active: !program.is_active },
    });
    setActionLoading(null);
  }

  if (programsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.programs.title')}</h1>
      <p className="page-subtitle">{t('admin.programs.subtitle')}</p>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void programsQuery.refetch()}
      />

      {/* Create form */}
      <form
        className="card"
        style={{ maxWidth: 720, marginBottom: 24, padding: 16 }}
        onSubmit={handleCreate}
      >
        <h2 style={{ marginTop: 0 }}>{t('admin.programs.createTitle')}</h2>
        <div className="form-field">
          <label htmlFor="prog-code">{t('admin.programs.code')}</label>
          <input
            id="prog-code"
            className="input"
            value={createForm.code}
            onChange={(e) => updateCreateField('code', e.target.value)}
            placeholder="SCI-MATH"
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="prog-name">{t('admin.programs.name')}</label>
          <input
            id="prog-name"
            className="input"
            value={createForm.name}
            onChange={(e) => updateCreateField('name', e.target.value)}
            placeholder="Sciences Mathématiques"
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="prog-level">{t('admin.programs.level')}</label>
          <input
            id="prog-level"
            className="input"
            value={createForm.level}
            onChange={(e) => updateCreateField('level', e.target.value)}
            placeholder="lycee"
          />
        </div>
        <div className="form-field">
          <label htmlFor="prog-version">{t('admin.programs.versionLabel')}</label>
          <input
            id="prog-version"
            className="input"
            value={createForm.version_label}
            onChange={(e) => updateCreateField('version_label', e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="prog-effective">{t('admin.programs.effectiveFrom')}</label>
          <input
            id="prog-effective"
            type="date"
            className="input"
            value={createForm.effective_from}
            onChange={(e) => updateCreateField('effective_from', e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="prog-description">{t('admin.programs.description')}</label>
          <textarea
            id="prog-description"
            className="input"
            rows={3}
            value={createForm.description}
            onChange={(e) => updateCreateField('description', e.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>
          {createMutation.isPending ? t('app.loading') : t('admin.programs.create')}
        </button>
      </form>

      {/* Filters */}
      <div className="filters-bar" style={{ marginBottom: 12 }}>
        <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
          />
          {t('admin.programs.showInactive')}
        </label>
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('admin.programs.empty')} icon="📚" />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('admin.programs.code')}</th>
                <th>{t('admin.programs.name')}</th>
                <th>{t('admin.programs.level')}</th>
                <th>{t('admin.programs.versionLabel')}</th>
                <th>{t('admin.programs.status')}</th>
                <th>{t('admin.programs.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((program) => {
                const isEditing = editingId === program.id;
                return (
                  <tr key={program.id}>
                    <td>
                      <code>{program.code}</code>
                    </td>
                    <td>
                      {isEditing ? (
                        <input
                          className="input"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                        />
                      ) : (
                        program.name
                      )}
                    </td>
                    <td>
                      {isEditing ? (
                        <input
                          className="input"
                          value={editLevel}
                          onChange={(e) => setEditLevel(e.target.value)}
                        />
                      ) : (
                        program.level || '—'
                      )}
                    </td>
                    <td>
                      {isEditing ? (
                        <input
                          className="input"
                          value={editVersion}
                          onChange={(e) => setEditVersion(e.target.value)}
                          style={{ width: 80 }}
                        />
                      ) : (
                        program.version_label
                      )}
                    </td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          color: program.is_active
                            ? 'var(--color-success)'
                            : 'var(--color-text-secondary)',
                          borderColor: program.is_active
                            ? 'var(--color-success)'
                            : 'var(--color-text-secondary)',
                        }}
                      >
                        {program.is_active
                          ? t('admin.programs.statusActive')
                          : t('admin.programs.statusInactive')}
                      </span>
                    </td>
                    <td>
                      {isEditing ? (
                        <>
                          <button
                            type="button"
                            className="btn btn-primary btn-sm"
                            onClick={() => void saveEdit(program)}
                            disabled={actionLoading === program.id}
                          >
                            {t('app.save')}
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={cancelEdit}
                            style={{ marginInlineStart: 4 }}
                          >
                            {t('app.cancel')}
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => startEdit(program)}
                          >
                            {t('admin.programs.edit')}
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => void toggleActive(program)}
                            disabled={actionLoading === program.id}
                            style={{ marginInlineStart: 4 }}
                          >
                            {program.is_active
                              ? t('admin.programs.deactivate')
                              : t('admin.programs.activate')}
                          </button>
                          <Link
                            to={`/admin/programs/${program.id}/versions`}
                            className="btn btn-secondary btn-sm"
                            style={{ marginInlineStart: 4 }}
                          >
                            {t('admin.programs.manageVersions', {
                              defaultValue: 'Versions',
                            })}
                          </Link>
                        </>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
