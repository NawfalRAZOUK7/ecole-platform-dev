import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { REVIEW_STATUS_OPTIONS } from './content-library.types';
import type { ContentSubmissionItem } from './teacher.service';
import { useTeacherContentSubmissions } from './useTeacher';

export function ContentSubmissionsTable() {
  const { t } = useTranslation();
  const [filterStatus, setFilterStatus] = useState('');
  const submissionsQuery = useTeacherContentSubmissions({ status: filterStatus || undefined });
  const items: ContentSubmissionItem[] = useMemo(() => submissionsQuery.data?.pages.flatMap((page) => page.data) ?? [], [submissionsQuery.data]);
  const dismissibleError = useDismissibleError(useMemo(() => toBannerError(submissionsQuery.error, t('app.error')), [submissionsQuery.error, t]));

  if (submissionsQuery.isLoading && !submissionsQuery.data) {
    return <LoadingState />;
  }

  const statusColors: Record<string, string> = {
    PENDING: 'var(--color-warning)',
    UNDER_REVIEW: 'var(--color-info)',
    APPROVED: 'var(--color-success)',
    REJECTED: 'var(--color-error)',
  };

  return (
    <>
      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} onRetry={() => void submissionsQuery.refetch()} />
      <div className="filters-bar" style={{ marginBottom: 16 }}>
        <select className="filter-select" value={filterStatus} onChange={(event) => setFilterStatus(event.target.value)}>
          <option value="">{t('teacherContent.allStatuses')}</option>
          {REVIEW_STATUS_OPTIONS.map((status) => <option key={status} value={status}>{t(`cms.reviewStatuses.${status}`)}</option>)}
        </select>
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('teacherContent.noSubmissions')} />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('teacherContent.contentTitle')}</th>
                <th>{t('teacherContent.submissionStatus')}</th>
                <th>{t('teacherContent.submittedAt')}</th>
                <th>{t('teacherContent.feedback')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((submission) => (
                <tr key={submission.id}>
                  <td style={{ fontWeight: 600 }}>{submission.content_title}</td>
                  <td><span style={{ color: statusColors[submission.status] || 'inherit', fontWeight: 600, fontSize: 13 }}>{t(`cms.reviewStatuses.${submission.status}`, submission.status)}</span></td>
                  <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{submission.submitted_at ? new Date(submission.submitted_at).toLocaleDateString() : '—'}</td>
                  <td style={{ fontSize: 13 }}>{submission.review_notes || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {submissionsQuery.hasNextPage && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={() => void submissionsQuery.fetchNextPage()} disabled={submissionsQuery.isFetchingNextPage}>
            {submissionsQuery.isFetchingNextPage ? t('app.loading') : t('teacherContent.loadMore')}
          </button>
        </div>
      )}
    </>
  );
}
