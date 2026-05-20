import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { Badge, EmptyState, ErrorBanner, LoadingState, SearchInput, Tabs } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { normalizeContentType } from '../model/content-types';
import type { ContentItem } from '../api/content.api';
import { useContentItems } from '../model/useContent';

const CONTENT_TYPE_TABS = [
  { id: 'all', label: 'content.tabAll' },
  { id: 'video', label: 'content.types.video' },
  { id: 'document', label: 'content.types.document' },
  { id: 'quiz', label: 'content.types.quiz' },
  { id: 'story', label: 'content.types.story' },
  { id: 'coloring_book', label: 'content.types.coloring_book' },
  { id: 'link', label: 'content.types.link' },
] as const;

function getLevel(item: ContentItem) {
  return item.level_band || item.level_tag || null;
}

export function ContentPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const contentQuery = useContentItems({
    search: search || undefined,
    level_band: levelFilter || undefined,
  });
  const items = useMemo(
    () => contentQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [contentQuery.data],
  );
  const dismissibleError = useDismissibleError(toBannerError(contentQuery.error, t('app.error')));

  if (contentQuery.isLoading && !contentQuery.data) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('content.title')}</h1>
          <p className="page-subtitle">{t('content.subtitle')}</p>
        </div>
        <div className="page-actions">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="content.searchPlaceholder"
          />
          <select
            value={levelFilter}
            className="filter-select"
            aria-label={t('content.level')}
            onChange={(event) => setLevelFilter(event.target.value)}
          >
            <option value="">{t('content.allLevels')}</option>
            <option value="beginner">{t('content.levels.beginner')}</option>
            <option value="intermediate">{t('content.levels.intermediate')}</option>
            <option value="advanced">{t('content.levels.advanced')}</option>
          </select>
        </div>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void contentQuery.refetch()}
      />

      {items.length === 0 ? (
        <EmptyState message={t('content.empty')} icon="📚" />
      ) : (
        <>
          <Tabs
            defaultTab="all"
            tabs={CONTENT_TYPE_TABS.map((tab) => {
              const filteredItems =
                tab.id === 'all'
                  ? items
                  : items.filter((item) => normalizeContentType(item.content_type) === tab.id);

              return {
                id: tab.id,
                label: tab.label,
                content:
                  filteredItems.length === 0 ? (
                    <EmptyState message={t('content.emptyFiltered')} icon="🔎" />
                  ) : (
                    <div className="card-list">
                      {filteredItems.map((item) => (
                        <article key={item.id} className="card content-card">
                          <div className="content-header">
                            <Badge variant="info">
                              {t(`content.types.${normalizeContentType(item.content_type)}`)}
                            </Badge>
                            {item.status ? (
                              <Badge variant={item.status === 'published' ? 'success' : 'warning'}>
                                {t(`content.status.${item.status}`, { defaultValue: item.status })}
                              </Badge>
                            ) : null}
                          </div>
                          <h3 className="content-title">{item.title}</h3>
                          <div className="content-meta">
                            {item.language ? <span>{item.language}</span> : null}
                            {getLevel(item) ? <span>{getLevel(item)}</span> : null}
                          </div>
                          <div className="page-actions">
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() => navigate(`/content/${item.id}`)}
                            >
                              {t('content.viewDetails')}
                            </button>
                            <button
                              type="button"
                              className="btn btn-primary"
                              onClick={() => navigate(`/content/${item.id}/play`)}
                            >
                              {t('content.openPlayer')}
                            </button>
                          </div>
                        </article>
                      ))}
                    </div>
                  ),
              };
            })}
          />

          {contentQuery.hasNextPage ? (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={() => void contentQuery.fetchNextPage()}
                disabled={contentQuery.isFetchingNextPage}
              >
                {contentQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
