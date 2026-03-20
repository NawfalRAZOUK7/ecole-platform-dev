/**
 * Teacher Submissions — list, download files, inline grading.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /teacher/submissions and POST /submissions/{id}/grade.
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';

interface GradeInfo {
  score: number;
  feedback_text: string | null;
  published_at: string | null;
}

interface SubmissionItem {
  id: string;
  assignment_id: string;
  assignment_title: string;
  assignment_total_points: number;
  student_id: string;
  student_name: string;
  status: string;
  submitted_at: string | null;
  grade: GradeInfo | null;
}

export function SubmissionsPage() {
  const { t } = useTranslation();
  const [submissions, setSubmissions] = useState<SubmissionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);

  // Filter
  const [filterStatus, setFilterStatus] = useState('');

  // Inline grading
  const [gradingId, setGradingId] = useState<string | null>(null);
  const [gradeScore, setGradeScore] = useState('');
  const [gradeFeedback, setGradeFeedback] = useState('');
  const [gradePublish, setGradePublish] = useState(true);
  const [gradeSubmitting, setGradeSubmitting] = useState(false);

  const fetchSubmissions = useCallback(async (append = false) => {
    try {
      const params: Record<string, string | number> = {};
      if (filterStatus) params.status = filterStatus;
      if (append && cursor) params.cursor = cursor;
      const resp = await api.list<SubmissionItem>('/teacher/submissions', params);
      if (append) {
        setSubmissions((prev) => [...prev, ...resp.data]);
      } else {
        setSubmissions(resp.data);
      }
      setCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t, filterStatus, cursor]);

  useEffect(() => {
    setLoading(true);
    setCursor(null);
    const params: Record<string, string | number> = {};
    if (filterStatus) params.status = filterStatus;
    api.list<SubmissionItem>('/teacher/submissions', params)
      .then((resp) => {
        setSubmissions(resp.data);
        setCursor(resp.meta.next_cursor);
        setHasMore(resp.meta.has_more);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof ApiClientError ? err.message : t('app.error'));
      })
      .finally(() => setLoading(false));
  }, [t, filterStatus]);

  async function handleGrade(e: FormEvent, submissionId: string) {
    e.preventDefault();
    setGradeSubmitting(true);
    try {
      await api.post(`/submissions/${submissionId}/grade`, {
        score: parseFloat(gradeScore),
        feedback_text: gradeFeedback.trim() || null,
        publish: gradePublish,
      });
      setGradingId(null);
      setGradeScore('');
      setGradeFeedback('');
      // Refresh
      const params: Record<string, string | number> = {};
      if (filterStatus) params.status = filterStatus;
      const resp = await api.list<SubmissionItem>('/teacher/submissions', params);
      setSubmissions(resp.data);
      setCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setGradeSubmitting(false);
    }
  }

  function openGrading(sub: SubmissionItem) {
    setGradingId(sub.id);
    setGradeScore(sub.grade ? String(sub.grade.score) : '');
    setGradeFeedback(sub.grade?.feedback_text || '');
    setGradePublish(true);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.submissions.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="">{t('teacher.submissions.allStatuses')}</option>
          <option value="submitted">{t('teacher.submissions.statusSubmitted')}</option>
          <option value="graded">{t('teacher.submissions.statusGraded')}</option>
          <option value="draft">{t('teacher.submissions.statusDraft')}</option>
        </select>
      </div>

      {submissions.length === 0 ? (
        <EmptyState message={t('teacher.submissions.empty')} />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('teacher.submissions.student')}</th>
                  <th>{t('teacher.submissions.assignment')}</th>
                  <th>{t('teacher.submissions.status')}</th>
                  <th>{t('teacher.submissions.score')}</th>
                  <th>{t('teacher.submissions.submittedAt')}</th>
                  <th>{t('teacher.submissions.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((sub) => (
                  <tr key={sub.id}>
                    <td style={{ fontWeight: 600 }}>{sub.student_name}</td>
                    <td>{sub.assignment_title}</td>
                    <td>
                      <span className={`status-badge status-${sub.status}`}>{sub.status}</span>
                    </td>
                    <td>
                      {sub.grade
                        ? `${sub.grade.score}/${sub.assignment_total_points}`
                        : '—'}
                    </td>
                    <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {sub.submitted_at ? new Date(sub.submitted_at).toLocaleString() : '—'}
                    </td>
                    <td>
                      {(sub.status === 'submitted' || sub.status === 'graded') && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => openGrading(sub)}
                        >
                          {t('teacher.submissions.grade')}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button className="btn btn-secondary" onClick={() => fetchSubmissions(true)}>
                {t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}

      {/* Inline grading form */}
      {gradingId && (
        <div className="card" style={{ marginTop: 20, maxWidth: 500 }}>
          <h3 style={{ marginBottom: 12, fontSize: 16, fontWeight: 600 }}>
            {t('teacher.submissions.gradeSubmission')}
          </h3>
          <form onSubmit={(e) => handleGrade(e, gradingId)}>
            <div className="form-field" style={{ marginBottom: 12 }}>
              <label>{t('teacher.submissions.score')}</label>
              <input
                type="number"
                className="filter-input"
                value={gradeScore}
                onChange={(e) => setGradeScore(e.target.value)}
                required
                min="0"
                step="0.5"
                style={{ width: 120 }}
              />
            </div>
            <div className="form-field" style={{ marginBottom: 12 }}>
              <label>{t('teacher.submissions.feedback')}</label>
              <input
                className="filter-input"
                value={gradeFeedback}
                onChange={(e) => setGradeFeedback(e.target.value)}
                placeholder={t('teacher.submissions.feedbackPlaceholder')}
                style={{ width: '100%' }}
              />
            </div>
            <label className="checkbox-label" style={{ marginBottom: 12 }}>
              <input
                type="checkbox"
                checked={gradePublish}
                onChange={(e) => setGradePublish(e.target.checked)}
              />
              {t('teacher.submissions.publishGrade')}
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary" type="submit" disabled={gradeSubmitting}>
                {gradeSubmitting ? t('app.loading') : t('app.save')}
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => setGradingId(null)}
              >
                {t('app.cancel')}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
