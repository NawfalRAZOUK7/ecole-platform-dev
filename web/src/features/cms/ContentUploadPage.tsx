/**
 * CMS Content Upload — create new platform content with file upload.
 *
 * Phase 10A — form: title, description, content_type, level_band, subject,
 * language, thumbnail + main file with progress bar.
 * Also supports bulk upload (multiple files → multiple content items).
 */

import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, getAccessToken } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';

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

  // Bulk upload
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkFiles, setBulkFiles] = useState<File[]>([]);
  const [bulkResults, setBulkResults] = useState<Array<{ name: string; ok: boolean; error?: string }>>([]);

  async function uploadFileWithProgress(contentId: string, file: File): Promise<void> {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `/api/v1/content-items/${contentId}/assets`);

      const token = getAccessToken();
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          setProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve();
        else reject(new Error(`Upload failed: ${xhr.status}`));
      };

      xhr.onerror = () => reject(new Error('Network error'));
      xhr.send(formData);
    });
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      // 1. Create content item
      const resp = await api.post<{ id: string }>('/cms/content', {
        title,
        content_type: contentType,
        level_band: levelBand || undefined,
        language: language || undefined,
        subject: subject || undefined,
        description: description || undefined,
        status: 'draft',
      });
      const contentId = resp.data.id;
      setCreatedId(contentId);

      // 2. Upload main file
      if (mainFile) {
        await uploadFileWithProgress(contentId, mainFile);
      }

      // 3. Upload thumbnail
      if (thumbnailFile) {
        setProgress(0);
        await uploadFileWithProgress(contentId, thumbnailFile);
      }

      setSuccess(true);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setUploading(false);
    }
  }

  async function handleBulkUpload() {
    if (bulkFiles.length === 0) return;
    setUploading(true);
    setError(null);
    const results: typeof bulkResults = [];

    for (const file of bulkFiles) {
      try {
        const inferredType = file.type.startsWith('video/') ? 'video'
          : file.type === 'application/pdf' ? 'pdf'
          : file.type.startsWith('audio/') ? 'audio'
          : 'interactive';

        const baseName = file.name.replace(/\.[^/.]+$/, '');
        const resp = await api.post<{ id: string }>('/cms/content', {
          title: baseName,
          content_type: inferredType,
          level_band: levelBand || undefined,
          language: language || undefined,
          subject: subject || undefined,
          status: 'draft',
        });
        await uploadFileWithProgress(resp.data.id, file);
        results.push({ name: file.name, ok: true });
      } catch (err) {
        results.push({
          name: file.name,
          ok: false,
          error: err instanceof ApiClientError ? err.message : String(err),
        });
      }
    }

    setBulkResults(results);
    setUploading(false);
  }

  if (success) {
    return (
      <div className="page">
        <h1 className="page-title">{t('cms.upload.successTitle')}</h1>
        <div className="card" style={{ padding: 24, textAlign: 'center' }}>
          <p style={{ fontSize: 16, marginBottom: 16 }}>{t('cms.upload.successMessage')}</p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            {createdId && (
              <button className="btn btn-primary" onClick={() => navigate(`/cms/content/${createdId}/edit`)}>
                {t('cms.upload.editContent')}
              </button>
            )}
            <button className="btn" onClick={() => { setSuccess(false); setTitle(''); setDescription(''); setMainFile(null); setThumbnailFile(null); setCreatedId(null); }}>
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

      {/* Toggle: single / bulk */}
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
            <select className="filter-select" value={levelBand} onChange={(e) => setLevelBand(e.target.value)}>
              <option value="">{t('cms.content.allLevels')}</option>
              {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
            <select className="filter-select" value={subject} onChange={(e) => setSubject(e.target.value)}>
              <option value="">{t('cms.content.allSubjects')}</option>
              {SUBJECTS.map((s) => <option key={s} value={s}>{t(`cms.subjects.${s}`, s)}</option>)}
            </select>
            <select className="filter-select" value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="fr">Francais</option>
              <option value="ar">Arabe</option>
              <option value="en">English</option>
            </select>
          </div>

          <input
            type="file"
            multiple
            onChange={(e) => setBulkFiles(Array.from(e.target.files || []))}
            style={{ marginBottom: 12 }}
          />

          {bulkFiles.length > 0 && (
            <p style={{ fontSize: 13 }}>{t('cms.upload.bulkCount', { count: bulkFiles.length })}</p>
          )}

          <button className="btn btn-primary" onClick={handleBulkUpload} disabled={uploading || bulkFiles.length === 0}>
            {uploading ? t('cms.upload.uploading') : t('cms.upload.bulkStart')}
          </button>

          {uploading && (
            <div style={{ marginTop: 12 }}>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}

          {bulkResults.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h3>{t('cms.upload.bulkResults')}</h3>
              {bulkResults.map((r, i) => (
                <div key={i} style={{ fontSize: 13, padding: '4px 0', color: r.ok ? 'var(--color-success)' : 'var(--color-danger)' }}>
                  {r.name}: {r.ok ? t('cms.upload.bulkOk') : r.error}
                </div>
              ))}
            </div>
          )}
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
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('cms.upload.titlePlaceholder')}
            />
          </div>

          <div className="form-field">
            <label>{t('cms.upload.description')}</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder={t('cms.upload.descriptionPlaceholder')}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-field">
              <label>{t('cms.upload.contentType')}</label>
              <select required value={contentType} onChange={(e) => setContentType(e.target.value)}>
                {CONTENT_TYPES.map((ct) => (
                  <option key={ct} value={ct}>{t(`cms.contentTypes.${ct}`, ct)}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>{t('cms.upload.level')}</label>
              <select value={levelBand} onChange={(e) => setLevelBand(e.target.value)}>
                <option value="">{t('cms.content.allLevels')}</option>
                {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>

            <div className="form-field">
              <label>{t('cms.upload.subject')}</label>
              <select value={subject} onChange={(e) => setSubject(e.target.value)}>
                <option value="">{t('cms.content.allSubjects')}</option>
                {SUBJECTS.map((s) => <option key={s} value={s}>{t(`cms.subjects.${s}`, s)}</option>)}
              </select>
            </div>

            <div className="form-field">
              <label>{t('cms.upload.language')}</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
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
              onChange={(e) => setMainFile(e.target.files?.[0] || null)}
            />
            {mainFile && contentType === 'video' && mainFile.size > 100 * 1024 * 1024 && (
              <p style={{ fontSize: 12, color: 'var(--color-warning)', marginTop: 4 }}>
                {t('cms.upload.largeFileWarning')}
              </p>
            )}
          </div>

          <div className="form-field">
            <label>{t('cms.upload.thumbnail')}</label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setThumbnailFile(e.target.files?.[0] || null)}
            />
          </div>

          {uploading && (
            <div style={{ marginBottom: 12 }}>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
              </div>
              <p style={{ fontSize: 12, textAlign: 'center', marginTop: 4 }}>{progress}%</p>
            </div>
          )}

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
