import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { DocumentFilters } from './DocumentFilters';
import { DocumentList } from './DocumentList';
import { DocumentUpload } from './DocumentUpload';
import { DocumentViewer } from './DocumentViewer';
import { useBulkDeleteDocuments, useBulkDownloadDocuments, useDocumentsOptions, useMyDocuments, useRateResource, useResourceDetail, useResources, useStudentChecklist, useStudentDocuments, useUploadDocument, useUploadResource } from './useDocuments';
import type { DocumentItem, DocumentsTab, ResourceItem } from './documents.service';
import type { DocumentsPageProps } from './documents.types';
import { openSignedUrl } from './documents.utils';

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
  const [resourceType, setResourceType] = useState<'lesson_plan' | 'worksheet' | 'presentation' | 'exam_template' | 'reference'>('lesson_plan');
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
  const resourcesQuery = useResources({ q: resourceSearch || undefined, type: resourceFilterType || undefined, subject: resourceFilterSubject || undefined, level: resourceFilterLevel || undefined, rating: resourceFilterRating || undefined });
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
  const resources: ResourceItem[] = useMemo(() => resourcesQuery.data?.pages.flatMap((page) => page.data) ?? [], [resourcesQuery.data]);
  const selectedResource = resourceDetailQuery.data ?? resources.find((resource) => resource.id === selectedResourceId) ?? null;
  const dismissibleError = useDismissibleError(useMemo(() => toBannerError(optionsQuery.error ?? myDocumentsQuery.error ?? studentDocumentsQuery.error ?? checklistQuery.error ?? resourcesQuery.error ?? resourceDetailQuery.error ?? uploadDocumentMutation.error ?? uploadResourceMutation.error ?? deleteDocumentsMutation.error ?? bulkDownloadMutation.error ?? rateResourceMutation.error, t('app.error')), [bulkDownloadMutation.error, checklistQuery.error, deleteDocumentsMutation.error, myDocumentsQuery.error, optionsQuery.error, rateResourceMutation.error, resourceDetailQuery.error, resourcesQuery.error, studentDocumentsQuery.error, t, uploadDocumentMutation.error, uploadResourceMutation.error]));

  useEffect(() => {
    if (!selectedStudentId && options.students.length > 0) setSelectedStudentId(options.students[0].id);
    if (options.categories.length > 0 && !uploadCategory) setUploadCategory(options.categories[0]);
  }, [options.categories, options.students, selectedStudentId, uploadCategory]);

  const filteredDocuments = useMemo(() => {
    const items = activeTab === 'student' ? studentDocuments : documents;
    return items.filter((item) => {
      if (documentCategoryFilter && item.category !== documentCategoryFilter) return false;
      if (documentTypeFilter && item.mime_type !== documentTypeFilter) return false;
      if (documentSearch) {
        const search = documentSearch.toLowerCase();
        if (!item.original_filename.toLowerCase().includes(search) && !item.category.toLowerCase().includes(search)) return false;
      }
      if (documentFromDate && item.created_at.slice(0, 10) < documentFromDate) return false;
      if (documentToDate && item.created_at.slice(0, 10) > documentToDate) return false;
      return true;
    });
  }, [activeTab, documentCategoryFilter, documentFromDate, documentSearch, documentToDate, documentTypeFilter, documents, studentDocuments]);

  const documentMimeOptions = useMemo(() => Array.from(new Set([...(documents ?? []), ...(studentDocuments ?? [])].map((item) => item.mime_type))).sort(), [documents, studentDocuments]);
  const loading = optionsQuery.isLoading || myDocumentsQuery.isLoading || resourcesQuery.isLoading || (canManageStudentDocs && Boolean(selectedStudentId) && (studentDocumentsQuery.isLoading || checklistQuery.isLoading));
  if (loading) return <LoadingState />;

  async function handleUpload() {
    if (!uploadFile) return;
    if (activeTab === 'resources') {
      await uploadResourceMutation.mutateAsync({ payload: { file: uploadFile, title: resourceTitle || uploadFile.name, description: resourceDescription, subject: resourceSubject, level: resourceLevel, type: resourceType, tags: resourceTags, language: i18n.language || 'fr' }, onProgress: setUploadProgress, onRequestCreated: (xhr) => { uploadXhrRef.current = xhr; } });
      setResourceFormOpen(false);
      await resourcesQuery.refetch();
    } else {
      await uploadDocumentMutation.mutateAsync({ payload: { file: uploadFile, category: uploadCategory, linkedStudentId: activeTab === 'student' ? selectedStudentId : undefined, expiresAt: uploadExpiry || undefined, language: i18n.language || 'fr' }, onProgress: setUploadProgress, onRequestCreated: (xhr) => { uploadXhrRef.current = xhr; } });
      await Promise.all([myDocumentsQuery.refetch(), studentDocumentsQuery.refetch(), checklistQuery.refetch()]);
    }
    uploadXhrRef.current = null;
    setUploadFile(null);
    setUploadExpiry('');
    setUploadProgress(0);
  }

  async function handleDeleteDocuments(hard = false, ids = selectedDocumentIds) {
    await deleteDocumentsMutation.mutateAsync({ documentIds: ids, hard, useBulkEndpoint: !hard && user?.role === 'ADM' && ids.length > 1 });
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

  return (
    <div className="page documents-page">
      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} />
      <section className="card documents-main-card">
        <DocumentFilters
          activeTab={activeTab}
          canUploadResources={canUploadResources}
          documentCategoryFilter={documentCategoryFilter}
          documentFromDate={documentFromDate}
          documentMimeOptions={documentMimeOptions}
          documentSearch={documentSearch}
          documentToDate={documentToDate}
          documentTypeFilter={documentTypeFilter}
          optionsCategories={options.categories}
          resourceFilterLevel={resourceFilterLevel}
          resourceFilterRating={resourceFilterRating}
          resourceFilterSubject={resourceFilterSubject}
          resourceFilterType={resourceFilterType}
          resourceFormOpen={resourceFormOpen}
          resourceSearch={resourceSearch}
          selectedDocumentCount={selectedDocumentIds.length}
          showHardDelete={['ADM', 'DIR'].includes(user?.role || '')}
          viewMode={viewMode}
          onBulkDelete={() => void handleDeleteDocuments(false)}
          onBulkDownload={() => void handleBulkDownload()}
          onChangeActiveTab={(tab) => { setActiveTab(tab); setSelectedDocumentIds([]); }}
          onChangeDocumentCategoryFilter={setDocumentCategoryFilter}
          onChangeDocumentFromDate={setDocumentFromDate}
          onChangeDocumentSearch={setDocumentSearch}
          onChangeDocumentToDate={setDocumentToDate}
          onChangeDocumentTypeFilter={setDocumentTypeFilter}
          onChangeResourceFilterLevel={setResourceFilterLevel}
          onChangeResourceFilterRating={setResourceFilterRating}
          onChangeResourceFilterSubject={setResourceFilterSubject}
          onChangeResourceFilterType={setResourceFilterType}
          onChangeResourceSearch={setResourceSearch}
          onHardDelete={() => void handleDeleteDocuments(true)}
          onToggleResourceForm={() => setResourceFormOpen((open) => !open)}
          onToggleViewMode={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
        />

        <DocumentUpload
          activeTab={activeTab}
          canUploadDocuments={canUploadDocuments}
          canUploadResources={canUploadResources}
          isPending={uploadDocumentMutation.isPending || uploadResourceMutation.isPending}
          options={options}
          resourceDescription={resourceDescription}
          resourceFormOpen={resourceFormOpen}
          resourceLevel={resourceLevel}
          resourceSubject={resourceSubject}
          resourceTags={resourceTags}
          resourceTitle={resourceTitle}
          resourceType={resourceType}
          uploadCategory={uploadCategory}
          uploadExpiry={uploadExpiry}
          uploadFile={uploadFile}
          uploadProgress={uploadProgress}
          onAbort={() => uploadXhrRef.current?.abort()}
          onChangeResourceDescription={setResourceDescription}
          onChangeResourceLevel={setResourceLevel}
          onChangeResourceSubject={setResourceSubject}
          onChangeResourceTags={setResourceTags}
          onChangeResourceTitle={setResourceTitle}
          onChangeResourceType={setResourceType}
          onChangeUploadCategory={setUploadCategory}
          onChangeUploadExpiry={setUploadExpiry}
          onDropFile={setUploadFile}
          onSubmit={() => void handleUpload()}
        />

        <div className="documents-layout">
          <section className="card documents-main-card">
            <DocumentList
              activeTab={activeTab}
              checklist={checklist}
              filteredDocuments={filteredDocuments}
              options={options}
              resources={resources}
              selectedDocumentIds={selectedDocumentIds}
              selectedStudentId={selectedStudentId}
              viewMode={viewMode}
              onChangeSelectedStudentId={setSelectedStudentId}
              onDeleteDocument={(documentId) => void handleDeleteDocuments(false, [documentId])}
              onDownloadDocument={openSignedUrl}
              onFetchNextPage={() => void resourcesQuery.fetchNextPage()}
              onPreviewDocument={setPreviewItem}
              onSelectResource={setSelectedResourceId}
              onToggleSelection={(documentId) => setSelectedDocumentIds((current) => current.includes(documentId) ? current.filter((item) => item !== documentId) : [...current, documentId])}
              resourcesHasNextPage={Boolean(resourcesQuery.hasNextPage)}
              resourcesIsFetchingNextPage={resourcesQuery.isFetchingNextPage}
            />
          </section>

          <DocumentViewer
            isResourceLoading={resourceDetailQuery.isLoading}
            previewItem={previewItem}
            selectedResource={selectedResource}
            onCloseResource={() => setSelectedResourceId(null)}
            onDownload={openSignedUrl}
            onRateResource={(resourceId, rating) => void handleRateResource(resourceId, rating)}
          />
        </div>
      </section>
    </div>
  );
}
