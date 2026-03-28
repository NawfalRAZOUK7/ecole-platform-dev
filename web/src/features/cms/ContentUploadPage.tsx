import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import {
  useCreateCmsContent,
  useUploadCmsContentAsset,
} from './useCms';

const CONTENT_TYPES = ['video', 'pdf', 'audio', 'interactive'];
const LEVELS = ['maternelle', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];
const SUBJECTS = ['math', 'french', 'arabic', 'science', 'history', 'geography', 'english', 'islamic_studies', 'art', 'sport'];

const ACCEPT_MAP: Record<string, string> = {
  video: '.mp4,.webm',
  pdf: '.pdf',
  audio: '.mp3,.wav,.ogg',
  interactive: '*',
};

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
  const [bulkResults, setBulkResults] = useState<Array<{ name: string; ok: boolean; error?: string }>>([]);

  async function uploadFileWithProgress(contentId: string, file: File) {
    await uploadContentAssetMutation.mutateAsync({
      contentId,
      file,
      onProgress: setProgress,
    });
  }

  async function handleSubmit(event: FormEvent) {
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

      if (mainFile) {
        await uploadFileWithProgress(created.id, mainFile);
      }

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
    const results: Array<{ name: string; ok: boolean; error?: string }> = [];

    for (const file of bulkFiles) {
      try {
        const inferredType = file.type.startsWith('video/')
          ? 'video'
          : file.type === 'application/pdf'
            ? 'pdf'
            : file.type.startsWith('audio/')
              ? 'audio'
              : 'interactive';

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
        results.push({
          name: file.name,
          ok: false,
          error: bulkError instanceof Error ? bulkError.message : t('app.error'),
        });
      }
    }

    setBulkResults(results);
    setUploading(false);
  }

  if (success) {
    return (
      <div className="page">
        <div className="card" style={{ padding: 24, maxWidth: 600 }}>
          <h1 className="page-title">{t('cms.upload.success')}</h1>
          <p>{t('cms.upload.successMessage')}</p>
          <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
            {createdId ? (
              <button className="btn btn-primary" onClick={() => navigate(`/cms/content/${createdId}/edit`)}>
                {t('cms.upload.editContent')}
              </button>
            ) : null}
            <button
              className="btn"
              onClick={() => {
                setSuccess(false);
                setTitle('');
                setDescription('');
                setMainFile(null);
                setThumbnailFile(null);
                setCreatedId(null);
              }}
            >
              {t('cms.upload.uploadAnother')}
            </button>
            <button className="btn" onClick={() => navigate('/cms')}>
              {t('cms.upload.backToList')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('cms.upload.title')}</h1>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <button className={`btn ${!bulkMode ? 'btn-primary' : ''}`} onClick={() => setBulkMode(false)}>
          {t('cms.upload.singleMode')}
        </button>
        <button className={`btn ${bulkMode ? 'btn-primary' : ''}`} onClick={() => setBulkMode(true)}>
          {t('cms.upload.bulkMode')}
        </button>
      </div>

      {bulkMode ? (
        <div className="card" style={{ padding: 24 }}>
          <h2 style={{ marginTop: 0 }}>{t('cms.upload.bulkTitle')}</h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>{t('cms.upload.bulkHint')}</p>

          <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
            <select className="filter-select" value={levelBand} onChange={(event) => setLevelBand(event.target.value)}>
              <option value="">{t('cms.content.allLevels')}</option>
              {LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}
            </select>
            <select className="filter-select" value={subject} onChange={(event) => setSubject(event.target.value)}>
              <option value="">{t('cms.content.allSubjects')}</option>
              {SUBJECTS.map((currentSubject) => (
                <option key={currentSubject} value={currentSubject}>
                  {t(`cms.subjects.${currentSubject}`, currentSubject)}
                </option>
              ))}
            </select>
            <select className="filter-select" value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option value="fr">Francais</option>
              <option value="ar">Arabe</option>
              <option value="en">English</option>
            </select>
          </div>

          <input
            type="file"
            multiple
            onChange={(event) => setBulkFiles(Array.from(event.target.files || []))}
            style={{ marginBottom: 12 }}
          />

          {bulkFiles.length > 0 ? (
            <p style={{ fontSize: 13 }}>{t('cms.upload.bulkCount', { count: bulkFiles.length })}</p>
          ) : null}

          <button className="btn btn-primary" onClick={handleBulkUpload} disabled={uploading || bulkFiles.length === 0}>
            {uploading ? t('cms.upload.uploading') : t('cms.upload.bulkStart')}
          </button>

          {uploading ? (
            <div style={{ marginTop: 12 }}>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
              </div>
            </div>
          ) : null}

          {bulkResults.length > 0 ? (
            <div style={{ marginTop: 16 }}>
              <h3>{t('cms.upload.bulkResults')}</h3>
              {bulkResults.map((result, index) => (
                <div
                  key={index}
                  style={{
                    fontSize: 13,
                    padding: '4px 0',
                    color: result.ok ? 'var(--color-success)' : 'var(--color-danger)',
                  }}
                >
                  {result.name}: {result.ok ? t('cms.upload.bulkOk') : result.error}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="card" style={{ padding: 24 }}>
          <div className="form-field">
            <label>{t('cms.upload.titleLabel')}</label>
            <input
              type="text"
              required
              maxLength={300}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder={t('cms.upload.titlePlaceholder')}
            />
          </div>

          <div className="form-field">
            <label>{t('cms.upload.description')}</label>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={3}
              placeholder={t('cms.upload.descriptionPlaceholder')}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-field">
              <label>{t('cms.upload.contentType')}</label>
              <select required value={contentType} onChange={(event) => setContentType(event.target.value)}>
                {CONTENT_TYPES.map((currentType) => (
                  <option key={currentType} value={currentType}>
                    {t(`cms.contentTypes.${currentType}`, currentType)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>{t('cms.upload.level')}</label>
              <select value={levelBand} onChange={(event) => setLevelBand(event.target.value)}>
                <option value="">{t('cms.content.allLevels')}</option>
                {LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}
              </select>
            </div>

            <div className="form-field">
              <label>{t('cms.upload.subject')}</label>
              <select value={subject} onChange={(event) => setSubject(event.target.value)}>
                <option value="">{t('cms.content.allSubjects')}</option>
                {SUBJECTS.map((currentSubject) => (
                  <option key={currentSubject} value={currentSubject}>
                    {t(`cms.subjects.${currentSubject}`, currentSubject)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>{t('cms.upload.language')}</label>
              <select value={language} onChange={(event) => setLanguage(event.target.value)}>
                <option value="fr">Francais</option>
                <option value="ar">Arabe</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>

          <div className="form-field">
            <label>{t('cms.upload.mainFile')}</label>
            <input
              type="file"
              accept={ACCEPT_MAP[contentType] || '*'}
              onChange={(event) => setMainFile(event.target.files?.[0] || null)}
            />
            {mainFile && contentType === 'video' && mainFile.size > 100 * 1024 * 1024 ? (
              <p style={{ fontSize: 12, color: 'var(--color-warning)', marginTop: 4 }}>
                {t('cms.upload.largeFileWarning')}
              </p>
            ) : null}
          </div>

          <div className="form-field">
            <label>{t('cms.upload.thumbnail')}</label>
            <input
              type="file"
              accept="image/*"
              onChange={(event) => setThumbnailFile(event.target.files?.[0] || null)}
            />
          </div>

          {uploading ? (
            <div style={{ marginBottom: 12 }}>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
              </div>
              <p style={{ fontSize: 12, textAlign: 'center', marginTop: 4 }}>{progress}%</p>
            </div>
          ) : null}

          <div style={{ display: 'flex', gap: 12 }}>
            <button type="submit" className="btn btn-primary" disabled={uploading || !title}>
              {uploading ? t('cms.upload.uploading') : t('cms.upload.submit')}
            </button>
            <button type="button" className="btn" onClick={() => navigate('/cms')}>
              {t('app.cancel')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
