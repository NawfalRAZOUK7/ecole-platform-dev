/**
 * Teacher Assignment Form — create assignment for a course.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /courses, GET /assignments, POST /assignments.
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';

interface CourseOption {
  id: string;
  title: string;
  class_id: string;
}

interface AssignmentItem {
  id: string;
  course_id: string;
  title: string;
  description: string | null;
  due_at: string | null;
  total_points: number;
}

export function AssignmentFormPage() {
  const { t } = useTranslation();
  const [courses, setCourses] = useState<CourseOption[]>([]);
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [showForm, setShowForm] = useState(false);
  const [formCourseId, setFormCourseId] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formDueAt, setFormDueAt] = useState('');
  const [formPoints, setFormPoints] = useState('20');
  const [submitting, setSubmitting] = useState(false);

  // Filter
  const [filterCourseId, setFilterCourseId] = useState('');

  const fetchCourses = useCallback(async () => {
    try {
      const resp = await api.list<CourseOption>('/courses');
      setCourses(resp.data);
    } catch { /* ignore */ }
  }, []);

  const fetchAssignments = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (filterCourseId) params.course_id = filterCourseId;
      const resp = await api.list<AssignmentItem>('/assignments', params);
      setAssignments(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t, filterCourseId]);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchCourses(), fetchAssignments()]).finally(() => setLoading(false));
  }, [fetchCourses, fetchAssignments]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!formCourseId || !formTitle.trim()) return;
    setSubmitting(true);
    try {
      await api.post('/assignments', {
        course_id: formCourseId,
        title: formTitle.trim(),
        description: formDesc.trim() || null,
        due_at: formDueAt ? new Date(formDueAt).toISOString() : null,
        total_points: parseInt(formPoints, 10) || 0,
      });
      setShowForm(false);
      setFormTitle('');
      setFormDesc('');
      setFormDueAt('');
      setFormPoints('20');
      await fetchAssignments();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <LoadingState />;

  // Course name map
  const courseMap: Record<string, string> = {};
  for (const c of courses) courseMap[c.id] = c.title;

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.assignments.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchAssignments} />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={filterCourseId}
          onChange={(e) => setFilterCourseId(e.target.value)}
        >
          <option value="">{t('teacher.assignments.allCourses')}</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>{c.title}</option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? t('app.cancel') : t('teacher.assignments.create')}
        </button>
      </div>

      {showForm && (
        <form className="card" style={{ marginBottom: 20, maxWidth: 500 }} onSubmit={handleCreate}>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.course')}</label>
            <select
              className="filter-select"
              value={formCourseId}
              onChange={(e) => setFormCourseId(e.target.value)}
              required
            >
              <option value="">{t('teacher.assignments.selectCourse')}</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.assignmentTitle')}</label>
            <input
              className="filter-input"
              value={formTitle}
              onChange={(e) => setFormTitle(e.target.value)}
              required
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.description')}</label>
            <input
              className="filter-input"
              value={formDesc}
              onChange={(e) => setFormDesc(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.dueAt')}</label>
            <input
              type="datetime-local"
              className="filter-input"
              value={formDueAt}
              onChange={(e) => setFormDueAt(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.totalPoints')}</label>
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
            {submitting ? t('app.loading') : t('teacher.assignments.create')}
          </button>
        </form>
      )}

      {assignments.length === 0 ? (
        <EmptyState message={t('teacher.assignments.empty')} />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('teacher.assignments.assignmentTitle')}</th>
                <th>{t('teacher.assignments.course')}</th>
                <th>{t('teacher.assignments.totalPoints')}</th>
                <th>{t('teacher.assignments.dueAt')}</th>
              </tr>
            </thead>
            <tbody>
              {assignments.map((a) => (
                <tr key={a.id}>
                  <td style={{ fontWeight: 600 }}>{a.title}</td>
                  <td>{courseMap[a.course_id] || a.course_id.slice(0, 8)}</td>
                  <td>{a.total_points}</td>
                  <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                    {a.due_at ? new Date(a.due_at).toLocaleString() : '—'}
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
