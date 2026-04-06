import { useTranslation } from 'react-i18next';
import type { DocumentsOptionsPayload, DocumentsTab } from './documents.service';
import { RESOURCE_TYPES } from './documents.types';
import { humanSize } from './documents.utils';

interface DocumentUploadProps {
  activeTab: DocumentsTab;
  canUploadDocuments: boolean;
  canUploadResources: boolean;
  isPending: boolean;
  options: DocumentsOptionsPayload;
  resourceDescription: string;
  resourceFormOpen: boolean;
  resourceLevel: string;
  resourceSubject: string;
  resourceTags: string;
  resourceTitle: string;
  resourceType: (typeof RESOURCE_TYPES)[number];
  uploadCategory: string;
  uploadExpiry: string;
  uploadFile: File | null;
  uploadProgress: number;
  onAbort: () => void;
  onChangeResourceDescription: (value: string) => void;
  onChangeResourceLevel: (value: string) => void;
  onChangeResourceSubject: (value: string) => void;
  onChangeResourceTags: (value: string) => void;
  onChangeResourceTitle: (value: string) => void;
  onChangeResourceType: (value: (typeof RESOURCE_TYPES)[number]) => void;
  onChangeUploadCategory: (value: string) => void;
  onChangeUploadExpiry: (value: string) => void;
  onDropFile: (file: File | null) => void;
  onSubmit: () => void;
}

export function DocumentUpload({
  activeTab,
  canUploadDocuments,
  canUploadResources,
  isPending,
  options,
  resourceDescription,
  resourceFormOpen,
  resourceLevel,
  resourceSubject,
  resourceTags,
  resourceTitle,
  resourceType,
  uploadCategory,
  uploadExpiry,
  uploadFile,
  uploadProgress,
  onAbort,
  onChangeResourceDescription,
  onChangeResourceLevel,
  onChangeResourceSubject,
  onChangeResourceTags,
  onChangeResourceTitle,
  onChangeResourceType,
  onChangeUploadCategory,
  onChangeUploadExpiry,
  onDropFile,
  onSubmit,
}: DocumentUploadProps) {
  const { t } = useTranslation();
  const shouldShow = (activeTab !== 'resources' && canUploadDocuments) || (activeTab === 'resources' && canUploadResources && resourceFormOpen);

  if (!shouldShow) {
    return null;
  }

  return (
    <div className="documents-upload-dropzone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); onDropFile(event.dataTransfer.files?.[0] || null); }}>
      <strong>{t('documents.uploadTitle')}</strong>
      <p>{t('documents.uploadSubtitle')}</p>
      <input type="file" onChange={(event) => onDropFile(event.target.files?.[0] || null)} />

      {activeTab !== 'resources' ? (
        <div className="documents-upload-fields">
          <select value={uploadCategory} onChange={(event) => onChangeUploadCategory(event.target.value)}>
            {options.categories.map((category) => <option key={category} value={category}>{t(`documents.categories.${category}`)}</option>)}
          </select>
          <input type="date" value={uploadExpiry} onChange={(event) => onChangeUploadExpiry(event.target.value)} />
        </div>
      ) : (
        <div className="documents-upload-fields documents-upload-fields--resource">
          <input value={resourceTitle} onChange={(event) => onChangeResourceTitle(event.target.value)} placeholder={t('documents.resources.title')} />
          <input value={resourceSubject} onChange={(event) => onChangeResourceSubject(event.target.value)} placeholder={t('documents.resources.subject')} />
          <input value={resourceLevel} onChange={(event) => onChangeResourceLevel(event.target.value)} placeholder={t('documents.resources.level')} />
          <select value={resourceType} onChange={(event) => onChangeResourceType(event.target.value as (typeof RESOURCE_TYPES)[number])}>
            {RESOURCE_TYPES.map((item) => <option key={item} value={item}>{t(`documents.resourceTypes.${item}`)}</option>)}
          </select>
          <input value={resourceTags} onChange={(event) => onChangeResourceTags(event.target.value)} placeholder={t('documents.resources.tags')} />
          <textarea value={resourceDescription} onChange={(event) => onChangeResourceDescription(event.target.value)} placeholder={t('documents.resources.description')} />
        </div>
      )}

      {uploadFile && <div className="documents-upload-summary"><span>{uploadFile.name}</span><span>{humanSize(uploadFile.size)}</span></div>}
      {isPending && <div className="documents-upload-progress"><div style={{ width: `${uploadProgress}%` }} /></div>}
      <div className="documents-upload-actions">
        <button type="button" className="btn btn-primary" onClick={onSubmit} disabled={!uploadFile || isPending}>{isPending ? t('documents.uploading') : t('documents.uploadAction')}</button>
        {isPending && <button type="button" className="btn btn-secondary" onClick={onAbort}>{t('documents.cancelUpload')}</button>}
      </div>
    </div>
  );
}
