/**
 * Teacher Assessment Form — create and publish assessments.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /assessments, POST /assessments, POST /assessments/{id}/publish.
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';

interface ClassOption {
  id: string;
  code: string;
  name: string;
}

interface AssessmentItem {
  id: string;
  class_id: string;
  title: string;
  due_at: string | null;
  window_end: string | null;
  total_points: number;
  status: string;
}

export function AssessmentFormPage() {
  const { t } = useTranslation();
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [assessments, setAssessments] = useState<AssessmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [showForm, setShowForm] = useState(false);
  const [formClassId, setFormClassId] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formDueAt, setFormDueAt] = useState('');
  const [formWindowEnd, setFormWindowEnd] = useState('');
  const [formPoints, setFormPoints] = useState('20');
  const [submitting, setSubmitting] = useState(false);

  // Filter
  const [filterClassId, setFilterClassId] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const fetchClasses = useCallback(async () => {
    try {
      const resp = await api.get<ClassOption[]>('/teacher/classes');
      setClasses(resp.data);
    } catch { /* ignore */ }
  }, []);

  const fetchAssessments = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (filterClassId) params.class_id = filterClassId;
      if (filterStatus) params.status = filterStatus;
      const resp = await api.list<AssessmentItem>('/assessments', params);
      setAssessments(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t, filterClassId, filterStatus]);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchClasses(), fetchAssessments()]).finally(() => setLoading(false));
  }, [fetchClasses, fetchAssessments]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!formClassId || !formTitle.trim()) return;
    setSubmitting(true);
    try {
      await api.post('/assessments', {
        class_id: formClassId,
        title: formTitle.trim(),
        due_at: formDueAt ? new Date(formDueAt).toISOString() : null,
        window_end: formWindowEnd ? new Date(formWindowEnd).toISOString() : null,
        total_points: parseInt(formPoints, 10) || 0,
        status: 'draft',
      });
      setShowForm(false);
      setFormTitle('');
      setFormDueAt('');
      setFormWindowEnd('');
      setFormPoints('20');
      await fetchAssessments();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePublish(assessmentId: string) {
    try {
      await api.post(`/assessments/${assessmentId}/publish`);
      await fetchAssessments();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  if (loading) return <LoadingState />;

  // Class name map
  const classMap: Record<string, string> = {};
  for (const c of classes) classMap[c.id] = `${c.code} — ${c.name}`;

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.assessments.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchAssessments} />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={filterClassId}
          onChange={(e) => setFilterClassId(e.target.value)}
        >
          <option value="">{t('teacher.assessments.allClasses')}</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
          ))}
        </select>
        <select
          className="filter-select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="">{t('teacher.assessments.allStatuses')}</option>
          <option value="draft">{t('teacher.assessments.statusDraft')}</option>
          <option value="published">{t('teacher.assessments.statusPublished')}</option>
          <option value="closed">{t('teacher.assessments.statusClosed')}</option>
        </select>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? t('app.cancel') : t('teacher.assessments.create')}
        </button>
      </div>

      {showForm && (
        <form className="card" style={{ marginBottom: 20, maxWidth: 500 }} onSubmit={handleCreate}>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.class')}</label>
            <select
              className="filter-select"
              value={formClassId}
              onChange={(e) => setFormClassId(e.target.value)}
              required
            >
              <option value="">{t('teacher.assessments.selectClass')}</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
              ))}
            </select>
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.assessmentTitle')}</label>
            <input
              className="filter-input"
              value={formTitle}
              onChange={(e) => setFormTitle(e.target.value)}
              required
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.dueAt')}</label>
            <input
              type="datetime-local"
              className="filter-input"
              value={formDueAt}
              onChange={(e) => setFormDueAt(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.windowEnd')}</label>
            <input
              type="datetime-local"
              className="filter-input"
              value={formWindowEnd}
              onChange={(e) => setFormWindowEnd(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.totalPoints')}</label>
            <input
              type="number"
              className="filter-input"
              value={formPoints}
              onChange={(e) => setFormPoints(e.target.value)}
              min="0"
              style={{ width: 120 }}
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? t('app.loading') : t('teacher.assessments.create')}
          </button>
        </form>
      )}

      {assessments.length === 0 ? (
        <EmptyState message={t('teacher.assessments.empty')} />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('teacher.assessments.assessmentTitle')}</th>
                <th>{t('teacher.assessments.class')}</th>
                <th>{t('teacher.assessments.totalPoints')}</th>
                <th>{t('teacher.assessments.status')}</th>
                <th>{t('teacher.assessments.dueAt')}</th>
                <th>{t('teacher.submissions.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {assessments.map((a) => (
                <tr key={a.id}>
                  <td style={{ fontWeight: 600 }}>{a.title}</td>
                  <td>{classMap[a.class_id] || a.class_id.slice(0, 8)}</td>
                  <td>{a.total_points}</td>
                  <td>
                    <span className={`status-badge status-${a.status}`}>{a.status}</span>
                  </td>
                  <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                    {a.due_at ? new Date(a.due_at).toLocaleString() : '—'}
                  </td>
                  <td>
                    {a.status === 'draft' && (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handlePublish(a.id)}
                      >
                        {t('teacher.assessments.publish')}
                      </button>
                    )}
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
