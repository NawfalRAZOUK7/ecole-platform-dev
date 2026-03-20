/**
 * Content library page — list content items with filters.
 *
 * Reference: S-081 — Content page with type/level filters
 * Calls GET /content-items with cursor pagination and query params.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface ContentItem {
  id: string;
  course_id: string;
  title: string;
  content_type: string;
  body_url: string | null;
  level_tag: string | null;
  language: string | null;
  sort_order: number;
  created_at: string;
}

export function ContentPage() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');

  const fetchContent = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;
      if (search) params.search = search;
      if (typeFilter) params.content_type = typeFilter;
      if (levelFilter) params.level_tag = levelFilter;

      const resp = await api.list<ContentItem>('/content-items', params);
      if (cursor) {
        setItems((prev) => [...prev, ...resp.data]);
      } else {
        setItems(resp.data);
      }
      setNextCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t, search, typeFilter, levelFilter]);

  useEffect(() => {
    setLoading(true);
    fetchContent().finally(() => setLoading(false));
  }, [fetchContent]);

  async function handleLoadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchContent(nextCursor);
    setLoadingMore(false);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('content.title')}</h1>

      {/* Search + Filters */}
      <div className="filters-bar">
        <input
          type="search"
          className="filter-input"
          placeholder={t('content.searchPlaceholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">{t('content.allTypes')}</option>
          <option value="video">Video</option>
          <option value="document">Document</option>
          <option value="quiz">Quiz</option>
          <option value="interactive">Interactive</option>
        </select>

        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">{t('content.allLevels')}</option>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchContent()} />

      {items.length === 0 ? (
        <EmptyState message={t('content.empty')} icon="📚" />
      ) : (
        <>
          <div className="card-list">
            {items.map((item) => (
              <div key={item.id} className="card content-card">
                <div className="content-header">
                  <span className="content-type-badge">{item.content_type}</span>
                  {item.level_tag && (
                    <span className="content-level-badge">{item.level_tag}</span>
                  )}
                </div>
                <h3 className="content-title">{item.title}</h3>
                <div className="content-meta">
                  {item.language && <span>{item.language}</span>}
                  <time>{formatDate(item.created_at, i18n.language)}</time>
                </div>
              </div>
            ))}
          </div>

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
