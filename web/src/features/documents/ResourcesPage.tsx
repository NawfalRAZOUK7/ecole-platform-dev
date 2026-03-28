import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, getAccessToken } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';

const RESOURCE_TYPES = [
  'lesson_plan',
  'worksheet',
  'presentation',
  'exam_template',
  'reference',
] as const;

interface ResourceDocumentPreview {
  mime_type: string;
  size_bytes: number;
  preview_url: string | null;
}

interface ResourceItem {
  id: string;
  title: string;
  description: string | null;
  subject: string | null;
  level: string | null;
  type: string;
  tags: string[];
  author: string | null;
  download_count: number;
  avg_rating: number;
  rating_count: number;
  download_url: string | null;
  preview_url: string | null;
  thumbnail_url: string | null;
  document: ResourceDocumentPreview | null;
  my_rating: number | null;
  created_at: string;
  can_edit: boolean;
  can_delete: boolean;
  can_rate: boolean;
}

function isImage(mimeType: string) {
  return mimeType.startsWith('image/');
}

function isPdf(mimeType: string) {
  return mimeType === 'application/pdf';
}

function humanSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function openSignedUrl(url: string | null) {
  if (!url) return;
  const href = url.startsWith('http') ? url : `${window.location.origin}${url}`;
  window.open(href, '_blank', 'noopener,noreferrer');
}

