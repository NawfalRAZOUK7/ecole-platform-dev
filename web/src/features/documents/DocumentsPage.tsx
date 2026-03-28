import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, getAccessToken } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';

type DocumentsTab = 'mine' | 'student' | 'resources';

interface StudentOption {
  id: string;
  full_name: string;
  email?: string;
}

interface DocumentItem {
  id: string;
  original_filename: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  category: string;
  linked_student_id: string | null;
  linked_student_name: string | null;
  uploader_id: string;
  uploader_name: string | null;
  expires_at: string | null;
  is_expired: boolean;
  is_expiring_soon: boolean;
  download_count: number;
  thumbnail_url: string | null;
  preview_url: string | null;
  download_url: string | null;
  created_at: string;
  deduplicated: boolean;
  can_delete: boolean;
  can_hard_delete: boolean;
}

interface ChecklistItem {
  category: string;
  required: boolean;
  description: string | null;
  status: 'uploaded' | 'missing' | 'expired';
  expires_at: string | null;
  document: DocumentItem | null;
}

interface ResourceItem {
  id: string;
  title: string;
  description: string | null;
  subject: string | null;
  level: string | null;
  type: string;
  tags: string[];
  visibility: string;
  class_id: string | null;
  download_count: number;
  avg_rating: number;
  rating_count: number;
  download_url: string | null;
  preview_url: string | null;
  thumbnail_url: string | null;
  document: DocumentItem | null;
  my_rating: number | null;
  created_at: string;
  can_edit: boolean;
  can_delete: boolean;
  can_rate: boolean;
}

interface DocumentsOptionsPayload {
  students: StudentOption[];
  categories: string[];
}

interface DocumentsPageProps {
  initialTab?: DocumentsTab;
}

const RESOURCE_TYPES = [
  'lesson_plan',
  'worksheet',
  'presentation',
  'exam_template',
  'reference',
] as const;

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

