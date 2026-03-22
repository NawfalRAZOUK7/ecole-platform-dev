/**
 * Results page — student/parent results listing + quiz results.
 *
 * Reference: S-081 — Results page
 * Phase 10B — Parent quiz results alongside assignment grades.
 * Calls GET /results with cursor pagination. STD and PAR roles.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface Result {
  assignment_id: string;
  assignment_title: string;
  course_title: string;
  due_at: string | null;
  submitted_at: string | null;
  score: number | null;
  out_of: number | null;
  letter_grade: string | null;
  feedback: string | null;
  submission_status: string;
}

interface QuizAttemptResult {
  id: string;
  quiz_id: string;
  quiz_title?: string;
  attempt_no: number;
  score: number | null;
  max_score: number | null;
  status: string;
  completed_at: string | null;
}

export function ResultsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [items, setItems] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  // Phase 10B — quiz results (PAR role shows children's quiz results)
  const [quizResults, setQuizResults] = useState<QuizAttemptResult[]>([]);
  const [tab, setTab] = useState<'assignments' | 'quizzes'>('assignments');

  const fetchResults = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;

      const resp = await api.list<Result>('/results', params);
      if (cursor) {
        setItems((prev) => [...prev, ...resp.data]);
      } else {
        setItems(resp.data);
      }
      setNextCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  // Phase 10B — fetch quiz results
  const fetchQuizResults = useCallback(async () => {
    try {
      const resp = await api.list<QuizAttemptResult>('/results/quizzes');
      setQuizResults(resp.data);
    } catch {
      // quiz results endpoint may not exist yet — gracefully ignore
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchResults(), fetchQuizResults()]).finally(() => setLoading(false));
  }, [fetchResults, fetchQuizResults]);

  async function handleLoadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchResults(nextCursor);
    setLoadingMore(false);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('results.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchResults()} />

      {/* Phase 10B — Tab switcher for assignments vs quizzes */}
      {quizResults.length > 0 && (
        <div className="filters-bar" style={{ marginBottom: 16 }}>
          <button
            className={`btn ${tab === 'assignments' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTab('assignments')}
            style={{ marginRight: 8 }}
          >
            {t('results.tabAssignments')}
          </button>
          <button
            className={`btn ${tab === 'quizzes' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTab('quizzes')}
          >
            {t('results.tabQuizzes')}
          </button>
        </div>
      )}

      {/* Quiz results tab */}
      {tab === 'quizzes' && quizResults.length > 0 && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('results.quiz')}</th>
                <th>{t('results.attempt')}</th>
                <th>{t('results.score')}</th>
                <th>{t('results.status')}</th>
                <th>{t('results.completedAt')}</th>
              </tr>
            </thead>
            <tbody>
              {quizResults.map((qr) => {
                const pct = qr.max_score && qr.score !== null
                  ? Math.round((qr.score / qr.max_score) * 100)
                  : null;
                return (
                  <tr key={qr.id}>
                    <td style={{ fontWeight: 600 }}>{qr.quiz_title || qr.quiz_id.slice(0, 8)}</td>
                    <td>#{qr.attempt_no}</td>
                    <td>
                      {qr.score !== null && qr.max_score !== null
                        ? `${qr.score}/${qr.max_score}`
                        : '—'}
                      {pct !== null && <span style={{ color: 'var(--color-text-secondary)', marginLeft: 4 }}>({pct}%)</span>}
                    </td>
                    <td>
                      <span className={`status-badge status-${qr.status}`}>{qr.status}</span>
                    </td>
                    <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {qr.completed_at ? formatDate(qr.completed_at, i18n.language) : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Assignment results tab */}
      {tab === 'assignments' && items.length === 0 ? (
        <EmptyState message={t('results.empty')} icon="📊" />
      ) : tab === 'assignments' ? (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('results.assignment')}</th>
                  <th>{t('results.course')}</th>
                  <th>{t('results.score')}</th>
                  <th>{t('results.status')}</th>
                  <th>{t('results.dueAt')}</th>
                  <th>{t('results.feedback')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.assignment_id}>
                    <td>{r.assignment_title}</td>
                    <td>{r.course_title}</td>
                    <td>
                      {r.score !== null && r.out_of !== null
                        ? `${r.score}/${r.out_of}`
                        : '-'}
                      {r.letter_grade && (
                        <span className="letter-grade"> ({r.letter_grade})</span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge status-${r.submission_status}`}>
                        {r.submission_status}
                      </span>
                    </td>
                    <td>{formatDate(r.due_at, i18n.language)}</td>
                    <td>{r.feedback || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
