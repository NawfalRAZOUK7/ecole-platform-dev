import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import type { ChecklistItem, DocumentItem, DocumentsOptionsPayload, DocumentsTab, ResourceItem } from './documents.service';
import type { DocumentViewMode } from './documents.types';
import { DocumentGrid } from './DocumentGrid';
import { ResourceGrid } from './ResourceGrid';

interface DocumentListProps {
  activeTab: DocumentsTab;
  checklist: ChecklistItem[];
  filteredDocuments: DocumentItem[];
  options: DocumentsOptionsPayload;
  resources: ResourceItem[];
  selectedDocumentIds: string[];
  selectedStudentId: string;
  viewMode: DocumentViewMode;
  onChangeSelectedStudentId: (value: string) => void;
  onDeleteDocument: (documentId: string) => void;
  onDownloadDocument: (url: string | null) => void;
  onFetchNextPage: () => void;
  onPreviewDocument: (item: DocumentItem) => void;
  onSelectResource: (resourceId: string) => void;
  onToggleSelection: (documentId: string) => void;
  resourcesHasNextPage: boolean;
  resourcesIsFetchingNextPage: boolean;
}

export function DocumentList({
  activeTab,
  checklist,
  filteredDocuments,
  options,
  resources,
  selectedDocumentIds,
  selectedStudentId,
  viewMode,
  onChangeSelectedStudentId,
  onDeleteDocument,
  onDownloadDocument,
  onFetchNextPage,
  onPreviewDocument,
  onSelectResource,
  onToggleSelection,
  resourcesHasNextPage,
  resourcesIsFetchingNextPage,
}: DocumentListProps) {
  const { t } = useTranslation();

  return (
    <>
      {activeTab === 'student' && options.students.length > 0 && (
        <div className="documents-student-header">
          <label className="form-field">
            <span>{t('documents.studentSelector')}</span>
            <select value={selectedStudentId} onChange={(event) => onChangeSelectedStudentId(event.target.value)}>
              {options.students.map((student) => <option key={student.id} value={student.id}>{student.full_name}</option>)}
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

      {activeTab === 'resources' ? (
        <ResourceGrid
          hasNextPage={resourcesHasNextPage}
          isFetchingNextPage={resourcesIsFetchingNextPage}
          onFetchNextPage={onFetchNextPage}
          onSelectResource={onSelectResource}
          resources={resources}
        />
      ) : filteredDocuments.length === 0 ? (
        <EmptyState message={t('documents.empty')} icon="🗂️" />
      ) : (
        <DocumentGrid
          documents={filteredDocuments}
          onDelete={onDeleteDocument}
          onDownload={onDownloadDocument}
          onPreview={onPreviewDocument}
          onToggleSelection={onToggleSelection}
          selectedDocumentIds={selectedDocumentIds}
          viewMode={viewMode}
        />
      )}
    </>
  );
}
