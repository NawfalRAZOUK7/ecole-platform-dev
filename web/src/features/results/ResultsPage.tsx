/**
 * Results page — student/parent results listing.
 *
 * Reference: S-081 — Results page
 * Calls GET /results with cursor pagination. STD and PAR roles.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
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

export function ResultsPage() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

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

  useEffect(() => {
    setLoading(true);
    fetchResults().finally(() => setLoading(false));
  }, [fetchResults]);

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

      {items.length === 0 ? (
        <EmptyState message={t('results.empty')} icon="📊" />
      ) : (
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
      )}
    </div>
  );
}
