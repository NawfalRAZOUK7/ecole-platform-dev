/**
 * CMS Content Edit — edit metadata, replace files, publish/archive.
 *
 * Phase 10A — loads content by ID, allows editing all metadata fields
 * and changing status (draft/published/archived).
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, getAccessToken } from '@/services/api/client';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';

interface ContentItem {
  id: string;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  thumbnail_path: string | null;
  origin: string;
  status: string;
  created_by: string | null;
  original_content_id: string | null;
}

const CONTENT_TYPES = ['video', 'pdf', 'audio', 'interactive'];
const LEVELS = ['maternelle', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];
const SUBJECTS = ['math', 'french', 'arabic', 'science', 'history', 'geography', 'english', 'islamic_studies', 'art', 'sport'];

export function CmsContentEditPage() {
  const { contentId } = useParams<{ contentId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [item, setItem] = useState<ContentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contentType, setContentType] = useState('');
  const [levelBand, setLevelBand] = useState('');
  const [subject, setSubject] = useState('');
  const [language, setLanguage] = useState('');
  const [status, setStatus] = useState('');

  // File replacement
  const [newFile, setNewFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const fetchContent = useCallback(async () => {
    try {
      // Use the cms endpoint to get full details
      const resp = await api.list<ContentItem>('/cms/content', { limit: 50 });
      const found = resp.data.find((c) => c.id === contentId);
      if (!found) {
        setError(t('errors.not_found'));
        return;
      }
      setItem(found);
      setTitle(found.title);
      setDescription(found.description || '');
      setContentType(found.content_type);
      setLevelBand(found.level_band || '');
      setSubject(found.subject || '');
      setLanguage(found.language || '');
      setStatus(found.status);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [contentId, t]);

  useEffect(() => {
    setLoading(true);
    fetchContent().finally(() => setLoading(false));
  }, [fetchContent]);

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      await api.put(`/cms/content/${contentId}`, {
        title,
        content_type: contentType,
        level_band: levelBand || null,
        language: language || null,
        subject: subject || null,
        description: description || null,
        status,
      });

      // Upload replacement file if provided
      if (newFile) {
        setUploadProgress(0);
        const formData = new FormData();
        formData.append('file', newFile);
        await new Promise<void>((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', `/api/v1/content-items/${contentId}/assets`);
          const token = getAccessToken();
          if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
          xhr.upload.onprogress = (ev) => {
            if (ev.lengthComputable) setUploadProgress(Math.round((ev.loaded / ev.total) * 100));
          };
          xhr.onload = () => (xhr.status < 300 ? resolve() : reject(new Error(`Upload failed: ${xhr.status}`)));
          xhr.onerror = () => reject(new Error('Network error'));
          xhr.send(formData);
        });
        setNewFile(null);
      }

      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSaving(false);
    }
  }

  async function handleArchive() {
    try {
      await api.delete(`/cms/content/${contentId}`);
      navigate('/cms');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  if (loading) return <LoadingState />;
  if (!item && error) {
    return (
      <div className="page">
        <ErrorBanner error={error} />
        <button className="btn" onClick={() => navigate('/cms')}>{t('app.back')}</button>
      </div>
    );
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 className="page-title">{t('cms.edit.title')}</h1>
        <button className="btn" onClick={() => navigate('/cms')}>{t('app.back')}</button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {saved && (
        <div className="alert alert-success" style={{ marginBottom: 16, padding: 12, borderRadius: 8 }}>
          {t('cms.edit.saved')}
        </div>
      )}

      <form onSubmit={handleSave} className="card" style={{ padding: 24 }}>
        <div className="form-field">
          <label>{t('cms.upload.titleLabel')}</label>
          <input type="text" required maxLength={300} value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>

        <div className="form-field">
          <label>{t('cms.upload.description')}</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="form-field">
            <label>{t('cms.upload.contentType')}</label>
            <select value={contentType} onChange={(e) => setContentType(e.target.value)}>
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
          <label>{t('cms.edit.status')}</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="draft">{t('cms.statuses.draft')}</option>
            <option value="published">{t('cms.statuses.published')}</option>
            <option value="archived">{t('cms.statuses.archived')}</option>
          </select>
        </div>

        <div className="form-field">
          <label>{t('cms.edit.replaceFile')}</label>
          <input type="file" onChange={(e) => setNewFile(e.target.files?.[0] || null)} />
        </div>

        {saving && newFile && (
          <div style={{ marginBottom: 12 }}>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
          </div>
        )}

        {item?.origin === 'PROMOTED' && (
          <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
            {t('cms.edit.promotedNote')}
          </p>
        )}

        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? t('app.loading') : t('app.save')}
          </button>
          {status !== 'archived' && (
            <button type="button" className="btn btn-danger" onClick={handleArchive}>
              {t('cms.edit.archive')}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
