import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { ContentProgressStatus } from './content.service';
import { useContentDetail, useUpdateContentProgress } from './useContent';

function normalizeContentType(contentType: string | null | undefined) {
  const value = (contentType || '').toLowerCase();

  if (value === 'video') {
    return 'video';
  }
  if (['document', 'pdf', 'audio'].includes(value)) {
    return 'document';
  }
  if (value === 'quiz') {
    return 'quiz';
  }

  return 'link';
}

function resolveContentUrl(content: {
  body_url?: string | null;
  embed_url?: string | null;
  external_url?: string | null;
  assets?: Array<{ download_url?: string | null; url?: string | null }> | null;
}) {
  return (
    content.embed_url ||
    content.body_url ||
    content.external_url ||
    content.assets?.[0]?.download_url ||
    content.assets?.[0]?.url ||
    null
  );
}

export function ContentPlayerPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const detailQuery = useContentDetail(id);
  const updateProgressMutation = useUpdateContentProgress();
  const [autoMarkedStarted, setAutoMarkedStarted] = useState(false);
  const contentUrl = resolveContentUrl(detailQuery.data ?? {});
  const contentType = normalizeContentType(detailQuery.data?.content_type);

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

    void updateProgressMutation.mutateAsync({
      contentId: id,
      status: 'in_progress',
    }).then(() => {
      setAutoMarkedStarted(true);
    }).catch(() => null);
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

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <button type="button" className="btn btn-secondary" onClick={() => navigate(`/content/${id}`)}>
            {t('content.backToDetail')}
          </button>
          <h1 className="page-title">{detailQuery.data?.title ?? t('content.openPlayer')}</h1>
          <p className="page-subtitle">{t('content.playerSubtitle')}</p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-secondary" onClick={() => void handleProgressChange('in_progress')}>
            {t('content.markInProgress')}
          </button>
          <button type="button" className="btn btn-primary" onClick={() => void handleProgressChange('completed')}>
            {t('content.markCompleted')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={toBannerError(detailQuery.error ?? updateProgressMutation.error, t('app.error'))}
        onRetry={() => void detailQuery.refetch()}
      />

      <div className="card" style={{ padding: 20 }}>
        {contentType === 'video' && contentUrl ? (
          <iframe
            title={detailQuery.data?.title || 'content-player'}
            src={contentUrl}
            style={{ width: '100%', minHeight: 520, border: 'none', borderRadius: 12 }}
            allow="autoplay; encrypted-media; picture-in-picture"
            allowFullScreen
          />
        ) : null}

        {contentType === 'document' && contentUrl ? (
          <iframe
            title={detailQuery.data?.title || 'content-document'}
            src={contentUrl}
            style={{ width: '100%', minHeight: 640, border: 'none', borderRadius: 12 }}
          />
        ) : null}

        {contentType === 'quiz' ? (
          <div style={{ textAlign: 'center', padding: '48px 24px' }}>
            <p>{t('content.quizLaunchHint')}</p>
            <button type="button" className="btn btn-primary" onClick={() => navigate('/student/quizzes')}>
              {t('content.launchQuiz')}
            </button>
          </div>
        ) : null}

        {contentType === 'link' && contentUrl ? (
          <div style={{ textAlign: 'center', padding: '48px 24px' }}>
            <p>{t('content.externalLinkHint')}</p>
            <a href={contentUrl} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
              {t('content.openExternal')}
            </a>
          </div>
        ) : null}

        {!contentUrl && contentType !== 'quiz' ? (
          <EmptyState message={t('content.playerUnavailable')} icon="🧩" />
        ) : null}
      </div>
    </div>
  );
}
