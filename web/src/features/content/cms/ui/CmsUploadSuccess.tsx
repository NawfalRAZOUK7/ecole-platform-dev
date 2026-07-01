import { useTranslation } from 'react-i18next';

export interface CmsUploadSuccessProps {
  createdId: string | null;
  onBackToList: () => void;
  onEditContent: () => void;
  onUploadAnother: () => void;
}

export function CmsUploadSuccess({
  createdId,
  onBackToList,
  onEditContent,
  onUploadAnother,
}: CmsUploadSuccessProps) {
  const { t } = useTranslation();

  return (
    <div className="card" style={{ padding: 24, maxWidth: 600 }}>
      <h1 className="page-title">{t('cms.upload.success')}</h1>
      <p>{t('cms.upload.successMessage')}</p>
      <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
        {createdId ? (
          <button className="btn btn-primary" onClick={onEditContent}>
            {t('cms.upload.editContent')}
          </button>
        ) : null}
        <button className="btn" onClick={onUploadAnother}>
          {t('cms.upload.uploadAnother')}
        </button>
        <button className="btn" onClick={onBackToList}>
          {t('cms.upload.backToList')}
        </button>
      </div>
    </div>
  );
}
