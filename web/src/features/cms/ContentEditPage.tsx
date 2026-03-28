import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import {
  useCmsContentItem,
  useDeleteCmsContent,
  useUpdateCmsContent,
  useUploadCmsContentAsset,
} from './useCms';

const CONTENT_TYPES = ['video', 'pdf', 'audio', 'interactive'];
const LEVELS = ['maternelle', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];
const SUBJECTS = ['math', 'french', 'arabic', 'science', 'history', 'geography', 'english', 'islamic_studies', 'art', 'sport'];

export function CmsContentEditPage() {
  const { contentId } = useParams<{ contentId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const contentQuery = useCmsContentItem(contentId);
  const updateContentMutation = useUpdateCmsContent();
  const deleteContentMutation = useDeleteCmsContent();
  const uploadContentAssetMutation = useUploadCmsContentAsset();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contentType, setContentType] = useState('');
  const [levelBand, setLevelBand] = useState('');
  const [subject, setSubject] = useState('');
  const [language, setLanguage] = useState('');
  const [status, setStatus] = useState('');
  const [newFile, setNewFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!contentQuery.data) return;
    setTitle(contentQuery.data.title);
    setDescription(contentQuery.data.description || '');
    setContentType(contentQuery.data.content_type);
    setLevelBand(contentQuery.data.level_band || '');
    setSubject(contentQuery.data.subject || '');
    setLanguage(contentQuery.data.language || '');
    setStatus(contentQuery.data.status);
  }, [contentQuery.data]);

  if (contentQuery.isLoading) {
    return <LoadingState />;
  }

  if (!contentQuery.data) {
    return (
      <div className="page">
        <ErrorBanner error={error || (contentQuery.error instanceof Error ? contentQuery.error.message : t('errors.not_found'))} />
        <button className="btn" onClick={() => navigate('/cms')}>{t('app.back')}</button>
      </div>
    );
  }

  const saving =
    updateContentMutation.isPending ||
    deleteContentMutation.isPending ||
    uploadContentAssetMutation.isPending;

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSaved(false);

    try {
      await updateContentMutation.mutateAsync({
        contentId: contentId!,
        payload: {
          title,
          content_type: contentType,
          level_band: levelBand || null,
          language: language || null,
          subject: subject || null,
          description: description || null,
          status,
        },
      });

      if (newFile) {
        setUploadProgress(0);
        await uploadContentAssetMutation.mutateAsync({
          contentId: contentId!,
          file: newFile,
          onProgress: setUploadProgress,
        });
        setNewFile(null);
      }

      setSaved(true);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : t('app.error'));
    }
  }

  async function handleArchive() {
    setError(null);
    try {
      await deleteContentMutation.mutateAsync(contentId!);
      navigate('/cms');
    } catch (archiveError) {
      setError(archiveError instanceof Error ? archiveError.message : t('app.error'));
    }
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 className="page-title">{t('cms.edit.title')}</h1>
        <button className="btn" onClick={() => navigate('/cms')}>{t('app.back')}</button>
      </div>

      <ErrorBanner
        error={error || (contentQuery.error instanceof Error ? contentQuery.error.message : null)}
        onDismiss={() => setError(null)}
      />
      {saved ? <div className="alert alert-success" style={{ marginBottom: 16, padding: 12, borderRadius: 8 }}>{t('app.saved')}</div> : null}

      <form onSubmit={handleSave} className="card" style={{ padding: 24 }}>
        <div className="form-field">
          <label>{t('cms.upload.titleLabel')}</label>
          <input type="text" value={title} onChange={(event) => setTitle(event.target.value)} required />
        </div>

        <div className="form-field">
          <label>{t('cms.upload.description')}</label>
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={4} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
          <div className="form-field">
            <label>{t('cms.upload.contentType')}</label>
            <select value={contentType} onChange={(event) => setContentType(event.target.value)}>
              {CONTENT_TYPES.map((currentType) => (
                <option key={currentType} value={currentType}>{t(`cms.contentTypes.${currentType}`, currentType)}</option>
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
                <option key={currentSubject} value={currentSubject}>{t(`cms.subjects.${currentSubject}`, currentSubject)}</option>
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
          <label>{t('cms.edit.status')}</label>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="draft">{t('cms.statuses.draft')}</option>
            <option value="published">{t('cms.statuses.published')}</option>
            <option value="archived">{t('cms.statuses.archived')}</option>
          </select>
        </div>

        <div className="form-field">
          <label>{t('cms.edit.replaceFile')}</label>
          <input type="file" onChange={(event) => setNewFile(event.target.files?.[0] || null)} />
        </div>

        {saving && newFile ? (
          <div style={{ marginBottom: 12 }}>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        ) : null}

        {contentQuery.data.origin === 'PROMOTED' ? (
          <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
            {t('cms.edit.promotedNote')}
          </p>
        ) : null}

        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? t('app.loading') : t('app.save')}
          </button>
          {status !== 'archived' ? (
            <button type="button" className="btn btn-danger" onClick={() => void handleArchive()}>
              {t('cms.edit.archive')}
            </button>
          ) : null}
        </div>
      </form>
    </div>
  );
}
