import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { ACCEPT_MAP, CONTENT_TYPES, LEVELS, SUBJECTS } from './content-upload.types';

export interface CmsSingleUploadFormProps {
  contentType: string;
  description: string;
  language: string;
  levelBand: string;
  mainFile: File | null;
  progress: number;
  subject: string;
  thumbnailFile: File | null;
  title: string;
  uploading: boolean;
  onCancel: () => void;
  onChangeContentType: (value: string) => void;
  onChangeDescription: (value: string) => void;
  onChangeLanguage: (value: string) => void;
  onChangeLevelBand: (value: string) => void;
  onChangeMainFile: (file: File | null) => void;
  onChangeSubject: (value: string) => void;
  onChangeThumbnailFile: (file: File | null) => void;
  onChangeTitle: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

export function CmsSingleUploadForm({
  contentType,
  description,
  language,
  levelBand,
  mainFile,
  progress,
  subject,
  thumbnailFile,
  title,
  uploading,
  onCancel,
  onChangeContentType,
  onChangeDescription,
  onChangeLanguage,
  onChangeLevelBand,
  onChangeMainFile,
  onChangeSubject,
  onChangeThumbnailFile,
  onChangeTitle,
  onSubmit,
}: CmsSingleUploadFormProps) {
  const { t } = useTranslation();

  return (
    <form onSubmit={onSubmit} className="card" style={{ padding: 24 }}>
      <div className="form-field">
        <label>{t('cms.upload.titleLabel')}</label>
        <input type="text" required maxLength={300} value={title} onChange={(event) => onChangeTitle(event.target.value)} placeholder={t('cms.upload.titlePlaceholder')} />
      </div>

      <div className="form-field">
        <label>{t('cms.upload.description')}</label>
        <textarea value={description} onChange={(event) => onChangeDescription(event.target.value)} rows={3} placeholder={t('cms.upload.descriptionPlaceholder')} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="form-field">
          <label>{t('cms.upload.contentType')}</label>
          <select required value={contentType} onChange={(event) => onChangeContentType(event.target.value)}>
            {CONTENT_TYPES.map((currentType) => <option key={currentType} value={currentType}>{t(`cms.contentTypes.${currentType}`, currentType)}</option>)}
          </select>
        </div>

        <div className="form-field">
          <label>{t('cms.upload.level')}</label>
          <select value={levelBand} onChange={(event) => onChangeLevelBand(event.target.value)}>
            <option value="">{t('cms.content.allLevels')}</option>
            {LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}
          </select>
        </div>

        <div className="form-field">
          <label>{t('cms.upload.subject')}</label>
          <select value={subject} onChange={(event) => onChangeSubject(event.target.value)}>
            <option value="">{t('cms.content.allSubjects')}</option>
            {SUBJECTS.map((currentSubject) => <option key={currentSubject} value={currentSubject}>{t(`cms.subjects.${currentSubject}`, currentSubject)}</option>)}
          </select>
        </div>

        <div className="form-field">
          <label>{t('cms.upload.language')}</label>
          <select value={language} onChange={(event) => onChangeLanguage(event.target.value)}>
            <option value="fr">Francais</option>
            <option value="ar">Arabe</option>
            <option value="en">English</option>
          </select>
        </div>
      </div>

      <div className="form-field">
        <label>{t('cms.upload.mainFile')}</label>
        <input type="file" accept={ACCEPT_MAP[contentType] || '*'} onChange={(event) => onChangeMainFile(event.target.files?.[0] || null)} />
        {mainFile && contentType === 'video' && mainFile.size > 100 * 1024 * 1024 ? <p style={{ fontSize: 12, color: 'var(--color-warning)', marginTop: 4 }}>{t('cms.upload.largeFileWarning')}</p> : null}
      </div>

      <div className="form-field">
        <label>{t('cms.upload.thumbnail')}</label>
        <input type="file" accept="image/*" onChange={(event) => onChangeThumbnailFile(event.target.files?.[0] || null)} />
        {thumbnailFile ? <p style={{ fontSize: 12, marginTop: 4 }}>{thumbnailFile.name}</p> : null}
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
        <button type="button" className="btn" onClick={onCancel}>
          {t('app.cancel')}
        </button>
      </div>
    </form>
  );
}
