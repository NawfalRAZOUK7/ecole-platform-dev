import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import {
  useBulkDeleteDocuments,
  useBulkDownloadDocuments,
  useDocumentsOptions,
  useMyDocuments,
  useRateResource,
  useResourceDetail,
  useResources,
  useStudentChecklist,
  useStudentDocuments,
  useUploadDocument,
  useUploadResource,
} from './useDocuments';
import type {
  DocumentItem,
  DocumentsTab,
  ResourceItem,
} from './documents.service';

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
  const uploadXhrRef = useRef<{ abort: () => void } | null>(null);
  const [activeTab, setActiveTab] = useState<DocumentsTab>(initialTab);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState('other');
  const [uploadExpiry, setUploadExpiry] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
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
  const [previewItem, setPreviewItem] = useState<DocumentItem | null>(null);
  const [selectedResourceId, setSelectedResourceId] = useState<string | null>(null);

  const canManageStudentDocs = ['PAR', 'ADM', 'DIR', 'TCH', 'STD'].includes(user?.role || '');
  const canUploadDocuments = user?.role !== 'STD';
  const canUploadResources = ['TCH', 'ADM', 'DIR'].includes(user?.role || '');

  const optionsQuery = useDocumentsOptions();
  const myDocumentsQuery = useMyDocuments();
  const studentDocumentsQuery = useStudentDocuments(selectedStudentId, canManageStudentDocs);
  const checklistQuery = useStudentChecklist(selectedStudentId, canManageStudentDocs);
  const resourcesQuery = useResources({
    q: resourceSearch || undefined,
    type: resourceFilterType || undefined,
    subject: resourceFilterSubject || undefined,
    level: resourceFilterLevel || undefined,
    rating: resourceFilterRating || undefined,
  });
  const resourceDetailQuery = useResourceDetail(selectedResourceId);
  const uploadDocumentMutation = useUploadDocument();
  const uploadResourceMutation = useUploadResource();
  const deleteDocumentsMutation = useBulkDeleteDocuments();
  const bulkDownloadMutation = useBulkDownloadDocuments();
  const rateResourceMutation = useRateResource();

  const options = optionsQuery.data ?? { students: [], categories: [] };
  const documents = myDocumentsQuery.data ?? [];
  const studentDocuments = studentDocumentsQuery.data ?? [];
  const checklist = checklistQuery.data ?? [];
  const resources: ResourceItem[] = useMemo(
    () => resourcesQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [resourcesQuery.data]
  );
  const selectedResource = resourceDetailQuery.data ?? resources.find((resource) => resource.id === selectedResourceId) ?? null;
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          optionsQuery.error ??
            myDocumentsQuery.error ??
            studentDocumentsQuery.error ??
            checklistQuery.error ??
            resourcesQuery.error ??
            resourceDetailQuery.error ??
            uploadDocumentMutation.error ??
            uploadResourceMutation.error ??
            deleteDocumentsMutation.error ??
            bulkDownloadMutation.error ??
            rateResourceMutation.error,
          t('app.error')
        ),
      [
        bulkDownloadMutation.error,
        checklistQuery.error,
        deleteDocumentsMutation.error,
        myDocumentsQuery.error,
        optionsQuery.error,
        rateResourceMutation.error,
        resourceDetailQuery.error,
        resourcesQuery.error,
        studentDocumentsQuery.error,
        t,
        uploadDocumentMutation.error,
        uploadResourceMutation.error,
      ]
    )
  );

  useEffect(() => {
    if (!selectedStudentId && options.students.length > 0) {
      setSelectedStudentId(options.students[0].id);
    }
    if (options.categories.length > 0 && !uploadCategory) {
      setUploadCategory(options.categories[0]);
    }
  }, [options.categories, options.students, selectedStudentId, uploadCategory]);

  const filteredDocuments = useMemo(() => {
    const items = activeTab === 'student' ? studentDocuments : documents;
    return items.filter((item) => {
      if (documentCategoryFilter && item.category !== documentCategoryFilter) return false;
      if (documentTypeFilter && item.mime_type !== documentTypeFilter) return false;
      if (documentSearch) {
        const search = documentSearch.toLowerCase();
        if (!item.original_filename.toLowerCase().includes(search) && !item.category.toLowerCase().includes(search)) {
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
    () => Array.from(new Set([...(documents ?? []), ...(studentDocuments ?? [])].map((item) => item.mime_type))).sort(),
    [documents, studentDocuments]
  );

  async function handleUpload() {
    if (!uploadFile) {
      return;
    }

    if (activeTab === 'resources') {
      await uploadResourceMutation.mutateAsync({
        payload: {
          file: uploadFile,
          title: resourceTitle || uploadFile.name,
          description: resourceDescription,
          subject: resourceSubject,
          level: resourceLevel,
          type: resourceType,
          tags: resourceTags,
          language: i18n.language || 'fr',
        },
        onProgress: setUploadProgress,
        onRequestCreated: (xhr) => {
          uploadXhrRef.current = xhr;
        },
      });
      setResourceFormOpen(false);
      await resourcesQuery.refetch();
    } else {
      await uploadDocumentMutation.mutateAsync({
        payload: {
          file: uploadFile,
          category: uploadCategory,
          linkedStudentId: activeTab === 'student' ? selectedStudentId : undefined,
          expiresAt: uploadExpiry || undefined,
          language: i18n.language || 'fr',
        },
        onProgress: setUploadProgress,
        onRequestCreated: (xhr) => {
          uploadXhrRef.current = xhr;
        },
      });
      await Promise.all([myDocumentsQuery.refetch(), studentDocumentsQuery.refetch(), checklistQuery.refetch()]);
    }

    uploadXhrRef.current = null;
    setUploadFile(null);
    setUploadExpiry('');
    setUploadProgress(0);
  }

  async function handleDeleteDocuments(hard = false, ids = selectedDocumentIds) {
    await deleteDocumentsMutation.mutateAsync({
      documentIds: ids,
      hard,
      useBulkEndpoint: !hard && user?.role === 'ADM' && ids.length > 1,
    });
    setSelectedDocumentIds([]);
    await Promise.all([myDocumentsQuery.refetch(), studentDocumentsQuery.refetch(), checklistQuery.refetch()]);
  }

  async function handleBulkDownload(ids = selectedDocumentIds) {
    const response = await bulkDownloadMutation.mutateAsync(ids);
    openSignedUrl(response.download_url);
  }

  async function handleRateResource(resourceId: string, rating: number) {
    await rateResourceMutation.mutateAsync({ resourceId, rating });
    await Promise.all([resourcesQuery.refetch(), resourceDetailQuery.refetch()]);
  }

  function toggleDocumentSelection(documentId: string) {
    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((item) => item !== documentId)
        : [...current, documentId]
    );
  }

  const loading =
    optionsQuery.isLoading ||
    myDocumentsQuery.isLoading ||
    resourcesQuery.isLoading ||
    (canManageStudentDocs && Boolean(selectedStudentId) && (studentDocumentsQuery.isLoading || checklistQuery.isLoading));

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

      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} />

      <div className="documents-layout">
        <section className="card documents-main-card">
          <div className="documents-toolbar">
            <div className="documents-toolbar__filters">
              {activeTab !== 'resources' && (
                <>
                  <input value={documentSearch} onChange={(event) => setDocumentSearch(event.target.value)} placeholder={t('documents.filters.search')} />
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
                      <option key={mime} value={mime}>{mime}</option>
                    ))}
                  </select>
                  <input type="date" value={documentFromDate} onChange={(event) => setDocumentFromDate(event.target.value)} />
                  <input type="date" value={documentToDate} onChange={(event) => setDocumentToDate(event.target.value)} />
                </>
              )}

              {activeTab === 'resources' && (
                <>
                  <input value={resourceSearch} onChange={(event) => setResourceSearch(event.target.value)} placeholder={t('documents.resources.searchPlaceholder')} />
                  <input value={resourceFilterSubject} onChange={(event) => setResourceFilterSubject(event.target.value)} placeholder={t('documents.resources.subject')} />
                  <input value={resourceFilterLevel} onChange={(event) => setResourceFilterLevel(event.target.value)} placeholder={t('documents.resources.level')} />
                  <select value={resourceFilterType} onChange={(event) => setResourceFilterType(event.target.value)}>
                    <option value="">{t('documents.resources.allTypes')}</option>
                    {RESOURCE_TYPES.map((item) => (
                      <option key={item} value={item}>{t(`documents.resourceTypes.${item}`)}</option>
                    ))}
                  </select>
                  <select value={resourceFilterRating} onChange={(event) => setResourceFilterRating(event.target.value)}>
                    <option value="">{t('documents.resources.allRatings')}</option>
                    {[5, 4, 3].map((rating) => (
                      <option key={rating} value={rating}>{t('documents.resources.ratingAtLeast', { rating })}</option>
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
                    <button type="button" className="btn btn-secondary" onClick={() => void handleBulkDownload()}>
                      {t('documents.bulk.download')}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={() => void handleDeleteDocuments(false)}>
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
                if (dropped) setUploadFile(dropped);
              }}
            >
              <strong>{t('documents.uploadTitle')}</strong>
              <p>{t('documents.uploadSubtitle')}</p>
              <input type="file" onChange={(event) => setUploadFile(event.target.files?.[0] || null)} />

              {activeTab !== 'resources' && (
                <div className="documents-upload-fields">
                  <select value={uploadCategory} onChange={(event) => setUploadCategory(event.target.value)}>
                    {options.categories.map((category) => (
                      <option key={category} value={category}>{t(`documents.categories.${category}`)}</option>
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
                      <option key={item} value={item}>{t(`documents.resourceTypes.${item}`)}</option>
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

              {(uploadDocumentMutation.isPending || uploadResourceMutation.isPending) && (
                <div className="documents-upload-progress">
                  <div style={{ width: `${uploadProgress}%` }} />
                </div>
              )}

              <div className="documents-upload-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void handleUpload()}
                  disabled={!uploadFile || uploadDocumentMutation.isPending || uploadResourceMutation.isPending}
                >
                  {uploadDocumentMutation.isPending || uploadResourceMutation.isPending ? t('documents.uploading') : t('documents.uploadAction')}
                </button>
                {(uploadDocumentMutation.isPending || uploadResourceMutation.isPending) && (
                  <button type="button" className="btn btn-secondary" onClick={() => uploadXhrRef.current?.abort()}>
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
                    <button key={resource.id} type="button" className="documents-resource-card" onClick={() => setSelectedResourceId(resource.id)}>
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
              {resourcesQuery.hasNextPage && (
                <button type="button" className="btn btn-secondary" onClick={() => void resourcesQuery.fetchNextPage()} disabled={resourcesQuery.isFetchingNextPage}>
                  {resourcesQuery.isFetchingNextPage ? t('documents.uploading') : t('documents.resources.loadMore')}
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
                    <input type="checkbox" checked={selectedDocumentIds.includes(item.id)} onChange={() => toggleDocumentSelection(item.id)} />
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
                      <button type="button" className="dropdown-link" onClick={() => void handleDeleteDocuments(false, [item.id])}>
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
              {!previewItem.preview_url && <div className="documents-preview-card__fallback">📄</div>}
              <p>{previewItem.mime_type}</p>
              <p>{humanSize(previewItem.size_bytes)}</p>
              {previewItem.expires_at && (
                <p>{t('documents.expiresAt')}: {formatDate(previewItem.expires_at, i18n.language, { dateStyle: 'medium' })}</p>
              )}
              <button type="button" className="btn btn-primary" onClick={() => openSignedUrl(previewItem.download_url)}>
                {t('documents.download')}
              </button>
            </div>
          )}
        </aside>
      </div>

      {selectedResource && (
        <div className="calendar-modal-shell" role="dialog" aria-modal="true">
          <div className="calendar-modal-card documents-resource-modal">
            <div className="calendar-modal-card__header">
              <h2>{selectedResource.title}</h2>
              <button type="button" className="btn btn-secondary" onClick={() => setSelectedResourceId(null)}>
                {t('app.close')}
              </button>
            </div>

            {resourceDetailQuery.isLoading ? (
              <LoadingState />
            ) : (
              <>
                {selectedResource.preview_url && selectedResource.document && 'mime_type' in selectedResource.document && isImage(selectedResource.document.mime_type) && (
                  <img src={selectedResource.preview_url} alt={selectedResource.title} className="documents-resource-modal__image" />
                )}
                {selectedResource.preview_url && selectedResource.document && 'mime_type' in selectedResource.document && isPdf(selectedResource.document.mime_type) && (
                  <iframe src={selectedResource.preview_url} title={selectedResource.title} className="documents-resource-modal__frame" />
                )}

                <p>{selectedResource.description || '—'}</p>
                <p>{[selectedResource.subject, selectedResource.level].filter(Boolean).join(' · ') || '—'}</p>
                <p>{selectedResource.author || '—'}</p>
                <p>{selectedResource.tags.join(', ') || '—'}</p>
                <p>{t('documents.resources.rating', { rating: selectedResource.avg_rating.toFixed(1), count: selectedResource.rating_count })}</p>
                <p>{t('documents.download', 'Download')} · {selectedResource.download_count}</p>
                <p>{formatDate(selectedResource.created_at, i18n.language, { dateStyle: 'medium' })}</p>
                {selectedResource.document && 'mime_type' in selectedResource.document && (
                  <p>{selectedResource.document.mime_type} · {humanSize(selectedResource.document.size_bytes)}</p>
                )}

                <div className="calendar-modal-card__actions">
                  <button type="button" className="btn btn-primary" onClick={() => openSignedUrl(selectedResource.download_url)}>
                    {t('documents.download')}
                  </button>
                  {selectedResource.can_rate && (
                    <div className="documents-rating-group">
                      {[1, 2, 3, 4, 5].map((rating) => (
                        <button
                          key={rating}
                          type="button"
                          className={`btn ${selectedResource.my_rating === rating ? 'btn-primary' : 'btn-secondary'}`}
                          onClick={() => void handleRateResource(selectedResource.id, rating)}
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
