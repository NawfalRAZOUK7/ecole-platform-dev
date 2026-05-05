import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { ApiClientError } from '@/services/api/client';
import { useSignedUrl } from '@/shared/hooks/useSignedUrl';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { ContentProgressStatus } from './content.service';
import { normalizeContentType } from './content-types';
import { useContentDetail, useUpdateContentProgress } from './useContent';

type ContentSource =
  | { kind: 'external'; url: string }
  | { kind: 'backend'; path: string }
  | { kind: 'missing' };

function isBackendPath(value: string) {
  if (value.startsWith('/')) {
    return true;
  }

  if (/^https?:\/\//i.test(value)) {
    const url = new URL(value, window.location.origin);
    return url.origin === window.location.origin && url.pathname.startsWith('/api/v1/');
  }

  return false;
}

function resolveContentSource(content: {
  body_url?: string | null;
  embed_url?: string | null;
  external_url?: string | null;
  assets?: Array<{ id?: string | null; download_url?: string | null; url?: string | null }> | null;
  id?: string | null;
}): ContentSource {
  if (content.embed_url) return { kind: 'external', url: content.embed_url };
  if (content.external_url) return { kind: 'external', url: content.external_url };

  if (content.body_url) {
    if (isBackendPath(content.body_url)) {
      return { kind: 'backend', path: content.body_url };
    }

    if (/^https?:\/\//i.test(content.body_url)) {
      return { kind: 'external', url: content.body_url };
    }
  }

  const assetCandidate = content.assets?.[0]?.download_url || content.assets?.[0]?.url;
  if (assetCandidate && isBackendPath(assetCandidate)) {
    return { kind: 'backend', path: assetCandidate };
  }

  const assetId = content.assets?.[0]?.id;
  if (content.id && assetId) {
    return { kind: 'backend', path: `/content-items/${content.id}/assets/${assetId}` };
  }

  if (content.id) {
    return { kind: 'backend', path: `/content-items/${content.id}/stream` };
  }

  return { kind: 'missing' };
}

export function ContentPlayerPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const detailQuery = useContentDetail(id);
  const updateProgressMutation = useUpdateContentProgress();
  const [autoMarkedStarted, setAutoMarkedStarted] = useState(false);
  const contentSource = resolveContentSource(detailQuery.data ?? {});
  const signedContent = useSignedUrl(contentSource.kind === 'backend' ? contentSource.path : null);
  const contentUrl =
    contentSource.kind === 'external'
      ? contentSource.url
      : contentSource.kind === 'backend'
        ? signedContent.url
        : null;
  const contentType = normalizeContentType(detailQuery.data?.content_type);
  const signedUrlError = contentSource.kind === 'backend' ? signedContent.error : null;

  useEffect(() => {
    if (
      !id ||
      !detailQuery.data ||
      autoMarkedStarted ||
      detailQuery.data.progress?.status === 'in_progress' ||
      detailQuery.data.progress?.status === 'completed'
    ) {
      return;
    }

    void updateProgressMutation
      .mutateAsync({
        contentId: id,
        status: 'in_progress',
      })
      .then(() => {
        setAutoMarkedStarted(true);
      })
      .catch(() => null);
  }, [autoMarkedStarted, detailQuery.data, id, updateProgressMutation]);

  async function handleProgressChange(status: ContentProgressStatus) {
    if (!id) {
      return;
    }

    await updateProgressMutation.mutateAsync({
      contentId: id,
      status,
    });
  }

  if (detailQuery.isLoading) {
    return <LoadingState />;
  }

  if (detailQuery.error instanceof ApiClientError && detailQuery.error.status === 404) {
    return <EmptyState message={t('content.notAvailable')} icon="📭" />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate(`/content/${id}`)}
          >
            {t('content.backToDetail')}
          </button>
          <h1 className="page-title">{detailQuery.data?.title ?? t('content.openPlayer')}</h1>
          <p className="page-subtitle">{t('content.playerSubtitle')}</p>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => void handleProgressChange('in_progress')}
          >
            {t('content.markInProgress')}
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => void handleProgressChange('completed')}
          >
            {t('content.markCompleted')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={toBannerError(
          detailQuery.error ?? signedUrlError ?? updateProgressMutation.error,
          t('app.error'),
        )}
        onRetry={() =>
          void Promise.all([
            detailQuery.refetch(),
            contentSource.kind === 'backend' ? signedContent.refresh() : Promise.resolve(),
          ])
        }
      />

      <div className="card" style={{ padding: 20 }}>
        {contentType === 'video' && contentUrl ? (
          <video
            controls
            title={detailQuery.data?.title || 'content-player'}
            src={contentUrl}
            style={{ width: '100%', maxHeight: 640, borderRadius: 12 }}
            onError={() => void signedContent.refresh()}
          />
        ) : null}

        {contentType === 'audio' && contentUrl ? (
          <audio
            controls
            src={contentUrl}
            style={{ width: '100%' }}
            onError={() => void signedContent.refresh()}
          />
        ) : null}

        {contentType === 'document' && contentUrl ? (
          <iframe
            title={detailQuery.data?.title || 'content-document'}
            src={contentUrl}
            style={{ width: '100%', minHeight: 640, border: 'none', borderRadius: 12 }}
            onError={() => void signedContent.refresh()}
          />
        ) : null}

        {(contentType === 'story' || contentType === 'coloring_book') && contentUrl ? (
          <iframe
            title={detailQuery.data?.title || 'content-preview'}
            src={contentUrl}
            style={{ width: '100%', minHeight: 640, border: 'none', borderRadius: 12 }}
            onError={() => void signedContent.refresh()}
          />
        ) : null}

        {contentType === 'quiz' ? (
          <div style={{ textAlign: 'center', padding: '48px 24px' }}>
            <p>{t('content.quizLaunchHint')}</p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => navigate('/student/quizzes')}
            >
              {t('content.launchQuiz')}
            </button>
          </div>
        ) : null}

        {contentType === 'link' && contentUrl ? (
          <div style={{ textAlign: 'center', padding: '48px 24px' }}>
            <p>{t('content.externalLinkHint')}</p>
            <a
              href={contentUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
            >
              {t('content.openExternal')}
            </a>
          </div>
        ) : null}

        {contentSource.kind === 'backend' && signedContent.isLoading ? <LoadingState /> : null}

        {!contentUrl && contentType !== 'quiz' && !signedContent.isLoading ? (
          <EmptyState message={t('content.playerUnavailable')} icon="🧩" />
        ) : null}
      </div>
    </div>
  );
}
