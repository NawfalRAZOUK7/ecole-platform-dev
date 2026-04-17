import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { ContentStoryPage } from '@/features/content/content.service';
import {
  useCompleteContentItem,
  useContentDetail,
  useContentStoryPages,
  useUpdateContentProgress,
} from '@/features/content/useContent';

interface StorySlide {
  pageNumber: number;
  imageAsset: ContentStoryPage | null;
  audioAsset: ContentStoryPage | null;
  narrationText: string | null;
  hasActivity: boolean;
}

function isImageAsset(asset: ContentStoryPage) {
  return (
    asset.mime_type?.startsWith('image/') ||
    ['page_image', 'illustration', 'coloring_page', 'cover'].includes(asset.asset_type ?? '')
  );
}

function isAudioAsset(asset: ContentStoryPage) {
  return asset.mime_type?.startsWith('audio/') || asset.asset_type === 'audio_narration';
}

function buildSlides(pages: ContentStoryPage[]): StorySlide[] {
  const slides = new Map<number, StorySlide>();

  for (const asset of pages) {
    if (asset.page_number === null) {
      continue;
    }

    const existing = slides.get(asset.page_number) ?? {
      pageNumber: asset.page_number,
      imageAsset: null,
      audioAsset: null,
      narrationText: asset.narration_text,
      hasActivity: asset.has_activity,
    };

    if (!existing.narrationText && asset.narration_text) {
      existing.narrationText = asset.narration_text;
    }

    existing.hasActivity = existing.hasActivity || asset.has_activity;

    if (isImageAsset(asset) && !existing.imageAsset) {
      existing.imageAsset = asset;
    }

    if (isAudioAsset(asset) && !existing.audioAsset) {
      existing.audioAsset = asset;
    }

    slides.set(asset.page_number, existing);
  }

  return [...slides.values()].sort((left, right) => left.pageNumber - right.pageNumber);
}

function getAssetUrl(contentId: string, assetId: string) {
  return `/api/v1/content-items/${encodeURIComponent(contentId)}/assets/${encodeURIComponent(assetId)}`;
}

