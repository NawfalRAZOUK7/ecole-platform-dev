/**
 * Teacher Courses — manage courses for assigned classes.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /courses and POST /courses.
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';

interface CourseItem {
  id: string;
  class_id: string;
  title: string;
  description: string | null;
  status: string;
}

interface ClassOption {
  id: string;
  code: string;
  name: string;
}

export function CoursesPage() {
  const { t } = useTranslation();
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [showForm, setShowForm] = useState(false);
  const [formClassId, setFormClassId] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formStatus, setFormStatus] = useState('draft');
  const [submitting, setSubmitting] = useState(false);

  // Filter
  const [filterClassId, setFilterClassId] = useState('');

  const fetchCourses = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (filterClassId) params.class_id = filterClassId;
      const resp = await api.list<CourseItem>('/courses', params);
      setCourses(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t, filterClassId]);

  const fetchClasses = useCallback(async () => {
    try {
      const resp = await api.get<ClassOption[]>('/teacher/classes');
      setClasses(resp.data);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchCourses(), fetchClasses()]).finally(() => setLoading(false));
  }, [fetchCourses, fetchClasses]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!formClassId || !formTitle.trim()) return;
    setSubmitting(true);
    try {
      await api.post('/courses', {
        class_id: formClassId,
        title: formTitle.trim(),
        description: formDesc.trim() || null,
        status: formStatus,
      });
      setShowForm(false);
      setFormTitle('');
      setFormDesc('');
      setFormStatus('draft');
      await fetchCourses();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <LoadingState />;

  // Build class name map
  const classMap: Record<string, string> = {};
  for (const c of classes) {
    classMap[c.id] = `${c.code} — ${c.name}`;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.courses.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchCourses} />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={filterClassId}
          onChange={(e) => setFilterClassId(e.target.value)}
        >
          <option value="">{t('teacher.courses.allClasses')}</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? t('app.cancel') : t('teacher.courses.create')}
        </button>
      </div>

      {showForm && (
        <form className="card" style={{ marginBottom: 20, maxWidth: 500 }} onSubmit={handleCreate}>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.courses.class')}</label>
            <select
              className="filter-select"
              value={formClassId}
              onChange={(e) => setFormClassId(e.target.value)}
              required
            >
              <option value="">{t('teacher.courses.selectClass')}</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
              ))}
            </select>
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.courses.courseTitle')}</label>
            <input
              className="filter-input"
              value={formTitle}
              onChange={(e) => setFormTitle(e.target.value)}
              required
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.courses.description')}</label>
            <input
              className="filter-input"
              value={formDesc}
              onChange={(e) => setFormDesc(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.courses.status')}</label>
            <select
              className="filter-select"
              value={formStatus}
              onChange={(e) => setFormStatus(e.target.value)}
            >
              <option value="draft">{t('teacher.courses.statusDraft')}</option>
              <option value="published">{t('teacher.courses.statusPublished')}</option>
            </select>
          </div>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? t('app.loading') : t('teacher.courses.create')}
          </button>
        </form>
      )}

      {courses.length === 0 ? (
        <EmptyState message={t('teacher.courses.empty')} />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('teacher.courses.courseTitle')}</th>
                <th>{t('teacher.courses.class')}</th>
                <th>{t('teacher.courses.status')}</th>
                <th>{t('teacher.courses.description')}</th>
              </tr>
            </thead>
            <tbody>
              {courses.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 600 }}>{c.title}</td>
                  <td>{classMap[c.class_id] || c.class_id.slice(0, 8)}</td>
                  <td>
                    <span className={`status-badge status-${c.status}`}>{c.status}</span>
                  </td>
                  <td style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
                    {c.description || '—'}
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
