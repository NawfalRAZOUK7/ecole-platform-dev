/**
 * Results page — student/parent results listing + quiz results.
 *
 * Reference: S-081 — Results page
 * Phase 10B — Parent quiz results alongside assignment grades.
 * Calls GET /results with cursor pagination. STD and PAR roles.
 */

import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import { useAssignmentResults, useQuizAttemptResults } from '../model/useResults';
import type { QuizAttemptResult, Result } from '../api/results.api';

export function ResultsPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [tab, setTab] = useState<'assignments' | 'quizzes'>('assignments');
  const assignmentsQuery = useAssignmentResults();
  const quizResultsQuery = useQuizAttemptResults();
  const items: Result[] = useMemo(
    () => assignmentsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [assignmentsQuery.data],
  );
  const quizResults: QuizAttemptResult[] = quizResultsQuery.data ?? [];
  const dismissibleError = useDismissibleError(
    toBannerError(assignmentsQuery.error ?? quizResultsQuery.error, t('app.error')),
  );

  if ((assignmentsQuery.isLoading && !assignmentsQuery.data) || quizResultsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('results.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void Promise.all([assignmentsQuery.refetch(), quizResultsQuery.refetch()])}
      />

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
                <th>{t('results.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {quizResults.map((result) => {
                const pct =
                  result.max_score && result.score !== null
                    ? Math.round((result.score / result.max_score) * 100)
                    : null;
                return (
                  <tr key={result.id}>
                    <td style={{ fontWeight: 600 }}>
                      {result.quiz_title || result.quiz_id.slice(0, 8)}
                    </td>
                    <td>#{result.attempt_no}</td>
                    <td>
                      {result.score !== null && result.max_score !== null
                        ? `${result.score}/${result.max_score}`
                        : '—'}
                      {pct !== null && (
                        <span style={{ color: 'var(--color-text-secondary)', marginLeft: 4 }}>
                          ({pct}%)
                        </span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge status-${result.status}`}>
                        {result.status}
                      </span>
                    </td>
                    <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {result.completed_at ? formatDate(result.completed_at, i18n.language) : '—'}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ fontSize: 12, padding: '4px 10px' }}
                        onClick={() => navigate(`/quizzes/attempts/${result.id}/results`)}
                      >
                        {t('results.viewDetails')}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

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
                {items.map((item) => (
                  <tr key={item.assignment_id}>
                    <td>{item.assignment_title}</td>
                    <td>{item.course_title}</td>
                    <td>
                      {item.score !== null && item.out_of !== null
                        ? `${item.score}/${item.out_of}`
                        : '-'}
                      {item.letter_grade && (
                        <span className="letter-grade"> ({item.letter_grade})</span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge status-${item.submission_status}`}>
                        {item.submission_status}
                      </span>
                    </td>
                    <td>{formatDate(item.due_at, i18n.language)}</td>
                    <td>{item.feedback || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {assignmentsQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={() => void assignmentsQuery.fetchNextPage()}
                disabled={assignmentsQuery.isFetchingNextPage}
              >
                {assignmentsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
