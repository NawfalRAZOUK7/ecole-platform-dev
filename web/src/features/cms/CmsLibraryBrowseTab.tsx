import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import type { ContentItem } from '@/features/teacher/teacher.service';
import { useTeacherClasses } from '@/features/teacher/useTeacher';
import { AssignContentModal } from '@/features/teacher/AssignContentModal';
import { ContentCard } from '@/features/teacher/ContentCard';
import { ContentFilters } from '@/features/teacher/ContentFilters';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import {
  useCmsAssignLibraryContent,
  useCmsLibraryContent,
  useCmsLibrarySubmissions,
  useCmsSubmitLibraryContentForReview,
} from './useCms';
import type { CmsLibraryItem, CmsLibrarySubmission } from './cms.service';

const REVIEW_STATUSES = ['PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED'] as const;

export function CmsLibraryBrowseTab() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canAssign = user?.role !== 'CONTENT_MGR';
  const [filterType, setFilterType] = useState('');
  const [filterSubject, setFilterSubject] = useState('');
  const [filterLevel, setFilterLevel] = useState('');
  const [filterOrigin, setFilterOrigin] = useState('');
  const [submissionStatus, setSubmissionStatus] = useState('');
  const [assignItem, setAssignItem] = useState<ContentItem | null>(null);
  const [assignClassId, setAssignClassId] = useState('');
  const [assignNotes, setAssignNotes] = useState('');

  const libraryQuery = useCmsLibraryContent({
    content_type: filterType || undefined,
    subject: filterSubject || undefined,
    level_band: filterLevel || undefined,
    origin: filterOrigin || undefined,
  });
  const submissionsQuery = useCmsLibrarySubmissions({
    status: submissionStatus || undefined,
  });
  const classesQuery = useTeacherClasses(canAssign);
  const assignMutation = useCmsAssignLibraryContent();
  const reviewMutation = useCmsSubmitLibraryContentForReview();

  const items: CmsLibraryItem[] = useMemo(
    () => libraryQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [libraryQuery.data],
  );
  const submissions: CmsLibrarySubmission[] = useMemo(
    () => submissionsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [submissionsQuery.data],
  );
  const classes = classesQuery.data ?? [];
  const error =
    libraryQuery.error ??
    submissionsQuery.error ??
    (canAssign ? classesQuery.error : null) ??
    assignMutation.error ??
    reviewMutation.error;

  if (
    (libraryQuery.isLoading && !libraryQuery.data) ||
    (canAssign && classesQuery.isLoading) ||
    (submissionsQuery.isLoading && !submissionsQuery.data)
  ) {
    return <LoadingState />;
  }

  async function handleAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!assignItem || !assignClassId) {
      return;
    }

    await assignMutation.mutateAsync({
      content_item_id: assignItem.id,
      class_id: assignClassId,
      notes: assignNotes.trim() || null,
    });
    setAssignItem(null);
    setAssignClassId('');
    setAssignNotes('');
  }

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      <ErrorBanner
        error={error instanceof Error ? error.message : null}
        onRetry={
          error
            ? () =>
                void Promise.all([
                  libraryQuery.refetch(),
                  submissionsQuery.refetch(),
                  ...(canAssign ? [classesQuery.refetch()] : []),
                ])
            : undefined
        }
      />

      <div>
        <ContentFilters
          filterLevel={filterLevel}
          filterOrigin={filterOrigin}
          filterSubject={filterSubject}
          filterType={filterType}
          onChangeLevel={setFilterLevel}
          onChangeOrigin={setFilterOrigin}
          onChangeSubject={setFilterSubject}
          onChangeType={setFilterType}
        />

        {items.length === 0 ? (
          <EmptyState message={t('cms.library.empty')} />
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: 16,
            }}
          >
            {items.map((item) => (
              <ContentCard
                key={item.id}
                item={item}
                reviewPending={reviewMutation.isPending}
                onAssign={
                  canAssign
                    ? (content) => {
                        setAssignItem(content);
                        setAssignClassId('');
                        setAssignNotes('');
                      }
                    : undefined
                }
                onSubmitForReview={(contentId) => void reviewMutation.mutateAsync(contentId)}
              />
            ))}
          </div>
        )}

        {libraryQuery.hasNextPage ? (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => void libraryQuery.fetchNextPage()}
              disabled={libraryQuery.isFetchingNextPage}
            >
              {libraryQuery.isFetchingNextPage ? t('app.loading') : t('teacherContent.loadMore')}
            </button>
          </div>
        ) : null}
      </div>

      <section className="card settings-card">
        <div className="settings-card__header">
          <h3>{t('cms.library.submissionsTitle')}</h3>
          <p>{t('cms.library.submissionsSubtitle')}</p>
        </div>
        <div className="filters-bar" style={{ marginBottom: 16 }}>
          <select
            className="filter-select"
            value={submissionStatus}
            onChange={(event) => setSubmissionStatus(event.target.value)}
          >
            <option value="">{t('teacherContent.allStatuses')}</option>
            {REVIEW_STATUSES.map((status) => (
              <option key={status} value={status}>
                {t(`cms.reviewStatuses.${status}`)}
              </option>
            ))}
          </select>
        </div>

        {submissions.length === 0 ? (
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
                {submissions.map((submission) => (
                  <tr key={submission.id}>
                    <td>{submission.content_title}</td>
                    <td>{t(`cms.reviewStatuses.${submission.status}`, submission.status)}</td>
                    <td>
                      {submission.submitted_at
                        ? new Date(submission.submitted_at).toLocaleDateString()
                        : '—'}
                    </td>
                    <td>{submission.review_notes || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {canAssign && (
        <AssignContentModal
          assignClassId={assignClassId}
          assignItem={assignItem}
          assignNotes={assignNotes}
          classes={classes}
          isPending={assignMutation.isPending}
          onChangeClassId={setAssignClassId}
          onChangeNotes={setAssignNotes}
          onClose={() => setAssignItem(null)}
          onSubmit={(event) => void handleAssign(event)}
        />
      )}
    </div>
  );
}
