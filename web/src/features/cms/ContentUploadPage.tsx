import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { CmsBulkUploadForm } from './CmsBulkUploadForm';
import { CmsSingleUploadForm } from './CmsSingleUploadForm';
import { CmsUploadSuccess } from './CmsUploadSuccess';
import type { BulkUploadResult } from './content-upload.types';
import { useCreateCmsContent, useUploadCmsContentAsset } from './useCms';

export function CmsContentUploadPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const createContentMutation = useCreateCmsContent();
  const uploadContentAssetMutation = useUploadCmsContentAsset();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contentType, setContentType] = useState('pdf');
  const [levelBand, setLevelBand] = useState('');
  const [subject, setSubject] = useState('');
  const [language, setLanguage] = useState('fr');
  const [mainFile, setMainFile] = useState<File | null>(null);
  const [thumbnailFile, setThumbnailFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [createdId, setCreatedId] = useState<string | null>(null);
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkFiles, setBulkFiles] = useState<File[]>([]);
  const [bulkResults, setBulkResults] = useState<BulkUploadResult[]>([]);

  async function uploadFileWithProgress(contentId: string, file: File) {
    await uploadContentAssetMutation.mutateAsync({ contentId, file, onProgress: setProgress });
  }

  function resetSingleUpload() {
    setSuccess(false);
    setTitle('');
    setDescription('');
    setMainFile(null);
    setThumbnailFile(null);
    setCreatedId(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      const created = await createContentMutation.mutateAsync({
        title,
        content_type: contentType,
        level_band: levelBand || undefined,
        language: language || undefined,
        subject: subject || undefined,
        description: description || undefined,
        status: 'draft',
      });
      setCreatedId(created.id);

      if (mainFile) await uploadFileWithProgress(created.id, mainFile);
      if (thumbnailFile) {
        setProgress(0);
        await uploadFileWithProgress(created.id, thumbnailFile);
      }

      setSuccess(true);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : t('app.error'));
    } finally {
      setUploading(false);
    }
  }

  async function handleBulkUpload() {
    if (bulkFiles.length === 0) return;

    setUploading(true);
    setError(null);
    const results: BulkUploadResult[] = [];

    for (const file of bulkFiles) {
      try {
        const inferredType = file.type.startsWith('video/') ? 'video' : file.type === 'application/pdf' ? 'pdf' : file.type.startsWith('audio/') ? 'audio' : 'interactive';
        const baseName = file.name.replace(/\.[^/.]+$/, '');
        const created = await createContentMutation.mutateAsync({
          title: baseName,
          content_type: inferredType,
          level_band: levelBand || undefined,
          language: language || undefined,
          subject: subject || undefined,
          status: 'draft',
        });
        await uploadFileWithProgress(created.id, file);
        results.push({ name: file.name, ok: true });
      } catch (bulkError) {
        results.push({ name: file.name, ok: false, error: bulkError instanceof Error ? bulkError.message : t('app.error') });
      }
    }

    setBulkResults(results);
    setUploading(false);
  }

  if (success) {
    return (
      <div className="page">
        <CmsUploadSuccess
          createdId={createdId}
          onBackToList={() => navigate('/cms')}
          onEditContent={() => navigate(`/cms/content/${createdId}/edit`)}
          onUploadAnother={resetSingleUpload}
        />
      </div>
    );
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('cms.upload.title')}</h1>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <button type="button" className={`btn ${!bulkMode ? 'btn-primary' : ''}`} onClick={() => setBulkMode(false)}>
          {t('cms.upload.singleMode')}
        </button>
        <button type="button" className={`btn ${bulkMode ? 'btn-primary' : ''}`} onClick={() => setBulkMode(true)}>
          {t('cms.upload.bulkMode')}
        </button>
      </div>

      {bulkMode ? (
        <CmsBulkUploadForm
          bulkFiles={bulkFiles}
          bulkResults={bulkResults}
          language={language}
          levelBand={levelBand}
          progress={progress}
          subject={subject}
          uploading={uploading}
          onBulkUpload={() => void handleBulkUpload()}
          onChangeBulkFiles={setBulkFiles}
          onChangeLanguage={setLanguage}
          onChangeLevelBand={setLevelBand}
          onChangeSubject={setSubject}
        />
      ) : (
        <CmsSingleUploadForm
          contentType={contentType}
          description={description}
          language={language}
          levelBand={levelBand}
          mainFile={mainFile}
          progress={progress}
          subject={subject}
          thumbnailFile={thumbnailFile}
          title={title}
          uploading={uploading}
          onCancel={() => navigate('/cms')}
          onChangeContentType={setContentType}
          onChangeDescription={setDescription}
          onChangeLanguage={setLanguage}
          onChangeLevelBand={setLevelBand}
          onChangeMainFile={setMainFile}
          onChangeSubject={setSubject}
          onChangeThumbnailFile={setThumbnailFile}
          onChangeTitle={setTitle}
          onSubmit={(event) => void handleSubmit(event)}
        />
      )}
    </div>
  );
}
