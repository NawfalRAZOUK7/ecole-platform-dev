/**
 * Student Content View — view assigned content (video/audio/PDF players), progress tracking.
 *
 * Phase 10B — Student views class content with HTML5 players.
 * API: GET /classes/{classId}/content, GET /content-items/{id},
 *      GET /content-items/{id}/assets/{assetId}, POST /content-items/{id}/progress
 */

import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { getContentTypeIcon, normalizeContentType } from '@/features/content/content-types';
import { studentService, type ClassContentItem, type StudentClassOption } from './student.service';
import { useStudentClassContent, useStudentClasses, useUpdateContentProgress } from './useStudent';

export function StudentContentPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [selectedClassId, setSelectedClassId] = useState('');
  const [viewingItem, setViewingItem] = useState<ClassContentItem | null>(null);
  const [progressMap, setProgressMap] = useState<Record<string, string>>({});
  const classesQuery = useStudentClasses();
  const contentQuery = useStudentClassContent(selectedClassId);
  const updateProgressMutation = useUpdateContentProgress();
  const classes: StudentClassOption[] = classesQuery.data ?? [];
  const contentItems: ClassContentItem[] = contentQuery.data ?? [];
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          classesQuery.error ?? contentQuery.error ?? updateProgressMutation.error,
          t('app.error'),
        ),
      [classesQuery.error, contentQuery.error, t, updateProgressMutation.error],
    ),
  );

  useEffect(() => {
    if (!selectedClassId && classes.length > 0) {
      setSelectedClassId(classes[0].class_id);
    }
  }, [classes, selectedClassId]);

  async function handleUpdateProgress(contentItemId: string, status: string) {
    await updateProgressMutation.mutateAsync({
      contentItemId,
      status,
    });
    setProgressMap((current) => ({ ...current, [contentItemId]: status }));
  }

  function markStarted(contentItemId: string) {
    if (progressMap[contentItemId]) {
      return;
    }

    void handleUpdateProgress(contentItemId, 'in_progress').catch(() => null);
  }

  function handleOpenItem(item: ClassContentItem) {
    const normalizedType = normalizeContentType(item.content_type);

    if (normalizedType === 'story') {
      markStarted(item.content_item_id);
      navigate(`/student/content/${item.content_item_id}/read`);
      return;
    }

    if (normalizedType === 'coloring_book') {
      markStarted(item.content_item_id);
      navigate(`/student/content/${item.content_item_id}/color`);
      return;
    }

    setViewingItem(item);
    markStarted(item.content_item_id);
  }

  if (classesQuery.isLoading || (selectedClassId && contentQuery.isLoading)) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('studentContent.title')}</h1>
      <p className="page-subtitle">{t('studentContent.subtitle')}</p>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() =>
          void Promise.all([
            classesQuery.refetch(),
            selectedClassId ? contentQuery.refetch() : Promise.resolve(),
          ])
        }
      />

      {classes.length > 1 && (
        <div className="filters-bar" style={{ marginBottom: 16 }}>
          <select
            className="filter-select"
            value={selectedClassId}
            onChange={(event) => setSelectedClassId(event.target.value)}
          >
            {classes.map((classItem) => (
              <option key={classItem.class_id} value={classItem.class_id}>
                {classItem.class_name}
              </option>
            ))}
          </select>
        </div>
      )}

      {viewingItem ? (
        <ContentPlayer
          item={viewingItem}
          onBack={() => setViewingItem(null)}
          onProgressUpdate={(status) =>
            void handleUpdateProgress(viewingItem.content_item_id, status)
          }
          progress={progressMap[viewingItem.content_item_id]}
        />
      ) : contentItems.length === 0 ? (
        <EmptyState message={t('studentContent.emptyKids')} icon="📚" />
      ) : (
        <div className="kids-content-grid">
          {contentItems.map((item) => {
            const progress = progressMap[item.content_item_id];
            const normalizedType = normalizeContentType(item.content_type);
            const actionLabel =
              normalizedType === 'story'
                ? t('studentContent.readStory')
                : normalizedType === 'coloring_book'
                  ? t('studentContent.viewColoringBook')
                  : t('studentContent.open', 'Open');
            const progressPercent =
              progress === 'completed' ? 100 : progress === 'in_progress' ? 50 : 0;

            return (
              <div
                key={item.id}
                className="kids-content-card"
                onClick={() => handleOpenItem(item)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    handleOpenItem(item);
                  }
                }}
                role="button"
                tabIndex={0}
                aria-label={item.title}
              >
                <div className="kids-content-card__header">
                  <span className="kids-content-card__type-icon">
                    {getContentTypeIcon(item.content_type)}
                  </span>
                  <span
                    className={`kids-content-card__type-badge kids-content-card__type-badge--${normalizedType}`}
                  >
                    {item.content_type}
                  </span>
                </div>
                <div className="kids-content-card__body">
                  <h4 className="kids-content-card__title">{item.title}</h4>
                  {item.description && (
                    <p className="kids-content-card__desc">
                      {item.description.length > 80
                        ? `${item.description.slice(0, 80)}…`
                        : item.description}
                    </p>
                  )}
                  {progressPercent > 0 && (
                    <>
                      <div className="kids-content-card__progress-bar">
                        <div
                          className={`kids-content-card__progress-fill${progress === 'completed' ? ' kids-content-card__progress-fill--completed' : ''}`}
                          style={{ width: `${progressPercent}%` }}
                        />
                      </div>
                      <span
                        className={`kids-content-card__status kids-content-card__status--${progress}`}
                      >
                        {t(`content.progress.${progress}`, progress)}
                        {progress === 'completed' && ' ✓'}
                      </span>
                    </>
                  )}
                  <button
                    type="button"
                    className="kids-content-card__action"
                    onClick={(event) => {
                      event.stopPropagation();
                      handleOpenItem(item);
                    }}
                  >
                    {actionLabel}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ContentPlayer({
  item,
  onBack,
  onProgressUpdate,
  progress,
}: {
  item: ClassContentItem;
  onBack: () => void;
  onProgressUpdate: (status: string) => void;
  progress: string | undefined;
}) {
  const { t } = useTranslation();
  const streamUrl = studentService.buildContentStreamUrl(item.content_item_id);

  return (
    <div>
      <button className="btn btn-secondary" onClick={onBack} style={{ marginBottom: 16 }}>
        {t('app.back')}
      </button>

      <div className="card" style={{ padding: 20 }}>
        <h2 style={{ margin: '0 0 8px', fontSize: 18 }}>{item.title}</h2>
        {item.description && (
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {item.description}
          </p>
        )}

        <div
          style={{
            marginBottom: 16,
            background: 'color-mix(in srgb, var(--color-text) 92%, transparent)',
            borderRadius: 8,
            overflow: 'hidden',
            minHeight: 300,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {item.content_type === 'video' && (
            <video
              controls
              style={{ width: '100%', maxHeight: 500 }}
              onEnded={() => onProgressUpdate('completed')}
            >
              <source src={streamUrl} />
              {t('studentContent.videoUnsupported')}
            </video>
          )}

          {item.content_type === 'audio' && (
            <div style={{ padding: 40, width: '100%' }}>
              <audio
                controls
                style={{ width: '100%' }}
                onEnded={() => onProgressUpdate('completed')}
              >
                <source src={streamUrl} />
                {t('studentContent.audioUnsupported')}
              </audio>
            </div>
          )}

          {item.content_type === 'pdf' && (
            <iframe
              src={streamUrl}
              style={{ width: '100%', height: 600, border: 'none' }}
              title={item.title}
            />
          )}

          {item.content_type === 'interactive' && (
            <div style={{ color: 'var(--color-inverse-text)', padding: 40, textAlign: 'center' }}>
              <p>{t('studentContent.interactiveHint')}</p>
              <a
                href={streamUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                {t('studentContent.openInteractive')}
              </a>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
            {t('studentContent.progress')}:
          </span>
          {progress === 'completed' ? (
            <span style={{ fontSize: 13, color: 'var(--color-success)', fontWeight: 600 }}>
              {t('content.progress.completed')}
            </span>
          ) : (
            <button
              className="btn btn-primary"
              style={{ fontSize: 12, padding: '4px 12px' }}
              onClick={() => onProgressUpdate('completed')}
            >
              {t('studentContent.markComplete')}
            </button>
          )}
        </div>

        {item.teacher_notes && (
          <div
            style={{
              marginTop: 16,
              padding: 12,
              background: 'var(--color-bg)',
              borderRadius: 'var(--radius)',
              fontSize: 13,
            }}
          >
            <strong>{t('studentContent.teacherNotes')}:</strong> {item.teacher_notes}
          </div>
        )}
      </div>
    </div>
  );
}
