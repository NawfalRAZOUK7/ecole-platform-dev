import { useTranslation } from 'react-i18next';
import { LEVELS, SUBJECTS, type BulkUploadResult } from './content-upload.types';

export interface CmsBulkUploadFormProps {
  bulkFiles: File[];
  bulkResults: BulkUploadResult[];
  language: string;
  levelBand: string;
  progress: number;
  subject: string;
  uploading: boolean;
  onBulkUpload: () => void;
  onChangeBulkFiles: (files: File[]) => void;
  onChangeLanguage: (value: string) => void;
  onChangeLevelBand: (value: string) => void;
  onChangeSubject: (value: string) => void;
}

export function CmsBulkUploadForm({
  bulkFiles,
  bulkResults,
  language,
  levelBand,
  progress,
  subject,
  uploading,
  onBulkUpload,
  onChangeBulkFiles,
  onChangeLanguage,
  onChangeLevelBand,
  onChangeSubject,
}: CmsBulkUploadFormProps) {
  const { t } = useTranslation();

  return (
    <div className="card" style={{ padding: 24 }}>
      <h2 style={{ marginTop: 0 }}>{t('cms.upload.bulkTitle')}</h2>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>{t('cms.upload.bulkHint')}</p>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <select className="filter-select" value={levelBand} onChange={(event) => onChangeLevelBand(event.target.value)}>
          <option value="">{t('cms.content.allLevels')}</option>
          {LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}
        </select>
        <select className="filter-select" value={subject} onChange={(event) => onChangeSubject(event.target.value)}>
          <option value="">{t('cms.content.allSubjects')}</option>
          {SUBJECTS.map((currentSubject) => <option key={currentSubject} value={currentSubject}>{t(`cms.subjects.${currentSubject}`, currentSubject)}</option>)}
        </select>
        <select className="filter-select" value={language} onChange={(event) => onChangeLanguage(event.target.value)}>
          <option value="fr">Francais</option>
          <option value="ar">Arabe</option>
          <option value="en">English</option>
        </select>
      </div>

      <input type="file" multiple onChange={(event) => onChangeBulkFiles(Array.from(event.target.files || []))} style={{ marginBottom: 12 }} />

      {bulkFiles.length > 0 ? <p style={{ fontSize: 13 }}>{t('cms.upload.bulkCount', { count: bulkFiles.length })}</p> : null}

      <button className="btn btn-primary" onClick={onBulkUpload} disabled={uploading || bulkFiles.length === 0}>
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
            <div key={`${result.name}-${index}`} style={{ fontSize: 13, padding: '4px 0', color: result.ok ? 'var(--color-success)' : 'var(--color-danger)' }}>
              {result.name}: {result.ok ? t('cms.upload.bulkOk') : result.error}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