export function StoryViewerPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const detailQuery = useContentDetail(id);
  const pagesQuery = useContentStoryPages(id);
  const updateProgressMutation = useUpdateContentProgress();
  const completeMutation = useCompleteContentItem();
  const startedAtRef = useRef(Date.now());
  const progressMarkedRef = useRef(false);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [completionMessage, setCompletionMessage] = useState<string | null>(null);

  const slides = useMemo(() => buildSlides(pagesQuery.data ?? []), [pagesQuery.data]);
  const currentSlide = slides[currentPageIndex] ?? null;
  const isCompleted =
    detailQuery.data?.progress?.status === 'completed' ||
    completeMutation.data?.progress.status === 'completed';

  useEffect(() => {
    startedAtRef.current = Date.now();
    progressMarkedRef.current = false;
    setCurrentPageIndex(0);
    setCompletionMessage(null);
  }, [id]);

  useEffect(() => {
    if (slides.length === 0) {
      return;
    }

    setCurrentPageIndex((current) => Math.min(current, slides.length - 1));
  }, [slides.length]);

  useEffect(() => {
    if (
      !id ||
      !detailQuery.data ||
      progressMarkedRef.current ||
      detailQuery.data.progress?.status === 'in_progress' ||
      detailQuery.data.progress?.status === 'completed'
    ) {
      return;
    }

    progressMarkedRef.current = true;
    void updateProgressMutation.mutateAsync({ contentId: id, status: 'in_progress' }).catch(() => {
      progressMarkedRef.current = false;
    });
  }, [detailQuery.data, id, updateProgressMutation]);

  async function handleCompleteStory() {
    if (!id) {
      return;
    }

    const timeSpentSeconds = Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000));
    const result = await completeMutation.mutateAsync({
      contentId: id,
      timeSpentSeconds,
    });

    setCompletionMessage(
      t('studentContent.storyCompletionSuccess', {
        stars: result.reward.stars,
        xp: result.reward.xp,
        badges: result.newly_earned_badges.length,
      }),
    );
  }

  if (detailQuery.isLoading || pagesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => navigate('/student/content')}
        >
          {t('studentContent.backToContent')}
        </button>
        <h1 className="page-title" style={{ marginTop: 12 }}>
          {detailQuery.data?.title ?? t('studentContent.storyViewerTitle')}
        </h1>
        <p className="page-subtitle">{t('studentContent.storyViewerSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          detailQuery.error ??
            pagesQuery.error ??
            updateProgressMutation.error ??
            completeMutation.error,
          t('app.error'),
        )}
        onRetry={() => void Promise.all([detailQuery.refetch(), pagesQuery.refetch()])}
      />

      {completionMessage ? (
        <div
          className="card"
          style={{
            marginBottom: 16,
            padding: 16,
            background: 'var(--color-surface-success)',
            border: '1px solid var(--color-success)',
          }}
        >
          <strong style={{ color: 'var(--color-success)' }}>{completionMessage}</strong>
        </div>
      ) : null}

      {!currentSlide ? (
        <EmptyState message={t('studentContent.noPages')} icon="📖" />
      ) : (
        <div
          className="card"
          style={{
            padding: 20,
            background: 'var(--kids-story-bg)',
            color: 'var(--kids-story-text)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: 12,
              alignItems: 'center',
              flexWrap: 'wrap',
              marginBottom: 16,
            }}
          >
            <div>
              <div style={{ fontWeight: 600 }}>
                {t('studentContent.pageIndicator', {
                  current: currentPageIndex + 1,
                  total: slides.length,
                })}
              </div>
              {isCompleted ? (
                <div style={{ color: 'var(--color-success)', fontSize: 13 }}>
                  {t('content.progress.completed')}
                </div>
              ) : null}
            </div>
            {currentSlide.hasActivity ? (
              <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
                {t('studentContent.storyActivityHint')}
              </div>
            ) : null}
          </div>

          <div
            style={{
              minHeight: 360,
              borderRadius: 16,
              background:
                detailQuery.data?.theme_color && detailQuery.data.theme_color.startsWith('#')
                  ? `${detailQuery.data.theme_color}22`
                  : 'var(--color-bg-secondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              marginBottom: 16,
            }}
          >
            {currentSlide.imageAsset ? (
              <img
                src={getAssetUrl(id, currentSlide.imageAsset.id)}
                alt={`${detailQuery.data?.title ?? t('studentContent.storyViewerTitle')} ${currentSlide.pageNumber}`}
                style={{ width: '100%', maxHeight: 640, objectFit: 'contain' }}
              />
            ) : (
              <EmptyState message={t('studentContent.noPages')} icon="🖼️" />
            )}
          </div>

          {currentSlide.audioAsset ? (
            <div style={{ marginBottom: 16 }}>
              <audio controls style={{ width: '100%' }}>
                <source src={getAssetUrl(id, currentSlide.audioAsset.id)} />
                {t('studentContent.audioUnsupported')}
              </audio>
            </div>
          ) : null}

          {currentSlide.narrationText ? (
            <div
              className="card"
              style={{
                padding: 16,
                marginBottom: 16,
                borderLeft: '4px solid var(--kids-story-highlight)',
                background: 'var(--kids-story-bg)',
              }}
            >
              <strong style={{ color: 'var(--kids-story-text)' }}>
                {t('studentContent.narration')}
              </strong>
              <p style={{ margin: '8px 0 0', lineHeight: 1.6, color: 'var(--kids-story-text)' }}>
                {currentSlide.narrationText}
              </p>
            </div>
          ) : null}

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: 12,
              alignItems: 'center',
              flexWrap: 'wrap',
            }}
          >
            <button
              type="button"
              className="btn btn-secondary"
              style={{ background: 'var(--kids-story-page-turn)', color: '#fff', border: 'none' }}
              onClick={() => setCurrentPageIndex((current) => Math.max(0, current - 1))}
              disabled={currentPageIndex === 0}
            >
              {t('studentContent.prevPage')}
            </button>

            <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {t('studentContent.pageIndicator', {
                current: currentPageIndex + 1,
                total: slides.length,
              })}
            </div>

            {currentPageIndex < slides.length - 1 ? (
              <button
                type="button"
                className="btn btn-primary"
                style={{ background: 'var(--kids-story-page-turn)', border: 'none' }}
                onClick={() =>
                  setCurrentPageIndex((current) => Math.min(slides.length - 1, current + 1))
                }
              >
                {t('studentContent.nextPage')}
              </button>
            ) : (
              <button
                type="button"
                className="btn btn-primary"
                disabled={completeMutation.isPending || isCompleted}
                onClick={() => void handleCompleteStory()}
              >
                {isCompleted
                  ? t('content.progress.completed')
                  : completeMutation.isPending
                    ? t('app.loading')
                    : t('studentContent.finishStory')}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
