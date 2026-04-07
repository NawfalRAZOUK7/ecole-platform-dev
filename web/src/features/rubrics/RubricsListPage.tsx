import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';
import { useCreateRubric, useDuplicateRubric, useRubrics } from './useRubrics';
import type { CreateRubricPayload } from './rubrics.types';

const EMPTY_FORM: CreateRubricPayload = {
  title: '',
  description: '',
  subject: '',
  criteria: [],
};

export function RubricsListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const rubricsQuery = useRubrics();
  const createMutation = useCreateRubric();
  const duplicateMutation = useDuplicateRubric();

  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<CreateRubricPayload>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const rubrics = rubricsQuery.data ?? [];

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await createMutation.mutateAsync(form);
      setShowModal(false);
      setForm(EMPTY_FORM);
      navigate(`/rubrics/${created.id}/edit`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  async function handleDuplicate(id: string) {
    try {
      await duplicateMutation.mutateAsync(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (rubricsQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('rubrics.title')}</h1>
          <p className="page-subtitle">{t('rubrics.subtitle')}</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => setShowModal(true)}>
          {t('rubrics.create')}
        </button>
      </div>

      <ErrorBanner
        error={error ?? (rubricsQuery.error instanceof Error ? rubricsQuery.error.message : null)}
        onDismiss={() => setError(null)}
        onRetry={() => void rubricsQuery.refetch()}
      />

      {rubrics.length === 0 ? (
        <EmptyState message={t('rubrics.empty')} icon="📊" />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('rubrics.cols.title')}</th>
                <th>{t('rubrics.cols.subject')}</th>
                <th>{t('rubrics.cols.criteria')}</th>
                <th>{t('rubrics.cols.maxScore')}</th>
                <th>{t('rubrics.cols.createdAt')}</th>
                <th>{t('app.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {rubrics.map((rubric) => (
                <tr key={rubric.id}>
                  <td>
                    <button
                      type="button"
                      className="btn-link"
                      style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', fontWeight: 600 }}
                      onClick={() => navigate(`/rubrics/${rubric.id}/edit`)}
                    >
                      {rubric.title}
                    </button>
                  </td>
                  <td>{rubric.subject ?? '—'}</td>
                  <td>{rubric.criteria.length}</td>
                  <td>{rubric.max_score}</td>
                  <td>{formatDate(rubric.created_at)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: 13 }}
                        onClick={() => navigate(`/rubrics/${rubric.id}/edit`)}
                      >
                        {t('app.edit')}
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: 13 }}
                        onClick={() => navigate(`/rubrics/${rubric.id}/grade`)}
                      >
                        {t('rubrics.grade')}
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: 13 }}
                        disabled={duplicateMutation.isPending}
                        onClick={() => void handleDuplicate(rubric.id)}
                      >
                        {t('rubrics.duplicate')}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 440 }}>
            <h2 style={{ marginBottom: 16 }}>{t('rubrics.create')}</h2>
            <ErrorBanner error={error} onDismiss={() => setError(null)} />
            <form onSubmit={handleCreate}>
              <div className="form-field">
                <label>{t('rubrics.cols.title')}</label>
                <input className="input" required value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>
                  {t('rubrics.cols.subject')} <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>({t('app.optional')})</span>
                </label>
                <input className="input" value={form.subject ?? ''} onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value || null }))} />
              </div>
              <div className="form-field">
                <label>
                  {t('rubrics.cols.description')} <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>({t('app.optional')})</span>
                </label>
                <textarea className="input" rows={2} value={form.description ?? ''} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value || null }))} style={{ resize: 'vertical' }} />
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('app.cancel')}</button>
                <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>
                  {createMutation.isPending ? t('app.loading') : t('rubrics.createAndEdit')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
