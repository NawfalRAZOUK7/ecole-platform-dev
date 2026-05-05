import { useEffect, useMemo, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSignedUrl } from '@/shared/hooks/useSignedUrl';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { PlatformBridgeCard } from '@/shared/ui/PlatformBridgeCard';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { ContentStoryPage } from '@/features/content/content.service';
import {
  useContentDetail,
  useContentStoryPages,
  useUpdateContentProgress,
} from '@/features/content/useContent';

function isImageAsset(asset: ContentStoryPage) {
  return (
    asset.page_number !== null &&
    (asset.mime_type?.startsWith('image/') ||
      ['page_image', 'illustration', 'coloring_page', 'cover'].includes(asset.asset_type ?? ''))
  );
}

function getAssetPath(contentId: string, assetId: string) {
  return `/content-items/${encodeURIComponent(contentId)}/assets/${encodeURIComponent(assetId)}`;
}

function SignedColoringImage({
  contentId,
  assetId,
  alt,
}: {
  contentId: string;
  assetId: string;
  alt: string;
}) {
  const signedAsset = useSignedUrl(getAssetPath(contentId, assetId));

  if (signedAsset.isLoading) {
    return <LoadingState />;
  }

  if (!signedAsset.url) {
    return <EmptyState message={alt} icon="🎨" />;
  }

  return (
    <img
      src={signedAsset.url}
      alt={alt}
      style={{ width: '100%', display: 'block', objectFit: 'contain' }}
      onError={() => void signedAsset.refresh()}
    />
  );
}

export function ColoringViewerPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const detailQuery = useContentDetail(id);
  const pagesQuery = useContentStoryPages(id);
  const updateProgressMutation = useUpdateContentProgress();
  const progressMarkedRef = useRef(false);

  const pages = useMemo(
    () =>
      (pagesQuery.data ?? [])
        .filter(isImageAsset)
        .sort((left, right) => (left.page_number ?? 0) - (right.page_number ?? 0)),
    [pagesQuery.data],
  );

  useEffect(() => {
    progressMarkedRef.current = false;
  }, [id]);

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
          {detailQuery.data?.title ?? t('studentContent.coloringViewerTitle')}
        </h1>
        <p className="page-subtitle">{t('studentContent.coloringViewerSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          detailQuery.error ?? pagesQuery.error ?? updateProgressMutation.error,
          t('app.error'),
        )}
        onRetry={() => void Promise.all([detailQuery.refetch(), pagesQuery.refetch()])}
      />

      <PlatformBridgeCard
        targetPlatform="mobile"
        title={t('bridge.coloringTitle', { defaultValue: 'تلوين تفاعلي' })}
        description={t('bridge.coloringDescription', {
          defaultValue:
            'هذا النشاط مصمم للأجهزة اللوحية — استخدم التطبيق لتجربة تلوين تفاعلية بلمسة إصبعك. يمكنك هنا معاينة صفحات التلوين.',
        })}
        icon="🎨"
      />

      {pages.length === 0 ? (
        <EmptyState message={t('studentContent.noColoringPages')} icon="🎨" />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 16,
          }}
        >
          {pages.map((page) => (
            <article key={page.id} className="card" style={{ padding: 16 }}>
              <div style={{ fontWeight: 600, marginBottom: 12 }}>
                {t('studentContent.coloringPageLabel', {
                  page: page.page_number ?? 1,
                })}
              </div>
              <div
                style={{
                  borderRadius: 12,
                  overflow: 'hidden',
                  background: 'var(--kids-canvas-bg)',
                  border: '1px solid var(--kids-color-picker-border)',
                }}
              >
                <SignedColoringImage
                  contentId={id}
                  assetId={page.id}
                  alt={t('studentContent.coloringPageLabel', {
                    page: page.page_number ?? 1,
                  })}
                />
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
