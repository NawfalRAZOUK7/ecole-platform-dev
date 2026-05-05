import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSignedUrl } from '@/shared/hooks/useSignedUrl';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { Tabs } from '@/shared/ui/Tabs';
import { CmsLibraryBrowseTab } from './CmsLibraryBrowseTab';
import { CONTENT_TYPES } from './content-upload.types';
import { useCmsContent } from './useCms';
import { fetchLevelMappings, buildLevelMap, type LevelAgeMapping } from '@/services/levels.service';
import type { CmsContentItem } from './cms.service';

function resolveThumbnailPath(item: CmsContentItem) {
  if (!item.thumbnail_path) {
    return null;
  }

  if (
    item.thumbnail_path.startsWith('/api/v1/') ||
    item.thumbnail_path.startsWith('/content-items/')
  ) {
    return item.thumbnail_path;
  }

  return null;
}

function SignedThumbnail({ item }: { item: CmsContentItem }) {
  const signedThumbnail = useSignedUrl(resolveThumbnailPath(item));

  if (!signedThumbnail.url) {
    return null;
  }

  return (
    <img
      src={signedThumbnail.url}
      alt=""
      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      onError={(event) => {
        (event.target as HTMLImageElement).style.display = 'none';
        void signedThumbnail.refresh();
      }}
    />
  );
}
const LEVELS = [
  'maternelle',
  'cp',
  'ce1',
  'ce2',
  'cm1',
  'cm2',
  '6eme',
  '5eme',
  '4eme',
  '3eme',
  '2nde',
  '1ere',
  'terminale',
];
const SUBJECTS = [
  'math',
  'french',
  'arabic',
  'science',
  'history',
  'geography',
  'english',
  'islamic_studies',
  'art',
  'sport',
];
const LANGUAGES = ['fr', 'ar', 'en'];
const STATUSES = ['draft', 'published', 'archived'];
const ORIGINS = ['PLATFORM', 'PROMOTED'];

