/**
 * Content library page — list content items with filters.
 *
 * Reference: S-081 — Content page with type/level filters
 * Calls GET /content-items with cursor pagination and query params.
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import { useContentItems } from './useContent';
import type { ContentItem } from './content.service';

export function ContentPage() {
  const { t, i18n } = useTranslation();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const contentQuery = useContentItems({
    search: search || undefined,
    content_type: typeFilter || undefined,
    level_tag: levelFilter || undefined,
  });
  const items: ContentItem[] = useMemo(
    () => contentQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [contentQuery.data]
  );
  const dismissibleError = useDismissibleError(toBannerError(contentQuery.error, t('app.error')));

  if (contentQuery.isLoading && !contentQuery.data) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('content.title')}</h1>

      <div className="filters-bar">
        <input
          type="search"
          className="filter-input"
          placeholder={t('content.searchPlaceholder')}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} className="filter-select">
          <option value="">{t('content.allTypes')}</option>
          <option value="video">Video</option>
          <option value="document">Document</option>
          <option value="quiz">Quiz</option>
          <option value="interactive">Interactive</option>
        </select>
        <select value={levelFilter} onChange={(event) => setLevelFilter(event.target.value)} className="filter-select">
          <option value="">{t('content.allLevels')}</option>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
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
          <div className="card-list">
            {items.map((item) => (
              <div key={item.id} className="card content-card">
                <div className="content-header">
                  <span className="content-type-badge">{item.content_type}</span>
                  {item.level_tag && <span className="content-level-badge">{item.level_tag}</span>}
                </div>
                <h3 className="content-title">{item.title}</h3>
                <div className="content-meta">
                  {item.language && <span>{item.language}</span>}
                  <time>{formatDate(item.created_at, i18n.language)}</time>
                </div>
              </div>
            ))}
          </div>

          {contentQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button className="btn btn-secondary" onClick={() => void contentQuery.fetchNextPage()} disabled={contentQuery.isFetchingNextPage}>
                {contentQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
