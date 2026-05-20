import { useEffect, useMemo, useState, type MouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { useAuth } from '@/app/providers/AuthContext';
import { useSignedUrl } from '@/shared/hooks/useSignedUrl';
import { Badge, DataTable, ErrorBanner, LoadingState, StatCard, Tabs } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { ContentAsset, ContentProgressStatus } from '../api/content.api';
import { normalizeContentType } from '../model/content-types';
import {
  useContentDetail,
  useToggleContentPublish,
  useUpdateContentOrdering,
  useUpdateContentProgress,
} from '../model/useContent';

type AssetRow = ContentAsset & Record<string, unknown>;
type AnalyticsRow = { metric: string; value: string } & Record<string, unknown>;

function AssetOpenButton({
  contentId,
  asset,
  label,
}: {
  contentId: string;
  asset: AssetRow;
  label: string;
}) {
  const signedAsset = useSignedUrl(
    contentId && asset.id ? `/content-items/${contentId}/assets/${asset.id}` : null,
  );

  async function handleClick(event: MouseEvent<HTMLAnchorElement>) {
    if (!signedAsset.url || signedAsset.isExpired) {
      event.preventDefault();
      const metadata = await signedAsset.refresh();
      if (metadata?.download_url) {
        window.open(metadata.download_url, '_blank', 'noopener,noreferrer');
      }
    }
  }

  if (!asset.id) {
    return <span>-</span>;
  }

  return (
    <a
      href={signedAsset.url ?? '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="btn btn-secondary btn-sm"
      aria-disabled={signedAsset.isFetching && !signedAsset.url}
      onClick={(event) => void handleClick(event)}
    >
      {signedAsset.isFetching && !signedAsset.url ? '...' : label}
    </a>
  );
}

function getProgressPercent(status: ContentProgressStatus | undefined) {
  if (status === 'completed') {
    return 100;
  }
  if (status === 'in_progress') {
    return 55;
  }

  return 0;
}

export function ContentDetailPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { id = '' } = useParams();
  const detailQuery = useContentDetail(id);
  const updateProgressMutation = useUpdateContentProgress();
  const togglePublishMutation = useToggleContentPublish();
  const updateOrderingMutation = useUpdateContentOrdering();
  const [sortOrder, setSortOrder] = useState('0');
  const progressStatus = (detailQuery.data?.progress?.status ||
    'not_started') as ContentProgressStatus;
  const progressPercent = getProgressPercent(progressStatus);
  const isManager = ['TCH', 'ADM', 'DIR', 'CONTENT_MGR'].includes(user?.role || '');

  useEffect(() => {
    setSortOrder(String(detailQuery.data?.sort_order ?? 0));
  }, [detailQuery.data?.sort_order]);

  const assetColumns: ColumnDef<AssetRow>[] = useMemo(
    () => [
      {
        key: 'name',
        header: 'content.assetName',
        render: (value, row) => String(value || row.mime_type || t('content.assetFallbackName')),
      },
      {
        key: 'mime_type',
        header: 'content.assetType',
        render: (value) => String(value || '-'),
      },
      {
        key: 'id',
        header: 'content.actions',
        sortable: false,
        render: (_value, row) =>
          id ? (
            <AssetOpenButton contentId={id} asset={row} label={t('content.openAsset')} />
          ) : (
            <span>-</span>
          ),
      },
    ],
    [id, t],
  );

  const analyticsRows = useMemo<AnalyticsRow[]>(() => {
    const analytics = detailQuery.data?.student_analytics;
    return [
      {
        metric: t('content.analytics.started'),
        value: String(analytics?.students_started ?? (progressStatus === 'not_started' ? 0 : 1)),
      },
      {
        metric: t('content.analytics.completed'),
        value: String(analytics?.students_completed ?? (progressStatus === 'completed' ? 1 : 0)),
      },
      {
        metric: t('content.analytics.completionRate'),
        value: `${Math.round(analytics?.completion_rate ?? progressPercent)}%`,
      },
      {
        metric: t('content.analytics.averageScore'),
        value:
          analytics?.average_score === null || analytics?.average_score === undefined
            ? '-'
            : `${Math.round(analytics.average_score * 10) / 10}`,
      },
      {
        metric: t('content.analytics.views'),
        value: String(analytics?.total_views ?? 0),
      },
    ];
  }, [detailQuery.data?.student_analytics, progressPercent, progressStatus, t]);

  const analyticsColumns: ColumnDef<AnalyticsRow>[] = useMemo(
    () => [
      { key: 'metric', header: 'content.metric' },
      { key: 'value', header: 'content.value' },
    ],
    [],
  );

  async function handleProgressChange(status: ContentProgressStatus) {
    if (!id) {
      return;
    }

    await updateProgressMutation.mutateAsync({ contentId: id, status });
  }

  async function handlePublishToggle() {
    if (!id) {
      return;
    }

    const nextStatus = detailQuery.data?.status === 'published' ? 'draft' : 'published';
    await togglePublishMutation.mutateAsync({ contentId: id, status: nextStatus });
  }

  async function handleSaveOrder() {
    if (!id) {
      return;
    }

    const nextSortOrder = Number(sortOrder);
    if (Number.isNaN(nextSortOrder)) {
      return;
    }

    await updateOrderingMutation.mutateAsync({ contentId: id, sortOrder: nextSortOrder });
  }

  if (detailQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/content')}>
            {t('content.backToList')}
          </button>
          <h1 className="page-title">{detailQuery.data?.title ?? t('content.title')}</h1>
          <p className="page-subtitle">{t('content.detailSubtitle')}</p>
        </div>
        <div className="page-actions">
          <Badge variant="info">
            {t(`content.types.${normalizeContentType(detailQuery.data?.content_type)}`, {
              defaultValue: detailQuery.data?.content_type || 'content',
            })}
          </Badge>
          {detailQuery.data?.status ? (
            <Badge variant={detailQuery.data.status === 'published' ? 'success' : 'warning'}>
              {t(`content.status.${detailQuery.data.status}`, {
                defaultValue: detailQuery.data.status,
              })}
            </Badge>
          ) : null}
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => navigate(`/content/${id}/play`)}
          >
            {t('content.openPlayer')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={toBannerError(
          detailQuery.error ??
            updateProgressMutation.error ??
            togglePublishMutation.error ??
            updateOrderingMutation.error,
          t('app.error'),
        )}
        onRetry={() => void detailQuery.refetch()}
      />

      <div className="stats-grid">
        <StatCard label="content.progressLabel" value={`${progressPercent}%`} icon="📈" />
        <StatCard
          label="content.analytics.started"
          value={
            detailQuery.data?.student_analytics?.students_started ?? (progressPercent > 0 ? 1 : 0)
          }
          icon="▶"
        />
        <StatCard
          label="content.analytics.completed"
          value={
            detailQuery.data?.student_analytics?.students_completed ??
            (progressStatus === 'completed' ? 1 : 0)
          }
          icon="✅"
        />
        <StatCard label="content.sortOrder" value={detailQuery.data?.sort_order ?? 0} icon="↕" />
      </div>

      <div className="card">
        <div
          style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}
        >
          <div style={{ flex: '1 1 320px' }}>
            <h2>{t('content.progressLabel')}</h2>
            <div
              aria-label={t('content.progressLabel')}
              style={{
                width: '100%',
                height: 12,
                borderRadius: 999,
                background: 'var(--color-bg-muted)',
                overflow: 'hidden',
                marginBottom: 12,
              }}
            >
              <div
                style={{
                  width: `${progressPercent}%`,
                  height: '100%',
                  background: 'var(--color-primary)',
                }}
              />
            </div>
            <p>{t(`content.progress.${progressStatus}`)}</p>
            <div className="page-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => void handleProgressChange('not_started')}
              >
                {t('content.markNotStarted')}
              </button>
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

          {isManager ? (
            <div style={{ flex: '1 1 260px' }}>
              <h2>{t('content.management')}</h2>
              <div className="page-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={togglePublishMutation.isPending}
                  onClick={() => void handlePublishToggle()}
                >
                  {togglePublishMutation.isPending
                    ? t('app.loading')
                    : detailQuery.data?.status === 'published'
                      ? t('content.unpublish')
                      : t('content.publish')}
                </button>
                <input
                  type="number"
                  className="filter-input"
                  min="0"
                  value={sortOrder}
                  aria-label={t('content.sortOrder')}
                  onChange={(event) => setSortOrder(event.target.value)}
                />
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={updateOrderingMutation.isPending}
                  onClick={() => void handleSaveOrder()}
                >
                  {updateOrderingMutation.isPending ? t('app.loading') : t('content.saveOrder')}
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <Tabs
        defaultTab="overview"
        tabs={[
          {
            id: 'overview',
            label: 'content.overview',
            content: (
              <div className="card">
                <h2>{t('content.description')}</h2>
                <p>{detailQuery.data?.description || t('content.noDescription')}</p>
              </div>
            ),
          },
          {
            id: 'analytics',
            label: 'content.studentAnalytics',
            content: (
              <DataTable
                columns={analyticsColumns}
                data={analyticsRows}
                loading={detailQuery.isFetching}
                emptyMessage="content.emptyAnalytics"
                ariaLabel={t('content.studentAnalytics')}
              />
            ),
          },
          {
            id: 'assets',
            label: 'content.assets',
            content: (
              <DataTable
                columns={assetColumns}
                data={(detailQuery.data?.assets ?? []) as AssetRow[]}
                loading={detailQuery.isFetching}
                emptyMessage="content.noAssets"
                ariaLabel={t('content.assets')}
              />
            ),
          },
        ]}
      />
    </div>
  );
}