export function CmsContentListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [contentType, setContentType] = useState('');
  const [level, setLevel] = useState('');
  const [subject, setSubject] = useState('');
  const [language, setLanguage] = useState('');
  const [status, setStatus] = useState('');
  const [origin, setOrigin] = useState('');
  const [search, setSearch] = useState('');
  const [levelMap, setLevelMap] = useState<Record<string, LevelAgeMapping>>({});

  useEffect(() => {
    fetchLevelMappings()
      .then((mappings) => setLevelMap(buildLevelMap(mappings)))
      .catch(() => {
        // Non-critical — hints simply won't show
      });
  }, []);
  const contentQuery = useCmsContent({
    content_type: contentType || undefined,
    level_band: level || undefined,
    subject: subject || undefined,
    language: language || undefined,
    status: status || undefined,
    origin: origin || undefined,
    search: search || undefined,
  });

  const items = useMemo(
    () => contentQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [contentQuery.data],
  );

  if (contentQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <h1 className="page-title">{t('cms.content.title')}</h1>
        <button className="btn btn-primary" onClick={() => navigate('/cms/upload')}>
          + {t('cms.nav.upload')}
        </button>
      </div>

      <ErrorBanner
        error={contentQuery.error instanceof Error ? contentQuery.error.message : null}
        onDismiss={() => {}}
        onRetry={() => void contentQuery.refetch()}
      />
      <Tabs
        tabs={[
          {
            id: 'managed',
            label: 'cms.content.tabs.managed',
            content: (
              <>
                <div
                  className="filter-bar"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: 8,
                    marginBottom: 16,
                  }}
                >
                  <input
                    className="filter-input"
                    type="search"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder={t('cms.content.searchPlaceholder')}
                  />
                  <select
                    className="filter-select"
                    value={contentType}
                    onChange={(event) => setContentType(event.target.value)}
                  >
                    <option value="">{t('cms.content.allTypes')}</option>
                    {CONTENT_TYPES.map((currentType) => (
                      <option key={currentType} value={currentType}>
                        {t(`cms.contentTypes.${currentType}`, currentType)}
                      </option>
                    ))}
                  </select>
                  <div>
                    <select
                      className="filter-select"
                      value={level}
                      onChange={(event) => setLevel(event.target.value)}
                    >
                      <option value="">{t('cms.content.allLevels')}</option>
                      {LEVELS.map((currentLevel) => (
                        <option key={currentLevel} value={currentLevel}>
                          {currentLevel}
                        </option>
                      ))}
                    </select>
                    {level && levelMap[level] ? (
                      <span
                        style={{
                          display: 'block',
                          fontSize: 11,
                          color: 'var(--color-text-secondary)',
                          marginTop: 2,
                        }}
                      >
                        {level.toUpperCase()} → {levelMap[level].default_age_min}-
                        {levelMap[level].default_age_max} {t('cms.content.ageHintSuffix', 'ans')}
                      </span>
                    ) : null}
                  </div>
                  <select
                    className="filter-select"
                    value={subject}
                    onChange={(event) => setSubject(event.target.value)}
                  >
                    <option value="">{t('cms.content.allSubjects')}</option>
                    {SUBJECTS.map((currentSubject) => (
                      <option key={currentSubject} value={currentSubject}>
                        {t(`cms.subjects.${currentSubject}`, currentSubject)}
                      </option>
                    ))}
                  </select>
                  <select
                    className="filter-select"
                    value={language}
                    onChange={(event) => setLanguage(event.target.value)}
                  >
                    <option value="">{t('cms.content.allLanguages')}</option>
                    {LANGUAGES.map((currentLanguage) => (
                      <option key={currentLanguage} value={currentLanguage}>
                        {currentLanguage}
                      </option>
                    ))}
                  </select>
                  <select
                    className="filter-select"
                    value={status}
                    onChange={(event) => setStatus(event.target.value)}
                  >
                    <option value="">{t('cms.content.allStatuses')}</option>
                    {STATUSES.map((currentStatus) => (
                      <option key={currentStatus} value={currentStatus}>
                        {t(`cms.statuses.${currentStatus}`, currentStatus)}
                      </option>
                    ))}
                  </select>
                  <select
                    className="filter-select"
                    value={origin}
                    onChange={(event) => setOrigin(event.target.value)}
                  >
                    <option value="">{t('cms.content.allOrigins')}</option>
                    {ORIGINS.map((currentOrigin) => (
                      <option key={currentOrigin} value={currentOrigin}>
                        {t(`cms.origins.${currentOrigin}`, currentOrigin)}
                      </option>
                    ))}
                  </select>
                </div>

                {items.length === 0 ? (
                  <p className="empty-state">{t('cms.content.empty')}</p>
                ) : (
                  <>
                    <div
                      className="card-grid"
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: 16,
                      }}
                    >
                      {items.map((item) => (
                        <div
                          key={item.id}
                          className="card"
                          style={{ cursor: 'pointer' }}
                          onClick={() => navigate(`/cms/content/${item.id}/edit`)}
                        >
                          {resolveThumbnailPath(item) ? (
                            <div
                              style={{
                                height: 140,
                                background: 'var(--color-bg-secondary)',
                                borderRadius: '8px 8px 0 0',
                                overflow: 'hidden',
                              }}
                            >
                              <SignedThumbnail item={item} />
                            </div>
                          ) : null}
                          <div style={{ padding: 12 }}>
                            <h3 style={{ margin: '0 0 4px', fontSize: 15 }}>{item.title}</h3>
                            {item.description ? (
                              <p
                                style={{
                                  margin: '0 0 8px',
                                  fontSize: 13,
                                  color: 'var(--color-text-secondary)',
                                }}
                              >
                                {item.description.substring(0, 100)}
                                {item.description.length > 100 ? '...' : ''}
                              </p>
                            ) : null}
                            <div
                              style={{ display: 'flex', gap: 6, flexWrap: 'wrap', fontSize: 11 }}
                            >
                              <span className="badge">{item.content_type}</span>
                              {item.level_band ? (
                                <span className="badge">{item.level_band}</span>
                              ) : null}
                              {item.subject ? (
                                <span className="badge">
                                  {t(`cms.subjects.${item.subject}`, item.subject)}
                                </span>
                              ) : null}
                              <span className={`badge badge--${item.status}`}>
                                {t(`cms.statuses.${item.status}`, item.status)}
                              </span>
                              {item.origin === 'PROMOTED' ? (
                                <span className="badge badge--promoted">
                                  {t('cms.origins.PROMOTED')}
                                </span>
                              ) : null}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {contentQuery.hasNextPage ? (
                      <div style={{ textAlign: 'center', marginTop: 16 }}>
                        <button
                          className="btn"
                          onClick={() => void contentQuery.fetchNextPage()}
                          disabled={contentQuery.isFetchingNextPage}
                        >
                          {contentQuery.isFetchingNextPage
                            ? t('app.loading')
                            : t('cms.content.loadMore')}
                        </button>
                      </div>
                    ) : null}
                  </>
                )}
              </>
            ),
          },
          {
            id: 'library',
            label: 'cms.content.tabs.library',
            content: <CmsLibraryBrowseTab />,
          },
        ]}
      />
    </div>
  );
}