export function DocumentsPage({ initialTab = 'mine' }: DocumentsPageProps) {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<DocumentsTab>(initialTab);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<DocumentsOptionsPayload>({ students: [], categories: [] });
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [studentDocuments, setStudentDocuments] = useState<DocumentItem[]>([]);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [resourcesCursor, setResourcesCursor] = useState<string | null>(null);
  const [resourcesHasMore, setResourcesHasMore] = useState(false);
  const [resourceModal, setResourceModal] = useState<ResourceItem | null>(null);
  const [previewItem, setPreviewItem] = useState<DocumentItem | null>(null);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState('other');
  const [uploadExpiry, setUploadExpiry] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [resourceFormOpen, setResourceFormOpen] = useState(false);
  const [resourceTitle, setResourceTitle] = useState('');
  const [resourceDescription, setResourceDescription] = useState('');
  const [resourceSubject, setResourceSubject] = useState('');
  const [resourceLevel, setResourceLevel] = useState('');
  const [resourceType, setResourceType] = useState<(typeof RESOURCE_TYPES)[number]>('lesson_plan');
  const [resourceTags, setResourceTags] = useState('');
  const [resourceSearch, setResourceSearch] = useState('');
  const [resourceFilterType, setResourceFilterType] = useState('');
  const [resourceFilterSubject, setResourceFilterSubject] = useState('');
  const [resourceFilterLevel, setResourceFilterLevel] = useState('');
  const [resourceFilterRating, setResourceFilterRating] = useState('');
  const [documentSearch, setDocumentSearch] = useState('');
  const [documentCategoryFilter, setDocumentCategoryFilter] = useState('');
  const [documentTypeFilter, setDocumentTypeFilter] = useState('');
  const [documentFromDate, setDocumentFromDate] = useState('');
  const [documentToDate, setDocumentToDate] = useState('');
  const uploadXhrRef = useRef<XMLHttpRequest | null>(null);

  const canManageStudentDocs = ['PAR', 'ADM', 'DIR', 'TCH', 'STD'].includes(user?.role || '');
  const canUploadDocuments = user?.role !== 'STD';
  const canUploadResources = ['TCH', 'ADM', 'DIR'].includes(user?.role || '');

  const loadOptions = useCallback(async () => {
    try {
      const response = await api.get<DocumentsOptionsPayload>('/documents/options');
      setOptions(response.data);
      if (!selectedStudentId && response.data.students.length > 0) {
        setSelectedStudentId(response.data.students[0].id);
      }
      if (response.data.categories.length > 0 && !uploadCategory) {
        setUploadCategory(response.data.categories[0]);
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [selectedStudentId, t, uploadCategory]);

  const loadDocuments = useCallback(async () => {
    try {
      const response = await api.list<DocumentItem>('/documents', {
        owner: 'me',
        limit: 100,
      });
      setDocuments(response.data);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  const loadStudentDocuments = useCallback(async () => {
    if (!selectedStudentId || !canManageStudentDocs) {
      setStudentDocuments([]);
      setChecklist([]);
      return;
    }
    try {
      const [documentsResponse, checklistResponse] = await Promise.all([
        api.list<DocumentItem>(`/students/${selectedStudentId}/documents`),
        api.get<ChecklistItem[]>(`/students/${selectedStudentId}/documents/checklist`),
      ]);
      setStudentDocuments(documentsResponse.data);
      setChecklist(checklistResponse.data);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [canManageStudentDocs, selectedStudentId, t]);

  const loadResources = useCallback(
    async (cursor?: string, append = false) => {
      try {
        const response = await api.list<ResourceItem>('/resources', {
          cursor,
          limit: 24,
          q: resourceSearch || undefined,
          type: resourceFilterType || undefined,
          subject: resourceFilterSubject || undefined,
          level: resourceFilterLevel || undefined,
          rating: resourceFilterRating || undefined,
        });
        setResources((current) => (append ? [...current, ...response.data] : response.data));
        setResourcesCursor(response.meta.next_cursor);
        setResourcesHasMore(response.meta.has_more);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : t('app.error'));
      }
    },
    [resourceFilterLevel, resourceFilterRating, resourceFilterSubject, resourceFilterType, resourceSearch, t]
  );

  useEffect(() => {
    setLoading(true);
    Promise.all([loadOptions(), loadDocuments(), loadResources()])
      .finally(() => setLoading(false));
  }, [loadDocuments, loadOptions, loadResources]);

  useEffect(() => {
    void loadStudentDocuments();
  }, [loadStudentDocuments]);

  useEffect(() => {
    void loadResources();
  }, [loadResources]);

  const filteredDocuments = useMemo(() => {
    const items = activeTab === 'student' ? studentDocuments : documents;
    return items.filter((item) => {
      if (documentCategoryFilter && item.category !== documentCategoryFilter) return false;
      if (documentTypeFilter && item.mime_type !== documentTypeFilter) return false;
      if (documentSearch) {
        const search = documentSearch.toLowerCase();
        if (
          !item.original_filename.toLowerCase().includes(search) &&
          !item.category.toLowerCase().includes(search)
        ) {
          return false;
        }
      }
      if (documentFromDate && item.created_at.slice(0, 10) < documentFromDate) return false;
      if (documentToDate && item.created_at.slice(0, 10) > documentToDate) return false;
      return true;
    });
  }, [
    activeTab,
    documentCategoryFilter,
    documentFromDate,
    documentSearch,
    documentToDate,
    documentTypeFilter,
    documents,
    studentDocuments,
  ]);

  const documentMimeOptions = useMemo(
    () =>
      Array.from(new Set([...(documents ?? []), ...(studentDocuments ?? [])].map((item) => item.mime_type))).sort(),
    [documents, studentDocuments]
  );

  async function performMultipartUpload(url: string, fields: Record<string, string>) {
    const token = getAccessToken();
    const formData = new FormData();
    if (!uploadFile) return;
    formData.append('file', uploadFile);
    Object.entries(fields).forEach(([key, value]) => {
      if (value) {
        formData.append(key, value);
      }
    });

    setUploading(true);
    setUploadProgress(0);

    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      uploadXhrRef.current = xhr;
      xhr.open('POST', `/api/v1${url}`);
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
    })
      .finally(() => {
        uploadXhrRef.current = null;
        setUploading(false);
      });
  }

  async function handleUpload() {
    if (!uploadFile) {
      return;
    }
    try {
      if (activeTab === 'resources') {
        await performMultipartUpload('/resources', {
          title: resourceTitle || uploadFile.name,
          description: resourceDescription,
          subject: resourceSubject,
          level: resourceLevel,
          type: resourceType,
          visibility: 'school',
          tags: resourceTags,
        });
        await loadResources();
        setResourceFormOpen(false);
      } else {
        await performMultipartUpload('/documents/upload', {
          category: uploadCategory,
          linked_student_id: activeTab === 'student' ? selectedStudentId : '',
          expires_at: uploadExpiry || '',
        });
        await Promise.all([loadDocuments(), loadStudentDocuments()]);
      }
      setUploadFile(null);
      setUploadExpiry('');
      setUploadProgress(100);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  async function handleDeleteDocuments(hard = false, ids = selectedDocumentIds) {
    try {
      if (!hard && user?.role === 'ADM' && ids.length > 1) {
        await api.post('/documents/bulk-delete', { document_ids: ids });
      } else {
        await Promise.all(
          ids.map((id) =>
            api.delete<{ deleted: boolean }>(`/documents/${id}${hard ? '?hard=true' : ''}`)
          )
        );
      }
      setSelectedDocumentIds([]);
      await Promise.all([loadDocuments(), loadStudentDocuments()]);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  async function handleBulkDownload(ids = selectedDocumentIds) {
    try {
      const response = await api.post<{ download_url: string }>('/documents/bulk-download', {
        document_ids: ids,
      });
      openSignedUrl(response.data.download_url);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  async function handleOpenResource(resourceId: string) {
    try {
      const response = await api.get<ResourceItem>(`/resources/${resourceId}`);
      setResourceModal(response.data);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  async function handleRateResource(resourceId: string, rating: number) {
    try {
      await api.post(`/resources/${resourceId}/rate`, { rating });
      await Promise.all([loadResources(), handleOpenResource(resourceId)]);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  function toggleDocumentSelection(documentId: string) {
    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((item) => item !== documentId)
        : [...current, documentId]
    );
  }

  if (loading) {
    return <LoadingState />;
  }

  return (
    <div className="page documents-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('documents.title')}</h1>
          <p className="page-subtitle">{t('documents.subtitle')}</p>
        </div>
        <div className="calendar-view-toggle">
          {(['mine', 'student', 'resources'] as DocumentsTab[]).map((tab) => (
            <button
              key={tab}
              type="button"
              className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => {
                setActiveTab(tab);
                setSelectedDocumentIds([]);
              }}
            >
              {t(`documents.tabs.${tab}`)}
            </button>
          ))}
        </div>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="documents-layout">
        <section className="card documents-main-card">
          <div className="documents-toolbar">
            <div className="documents-toolbar__filters">
              {activeTab !== 'resources' && (
                <>
                  <input
                    value={documentSearch}
                    onChange={(event) => setDocumentSearch(event.target.value)}
                    placeholder={t('documents.filters.search')}
                  />
                  <select value={documentCategoryFilter} onChange={(event) => setDocumentCategoryFilter(event.target.value)}>
                    <option value="">{t('documents.filters.allCategories')}</option>
                    {options.categories.map((category) => (
                      <option key={category} value={category}>
                        {t(`documents.categories.${category}`)}
                      </option>
                    ))}
                  </select>
                  <select value={documentTypeFilter} onChange={(event) => setDocumentTypeFilter(event.target.value)}>
                    <option value="">{t('documents.filters.allTypes')}</option>
                    {documentMimeOptions.map((mime) => (
                      <option key={mime} value={mime}>
                        {mime}
                      </option>
                    ))}
                  </select>
                  <input type="date" value={documentFromDate} onChange={(event) => setDocumentFromDate(event.target.value)} />
                  <input type="date" value={documentToDate} onChange={(event) => setDocumentToDate(event.target.value)} />
                </>
              )}

              {activeTab === 'resources' && (
                <>
                  <input
                    value={resourceSearch}
                    onChange={(event) => setResourceSearch(event.target.value)}
                    placeholder={t('documents.resources.searchPlaceholder')}
                  />
                  <input
                    value={resourceFilterSubject}
                    onChange={(event) => setResourceFilterSubject(event.target.value)}
                    placeholder={t('documents.resources.subject')}
                  />
                  <input
                    value={resourceFilterLevel}
                    onChange={(event) => setResourceFilterLevel(event.target.value)}
                    placeholder={t('documents.resources.level')}
                  />
                  <select value={resourceFilterType} onChange={(event) => setResourceFilterType(event.target.value)}>
                    <option value="">{t('documents.resources.allTypes')}</option>
                    {RESOURCE_TYPES.map((item) => (
                      <option key={item} value={item}>
                        {t(`documents.resourceTypes.${item}`)}
                      </option>
                    ))}
                  </select>
                  <select value={resourceFilterRating} onChange={(event) => setResourceFilterRating(event.target.value)}>
                    <option value="">{t('documents.resources.allRatings')}</option>
                    {[5, 4, 3].map((rating) => (
                      <option key={rating} value={rating}>
                        {t('documents.resources.ratingAtLeast', { rating })}
                      </option>
                    ))}
                  </select>
                </>
              )}
            </div>

            {activeTab !== 'resources' && (
              <div className="documents-toolbar__actions">
                <button type="button" className="btn btn-secondary" onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}>
                  {t(`documents.view.${viewMode === 'grid' ? 'list' : 'grid'}`)}
                </button>
                {selectedDocumentIds.length > 0 && (
                  <>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => void handleBulkDownload()}
                    >
                      {t('documents.bulk.download')}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => void handleDeleteDocuments(false)}
                    >
                      {t('documents.bulk.delete')}
                    </button>
                    {['ADM', 'DIR'].includes(user?.role || '') && (
                      <button type="button" className="btn btn-danger" onClick={() => void handleDeleteDocuments(true)}>
                        {t('documents.bulk.hardDelete')}
                      </button>
                    )}
                  </>
                )}
              </div>
            )}

            {activeTab === 'resources' && canUploadResources && (
              <button type="button" className="btn btn-primary" onClick={() => setResourceFormOpen((open) => !open)}>
                {t('documents.resources.uploadAction')}
              </button>
            )}
          </div>

          {activeTab === 'student' && options.students.length > 0 && (
            <div className="documents-student-header">
              <label className="form-field">
                <span>{t('documents.studentSelector')}</span>
                <select value={selectedStudentId} onChange={(event) => setSelectedStudentId(event.target.value)}>
                  {options.students.map((student) => (
                    <option key={student.id} value={student.id}>
                      {student.full_name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          {activeTab === 'student' && checklist.length > 0 && (
            <div className="documents-checklist">
              {checklist.map((item) => (
                <div key={item.category} className={`documents-checklist__item status-${item.status}`}>
                  <div>
                    <strong>{t(`documents.categories.${item.category}`)}</strong>
                    {item.description && <p>{item.description}</p>}
                  </div>
                  <span className={`status-badge status-${item.status}`}>{t(`documents.checklist.${item.status}`)}</span>
                </div>
              ))}
            </div>
          )}

          {((activeTab !== 'resources' && canUploadDocuments) || (activeTab === 'resources' && canUploadResources && resourceFormOpen)) && (
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

              {activeTab !== 'resources' && (
                <div className="documents-upload-fields">
                  <select value={uploadCategory} onChange={(event) => setUploadCategory(event.target.value)}>
                    {options.categories.map((category) => (
                      <option key={category} value={category}>
                        {t(`documents.categories.${category}`)}
                      </option>
                    ))}
                  </select>
                  <input type="date" value={uploadExpiry} onChange={(event) => setUploadExpiry(event.target.value)} />
                </div>
              )}

              {activeTab === 'resources' && (
                <div className="documents-upload-fields documents-upload-fields--resource">
                  <input value={resourceTitle} onChange={(event) => setResourceTitle(event.target.value)} placeholder={t('documents.resources.title')} />
                  <input value={resourceSubject} onChange={(event) => setResourceSubject(event.target.value)} placeholder={t('documents.resources.subject')} />
                  <input value={resourceLevel} onChange={(event) => setResourceLevel(event.target.value)} placeholder={t('documents.resources.level')} />
                  <select value={resourceType} onChange={(event) => setResourceType(event.target.value as (typeof RESOURCE_TYPES)[number])}>
                    {RESOURCE_TYPES.map((item) => (
                      <option key={item} value={item}>
                        {t(`documents.resourceTypes.${item}`)}
                      </option>
                    ))}
                  </select>
                  <input value={resourceTags} onChange={(event) => setResourceTags(event.target.value)} placeholder={t('documents.resources.tags')} />
                  <textarea value={resourceDescription} onChange={(event) => setResourceDescription(event.target.value)} placeholder={t('documents.resources.description')} />
                </div>
              )}

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
                <button type="button" className="btn btn-primary" onClick={() => void handleUpload()} disabled={!uploadFile || uploading}>
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

          {activeTab === 'resources' ? (
            <>
              {resources.length === 0 ? (
                <EmptyState message={t('documents.resources.empty')} icon="📚" />
              ) : (
                <div className="documents-resource-grid">
                  {resources.map((resource) => (
                    <button key={resource.id} type="button" className="documents-resource-card" onClick={() => void handleOpenResource(resource.id)}>
                      {resource.thumbnail_url ? (
                        <img src={resource.thumbnail_url} alt={resource.title} className="documents-resource-card__thumb" />
                      ) : (
                        <div className="documents-resource-card__thumb documents-resource-card__thumb--empty">📄</div>
                      )}
                      <div>
                        <strong>{resource.title}</strong>
                        <p>{[resource.subject, resource.level].filter(Boolean).join(' · ')}</p>
                        <span>{t('documents.resources.rating', { rating: resource.avg_rating.toFixed(1), count: resource.rating_count })}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              {resourcesHasMore && (
                <button type="button" className="btn btn-secondary" onClick={() => void loadResources(resourcesCursor || undefined, true)}>
                  {t('documents.resources.loadMore')}
                </button>
              )}
            </>
          ) : filteredDocuments.length === 0 ? (
            <EmptyState message={t('documents.empty')} icon="🗂️" />
          ) : (
            <div className={`documents-collection documents-collection--${viewMode}`}>
              {filteredDocuments.map((item) => (
                <article key={item.id} className="documents-card">
                  <label className="documents-card__select">
                    <input
                      type="checkbox"
                      checked={selectedDocumentIds.includes(item.id)}
                      onChange={() => toggleDocumentSelection(item.id)}
                    />
                  </label>
                  <button type="button" className="documents-card__preview" onClick={() => setPreviewItem(item)}>
                    {item.thumbnail_url ? (
                      <img src={item.thumbnail_url} alt={item.original_filename} />
                    ) : (
                      <span>{isPdf(item.mime_type) ? '📕' : isImage(item.mime_type) ? '🖼️' : '📄'}</span>
                    )}
                  </button>
                  <div className="documents-card__body">
                    <strong>{item.original_filename}</strong>
                    <p>{humanSize(item.size_bytes)} · {item.mime_type}</p>
                    <div className="documents-card__meta">
                      <span className="status-badge">{t(`documents.categories.${item.category}`)}</span>
                      {item.is_expired && <span className="status-badge status-expired">{t('documents.expired')}</span>}
                      {!item.is_expired && item.is_expiring_soon && <span className="status-badge status-warning">{t('documents.expiringSoon')}</span>}
                    </div>
                    <span>{formatDate(item.created_at, i18n.language, { dateStyle: 'medium', timeStyle: 'short' })}</span>
                  </div>
                  <div className="documents-card__actions">
                    {item.preview_url && (
                      <button type="button" className="dropdown-link" onClick={() => setPreviewItem(item)}>
                        {t('documents.preview')}
                      </button>
                    )}
                    <button type="button" className="dropdown-link" onClick={() => openSignedUrl(item.download_url)}>
                      {t('documents.download')}
                    </button>
                    {item.can_delete && (
                      <button
                        type="button"
                        className="dropdown-link"
                        onClick={() => void handleDeleteDocuments(false, [item.id])}
                      >
                        {t('documents.delete')}
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <aside className="card documents-preview-card">
          <h2>{t('documents.previewPanelTitle')}</h2>
          {!previewItem ? (
            <EmptyState message={t('documents.previewEmpty')} icon="🔎" />
          ) : (
            <div className="documents-preview-card__content">
              <strong>{previewItem.original_filename}</strong>
              {previewItem.preview_url && isImage(previewItem.mime_type) && (
                <img src={previewItem.preview_url} alt={previewItem.original_filename} className="documents-preview-card__image" />
              )}
              {previewItem.preview_url && isPdf(previewItem.mime_type) && (
                <iframe src={previewItem.preview_url} title={previewItem.original_filename} className="documents-preview-card__frame" />
              )}
              {!previewItem.preview_url && (
                <div className="documents-preview-card__fallback">📄</div>
              )}
              <p>{previewItem.mime_type}</p>
              <p>{humanSize(previewItem.size_bytes)}</p>
              {previewItem.expires_at && (
                <p>{t('documents.expiresAt')}: {formatDate(previewItem.expires_at, i18n.language, { dateStyle: 'medium' })}</p>
              )}
              <div className="documents-preview-card__actions">
                <button type="button" className="btn btn-secondary" onClick={() => openSignedUrl(previewItem.download_url)}>
                  {t('documents.download')}
                </button>
              </div>
            </div>
          )}
        </aside>
      </div>

      {resourceModal && (
        <div className="calendar-modal-shell" role="dialog" aria-modal="true">
          <div className="calendar-modal-card documents-resource-modal">
            <div className="calendar-modal-card__header">
              <h2>{resourceModal.title}</h2>
              <button type="button" className="btn btn-secondary" onClick={() => setResourceModal(null)}>
                {t('app.close')}
              </button>
            </div>
            {resourceModal.preview_url && isImage(resourceModal.document?.mime_type || '') && (
              <img src={resourceModal.preview_url} alt={resourceModal.title} className="documents-resource-modal__image" />
            )}
            {resourceModal.preview_url && isPdf(resourceModal.document?.mime_type || '') && (
              <iframe src={resourceModal.preview_url} title={resourceModal.title} className="documents-resource-modal__frame" />
            )}
            <p>{resourceModal.description}</p>
            <p>{[resourceModal.subject, resourceModal.level].filter(Boolean).join(' · ')}</p>
            <p>{resourceModal.tags.join(', ')}</p>
            <p>{t('documents.resources.rating', { rating: resourceModal.avg_rating.toFixed(1), count: resourceModal.rating_count })}</p>
            <div className="calendar-modal-card__actions">
              <button type="button" className="btn btn-primary" onClick={() => openSignedUrl(resourceModal.download_url)}>
                {t('documents.download')}
              </button>
              {resourceModal.can_rate && (
                <div className="documents-rating-group">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      type="button"
                      className={`btn ${resourceModal.my_rating === rating ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => void handleRateResource(resourceModal.id, rating)}
                    >
                      {rating}★
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
