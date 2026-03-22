/**
 * CMS Content List — list platform content with filters.
 *
 * Phase 10A — filters: type, level, subject, language, status, origin.
 * Calls GET /cms/content with pagination.
 */

import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';

interface ContentItem {
  id: string;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  thumbnail_path: string | null;
  origin: string;
  status: string;
  created_by: string | null;
  original_content_id: string | null;
}

const CONTENT_TYPES = ['video', 'pdf', 'audio', 'interactive'];
const LEVELS = ['maternelle', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];
const SUBJECTS = ['math', 'french', 'arabic', 'science', 'history', 'geography', 'english', 'islamic_studies', 'art', 'sport'];
const LANGUAGES = ['fr', 'ar', 'en'];
const STATUSES = ['draft', 'published', 'archived'];
const ORIGINS = ['PLATFORM', 'PROMOTED'];

export function CmsContentListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [items, setItems] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  // Filters
  const [contentType, setContentType] = useState('');
  const [level, setLevel] = useState('');
  const [subject, setSubject] = useState('');
  const [language, setLanguage] = useState('');
  const [status, setStatus] = useState('');
  const [origin, setOrigin] = useState('');
  const [search, setSearch] = useState('');

  const fetchContent = useCallback(async (append = false, nextCursor?: string | null) => {
    try {
      const params: Record<string, string | number | undefined> = { limit: 20 };
      if (contentType) params.content_type = contentType;
      if (level) params.level_band = level;
      if (subject) params.subject = subject;
      if (language) params.language = language;
      if (status) params.status = status;
      if (origin) params.origin = origin;
      if (search) params.search = search;
      if (nextCursor) params.cursor = nextCursor;

      const resp = await api.list<ContentItem>('/cms/content', params);
      setItems(append ? (prev) => [...prev, ...resp.data] : resp.data);
      setCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [contentType, level, subject, language, status, origin, search, t]);

  useEffect(() => {
    setLoading(true);
    fetchContent().finally(() => setLoading(false));
  }, [fetchContent]);

  function handleLoadMore() {
    if (cursor) fetchContent(true, cursor);
  }

  if (loading && items.length === 0) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 className="page-title">{t('cms.content.title')}</h1>
        <button className="btn btn-primary" onClick={() => navigate('/cms/upload')}>
          {t('cms.content.create')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchContent()} />

      {/* Filters */}
      <div className="filter-bar" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <input
          className="filter-input"
          placeholder={t('cms.content.searchPlaceholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ minWidth: 200 }}
        />
        <select className="filter-select" value={contentType} onChange={(e) => setContentType(e.target.value)}>
          <option value="">{t('cms.content.allTypes')}</option>
          {CONTENT_TYPES.map((ct) => (
            <option key={ct} value={ct}>{t(`cms.contentTypes.${ct}`, ct)}</option>
          ))}
        </select>
        <select className="filter-select" value={level} onChange={(e) => setLevel(e.target.value)}>
          <option value="">{t('cms.content.allLevels')}</option>
          {LEVELS.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <select className="filter-select" value={subject} onChange={(e) => setSubject(e.target.value)}>
          <option value="">{t('cms.content.allSubjects')}</option>
          {SUBJECTS.map((s) => (
            <option key={s} value={s}>{t(`cms.subjects.${s}`, s)}</option>
          ))}
        </select>
        <select className="filter-select" value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="">{t('cms.content.allLanguages')}</option>
          {LANGUAGES.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <select className="filter-select" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">{t('cms.content.allStatuses')}</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{t(`cms.statuses.${s}`, s)}</option>
          ))}
        </select>
        <select className="filter-select" value={origin} onChange={(e) => setOrigin(e.target.value)}>
          <option value="">{t('cms.content.allOrigins')}</option>
          {ORIGINS.map((o) => (
            <option key={o} value={o}>{t(`cms.origins.${o}`, o)}</option>
          ))}
        </select>
      </div>

      {/* Content grid */}
      {items.length === 0 ? (
        <p className="empty-state">{t('cms.content.empty')}</p>
      ) : (
        <>
          <div className="card-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
            {items.map((item) => (
              <div
                key={item.id}
                className="card"
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/cms/content/${item.id}/edit`)}
              >
                {item.thumbnail_path && (
                  <div style={{ height: 140, background: 'var(--color-bg-secondary)', borderRadius: '8px 8px 0 0', overflow: 'hidden' }}>
                    <img
                      src={`/api/v1/content-items/${item.id}/assets/${item.thumbnail_path}`}
                      alt=""
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                  </div>
                )}
                <div style={{ padding: 12 }}>
                  <h3 style={{ margin: '0 0 4px', fontSize: 15 }}>{item.title}</h3>
                  {item.description && (
                    <p style={{ margin: '0 0 8px', fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {item.description.substring(0, 100)}{item.description.length > 100 ? '...' : ''}
                    </p>
                  )}
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', fontSize: 11 }}>
                    <span className="badge">{item.content_type}</span>
                    {item.level_band && <span className="badge">{item.level_band}</span>}
                    {item.subject && <span className="badge">{t(`cms.subjects.${item.subject}`, item.subject)}</span>}
                    <span className={`badge badge--${item.status}`}>{t(`cms.statuses.${item.status}`, item.status)}</span>
                    {item.origin === 'PROMOTED' && <span className="badge badge--promoted">{t('cms.origins.PROMOTED')}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button className="btn" onClick={handleLoadMore}>
                {t('cms.content.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