export function ResourcesPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const uploadXhrRef = useRef<XMLHttpRequest | null>(null);

  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [selectedResource, setSelectedResource] = useState<ResourceItem | null>(null);

  const [search, setSearch] = useState('');
  const [subjectFilter, setSubjectFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [tagsFilter, setTagsFilter] = useState('');

  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [resourceTitle, setResourceTitle] = useState('');
  const [resourceDescription, setResourceDescription] = useState('');
  const [resourceSubject, setResourceSubject] = useState('');
  const [resourceLevel, setResourceLevel] = useState('');
  const [resourceType, setResourceType] = useState<(typeof RESOURCE_TYPES)[number]>('lesson_plan');
  const [resourceTags, setResourceTags] = useState('');

  const canUploadResources = ['TCH', 'ADM', 'DIR'].includes(user?.role || '');

  const loadResources = useCallback(
    async (cursor?: string, append = false) => {
      try {
        setError(null);
        if (append) {
          setLoadingMore(true);
        } else {
          setLoading(true);
        }
        const response = await api.list<ResourceItem>('/resources', {
          cursor,
          limit: 18,
          q: search || undefined,
          subject: subjectFilter || undefined,
          level: levelFilter || undefined,
          type: typeFilter || undefined,
          tags: tagsFilter || undefined,
        });
        setResources((current) => (append ? [...current, ...response.data] : response.data));
        setNextCursor(response.meta.next_cursor);
        setHasMore(response.meta.has_more);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : t('app.error'));
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [levelFilter, search, subjectFilter, tagsFilter, t, typeFilter]
  );

  useEffect(() => {
    void loadResources();
  }, [loadResources]);

  const loadResourceDetail = useCallback(
    async (resourceId: string) => {
      try {
        setDetailLoading(true);
        setError(null);
        const response = await api.get<ResourceItem>(`/resources/${resourceId}`);
        setSelectedResource(response.data);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : t('app.error'));
      } finally {
        setDetailLoading(false);
      }
    },
    [t]
  );

  async function performMultipartUpload() {
    if (!uploadFile) {
      return;
    }
    const token = getAccessToken();
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('title', resourceTitle || uploadFile.name);
    formData.append('description', resourceDescription);
    formData.append('subject', resourceSubject);
    formData.append('level', resourceLevel);
    formData.append('type', resourceType);
    formData.append('visibility', 'school');
    formData.append('tags', resourceTags);

    setUploading(true);
    setUploadProgress(0);

    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      uploadXhrRef.current = xhr;
      xhr.open('POST', '/api/v1/resources');
      xhr.setRequestHeader('Accept-Language', i18n.language || 'fr');
      xhr.setRequestHeader('X-Correlation-Id', crypto.randomUUID());
      xhr.setRequestHeader('X-Client-Version', '0.1.0');
      xhr.setRequestHeader('X-Client-Platform', 'web');
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          setUploadProgress(Math.round((event.loaded / event.total) * 100));
        }
      };
      xhr.onerror = () => reject(new Error(t('app.error')));
      xhr.onabort = () => reject(new Error(t('documents.uploadCanceled')));
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
          return;
        }
        try {
          const payload = JSON.parse(xhr.responseText);
          reject(new Error(payload?.error?.message || t('app.error')));
        } catch {
          reject(new Error(t('app.error')));
        }
      };
      xhr.send(formData);
    }).finally(() => {
      uploadXhrRef.current = null;
      setUploading(false);
    });
  }

  async function handleUpload() {
    if (!uploadFile) {
      return;
    }
    try {
      await performMultipartUpload();
      setUploadFile(null);
      setUploadProgress(100);
      setUploadOpen(false);
      setResourceTitle('');
      setResourceDescription('');
      setResourceSubject('');
      setResourceLevel('');
      setResourceType('lesson_plan');
      setResourceTags('');
      await loadResources();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  async function handleRate(resourceId: string, rating: number) {
    try {
      setError(null);
      await api.post(`/resources/${resourceId}/rate`, { rating });
      await Promise.all([loadResources(), loadResourceDetail(resourceId)]);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  async function handleLoadMore() {
    if (!hasMore || !nextCursor) {
      return;
    }
    await loadResources(nextCursor, true);
  }

  if (loading) {
    return <LoadingState />;
  }

  return (
    <div className="page documents-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('documents.tabs.resources')}</h1>
          <p className="page-subtitle">{t('documents.resources.empty')}</p>
        </div>
        <div className="documents-toolbar__actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setSearch('');
              setSubjectFilter('');
              setLevelFilter('');
              setTypeFilter('');
              setTagsFilter('');
            }}
          >
            {t('app.reset', 'Reset')}
          </button>
          {canUploadResources && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setUploadOpen((current) => !current)}
            >
              {t('documents.resources.uploadAction')}
            </button>
          )}
        </div>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <section className="card documents-main-card">
        <div className="documents-toolbar">
          <div className="documents-toolbar__filters">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t('documents.resources.searchPlaceholder')}
            />
            <input
              value={subjectFilter}
              onChange={(event) => setSubjectFilter(event.target.value)}
              placeholder={t('documents.resources.subject')}
            />
            <input
              value={levelFilter}
              onChange={(event) => setLevelFilter(event.target.value)}
              placeholder={t('documents.resources.level')}
            />
            <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
              <option value="">{t('documents.resources.allTypes')}</option>
              {RESOURCE_TYPES.map((item) => (
                <option key={item} value={item}>
                  {t(`documents.resourceTypes.${item}`)}
                </option>
              ))}
            </select>
            <input
              value={tagsFilter}
              onChange={(event) => setTagsFilter(event.target.value)}
              placeholder={t('documents.resources.tags')}
            />
          </div>
        </div>

        {uploadOpen && canUploadResources && (
          <div
            className="documents-upload-dropzone"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              const dropped = event.dataTransfer.files?.[0];
              if (dropped) {
                setUploadFile(dropped);
              }
            }}
          >
            <strong>{t('documents.uploadTitle')}</strong>
            <p>{t('documents.uploadSubtitle')}</p>
            <input
              type="file"
              onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
            />

            <div className="documents-upload-fields documents-upload-fields--resource">
              <input
                value={resourceTitle}
                onChange={(event) => setResourceTitle(event.target.value)}
                placeholder={t('documents.resources.title')}
              />
              <input
                value={resourceSubject}
                onChange={(event) => setResourceSubject(event.target.value)}
                placeholder={t('documents.resources.subject')}
              />
              <input
                value={resourceLevel}
                onChange={(event) => setResourceLevel(event.target.value)}
                placeholder={t('documents.resources.level')}
              />
              <select
                value={resourceType}
                onChange={(event) => setResourceType(event.target.value as (typeof RESOURCE_TYPES)[number])}
              >
                {RESOURCE_TYPES.map((item) => (
                  <option key={item} value={item}>
                    {t(`documents.resourceTypes.${item}`)}
                  </option>
                ))}
              </select>
              <input
                value={resourceTags}
                onChange={(event) => setResourceTags(event.target.value)}
                placeholder={t('documents.resources.tags')}
              />
              <textarea
                value={resourceDescription}
                onChange={(event) => setResourceDescription(event.target.value)}
                placeholder={t('documents.resources.description')}
              />
            </div>

            {uploadFile && (
              <div className="documents-upload-summary">
                <span>{uploadFile.name}</span>
                <span>{humanSize(uploadFile.size)}</span>
              </div>
            )}

            {uploading && (
              <div className="documents-upload-progress">
                <div style={{ width: `${uploadProgress}%` }} />
              </div>
            )}

            <div className="documents-upload-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => void handleUpload()}
                disabled={!uploadFile || uploading}
              >
                {uploading ? t('documents.uploading') : t('documents.uploadAction')}
              </button>
              {uploading && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => uploadXhrRef.current?.abort()}
                >
                  {t('documents.cancelUpload')}
                </button>
              )}
            </div>
          </div>
        )}

        {resources.length === 0 ? (
          <EmptyState message={t('documents.resources.empty')} icon="📚" />
        ) : (
          <div className="documents-resource-grid">
            {resources.map((resource) => (
              <article key={resource.id} className="documents-resource-card">
                <button
                  type="button"
                  className="documents-card__preview"
                  onClick={() => void loadResourceDetail(resource.id)}
                >
                  {resource.thumbnail_url ? (
                    <img
                      src={resource.thumbnail_url}
                      alt={resource.title}
                      className="documents-resource-card__thumb"
                    />
                  ) : (
                    <div className="documents-resource-card__thumb documents-resource-card__thumb--empty">
                      📄
                    </div>
                  )}
                </button>

                <div className="documents-card__body">
                  <div className="documents-card__meta">
                    <span className="status-badge">
                      {t(`documents.resourceTypes.${resource.type}`, resource.type)}
                    </span>
                    {resource.subject && <span className="status-badge">{resource.subject}</span>}
                  </div>
                  <strong>{resource.title}</strong>
                  <p>{resource.description || t('documents.resources.empty')}</p>
                  <p>{[resource.level, resource.author].filter(Boolean).join(' · ')}</p>
                  <span>
                    {t('documents.resources.rating', {
                      rating: resource.avg_rating.toFixed(1),
                      count: resource.rating_count,
                    })}
                  </span>
                  <span>
                    {t('documents.download', 'Download')} · {resource.download_count}
                  </span>
                  <span>{formatDate(resource.created_at, i18n.language, { dateStyle: 'medium' })}</span>
                </div>

                <div className="documents-card__actions">
                  <button
                    type="button"
                    className="dropdown-link"
                    onClick={() => void loadResourceDetail(resource.id)}
                  >
                    {t('documents.preview')}
                  </button>
                  <button
                    type="button"
                    className="dropdown-link"
                    onClick={() => openSignedUrl(resource.download_url)}
                  >
                    {t('documents.download')}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}

        {hasMore && (
          <div className="documents-upload-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => void handleLoadMore()}
              disabled={loadingMore}
            >
              {loadingMore ? t('documents.uploading') : t('documents.resources.loadMore')}
            </button>
          </div>
        )}
      </section>

      {selectedResource && (
        <div className="calendar-modal-shell" role="dialog" aria-modal="true">
          <div className="calendar-modal-card documents-resource-modal">
            <div className="calendar-modal-card__header">
              <h2>{selectedResource.title}</h2>
              <button type="button" className="btn btn-secondary" onClick={() => setSelectedResource(null)}>
                {t('app.close')}
              </button>
            </div>

            {detailLoading ? (
              <LoadingState />
            ) : (
              <>
                {selectedResource.preview_url &&
                  selectedResource.document &&
                  isImage(selectedResource.document.mime_type) && (
                    <img
                      src={selectedResource.preview_url}
                      alt={selectedResource.title}
                      className="documents-resource-modal__image"
                    />
                  )}
                {selectedResource.preview_url &&
                  selectedResource.document &&
                  isPdf(selectedResource.document.mime_type) && (
                    <iframe
                      src={selectedResource.preview_url}
                      title={selectedResource.title}
                      className="documents-resource-modal__frame"
                    />
                  )}

                <p>{selectedResource.description || '—'}</p>
                <p>{[selectedResource.subject, selectedResource.level].filter(Boolean).join(' · ') || '—'}</p>
                <p>{selectedResource.author || '—'}</p>
                <p>{selectedResource.tags.join(', ') || '—'}</p>
                <p>
                  {t('documents.resources.rating', {
                    rating: selectedResource.avg_rating.toFixed(1),
                    count: selectedResource.rating_count,
                  })}
                </p>
                <p>
                  {t('documents.download', 'Download')} · {selectedResource.download_count}
                </p>
                <p>{formatDate(selectedResource.created_at, i18n.language, { dateStyle: 'medium' })}</p>
                {selectedResource.document && (
                  <p>
                    {selectedResource.document.mime_type} · {humanSize(selectedResource.document.size_bytes)}
                  </p>
                )}

                <div className="calendar-modal-card__actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => openSignedUrl(selectedResource.download_url)}
                  >
                    {t('documents.download')}
                  </button>
                  {selectedResource.can_rate && (
                    <div className="documents-rating-group">
                      {[1, 2, 3, 4, 5].map((rating) => (
                        <button
                          key={rating}
                          type="button"
                          className={`btn ${selectedResource.my_rating === rating ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => void handleRate(selectedResource.id, rating)}
                        >
                          {rating}★
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
