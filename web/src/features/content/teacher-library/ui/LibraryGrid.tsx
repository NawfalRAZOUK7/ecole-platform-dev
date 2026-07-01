import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useAssignableClasses,
  useAssignContent,
  useSubmitContentForReview,
  useTeacherContentLibrary,
} from '@/features/lms/teacher/model/useTeacher';
import { AssignContentModal } from './AssignContentModal';
import { ContentCard } from './ContentCard';
import { ContentFilters } from './ContentFilters';
import type { ClassOption, ContentItem } from '@/features/lms/teacher/api/teacher.api';

export function LibraryGrid() {
  const { t } = useTranslation();
  const [filterType, setFilterType] = useState('');
  const [filterSubject, setFilterSubject] = useState('');
  const [filterLevel, setFilterLevel] = useState('');
  const [filterOrigin, setFilterOrigin] = useState('');
  const [assignItem, setAssignItem] = useState<ContentItem | null>(null);
  const [assignClassId, setAssignClassId] = useState('');
  const [assignNotes, setAssignNotes] = useState('');

  const contentQuery = useTeacherContentLibrary({
    content_type: filterType || undefined,
    subject: filterSubject || undefined,
    level_band: filterLevel || undefined,
    origin: filterOrigin || undefined,
  });
  const classesQuery = useAssignableClasses();
  const assignMutation = useAssignContent();
  const reviewMutation = useSubmitContentForReview();
  const items: ContentItem[] = useMemo(
    () => contentQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [contentQuery.data],
  );
  const classes: ClassOption[] = classesQuery.data ?? [];
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          contentQuery.error ?? classesQuery.error ?? assignMutation.error ?? reviewMutation.error,
          t('app.error'),
        ),
      [assignMutation.error, classesQuery.error, contentQuery.error, reviewMutation.error, t],
    ),
  );

  async function handleAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!assignItem || !assignClassId) return;
    await assignMutation.mutateAsync({
      content_item_id: assignItem.id,
      class_id: assignClassId,
      notes: assignNotes.trim() || null,
    });
    setAssignItem(null);
    setAssignClassId('');
    setAssignNotes('');
  }

  async function handleSubmitForReview(contentId: string) {
    await reviewMutation.mutateAsync(contentId);
  }

  if ((contentQuery.isLoading && !contentQuery.data) || classesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <>
      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void contentQuery.refetch()}
      />
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
        <EmptyState message={t('teacherContent.empty')} />
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
              onAssign={(content) => {
                setAssignItem(content);
                setAssignClassId('');
                setAssignNotes('');
              }}
              onSubmitForReview={(contentId) => void handleSubmitForReview(contentId)}
            />
          ))}
        </div>
      )}

      {contentQuery.hasNextPage && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button
            className="btn btn-secondary"
            onClick={() => void contentQuery.fetchNextPage()}
            disabled={contentQuery.isFetchingNextPage}
          >
            {contentQuery.isFetchingNextPage ? t('app.loading') : t('teacherContent.loadMore')}
          </button>
        </div>
      )}

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
    </>
  );
}
