import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { toBannerError } from '@/shared/ui/errorUtils';
import { LEVEL_OPTIONS, SUBJECT_OPTIONS } from './content-library.types';
import { useUploadContentItem } from './useTeacher';

export function ContentUploadPanel() {
  const { t } = useTranslation();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contentType, setContentType] = useState('pdf');
  const [levelBand, setLevelBand] = useState('');
  const [subject, setSubject] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [success, setSuccess] = useState(false);
  const uploadMutation = useUploadContentItem();
  const dismissibleError = useDismissibleError(useMemo(() => toBannerError(uploadMutation.error, t('app.error')), [t, uploadMutation.error]));

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !file) return;
    setProgress(0);
    await uploadMutation.mutateAsync({ payload: { title: title.trim(), description: description.trim() || undefined, content_type: contentType, level_band: levelBand || undefined, subject: subject || undefined, language: 'fr', file }, onProgress: setProgress });
    setSuccess(true);
    setTitle('');
    setDescription('');
    setContentType('pdf');
    setLevelBand('');
    setSubject('');
    setFile(null);
    setProgress(0);
  }

  return (
    <>
      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} />
      {success ? (
        <div className="card" style={{ padding: 20, maxWidth: 500 }}>
          <h3 style={{ color: 'var(--color-success)', marginBottom: 12 }}>{t('teacherContent.uploadSuccess')}</h3>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>{t('teacherContent.uploadSuccessMsg')}</p>
          <button className="btn btn-primary" onClick={() => setSuccess(false)}>{t('teacherContent.uploadAnother')}</button>
        </div>
      ) : (
        <form className="card" style={{ padding: 20, maxWidth: 500 }} onSubmit={(event) => void handleSubmit(event)}>
          <h3 style={{ margin: '0 0 16px' }}>{t('teacherContent.uploadTitle')}</h3>
          <label className="form-field" style={{ marginBottom: 12 }}><span>{t('teacherContent.contentTitle')}</span><input className="filter-input" value={title} onChange={(event) => setTitle(event.target.value)} required style={{ width: '100%' }} /></label>
          <label className="form-field" style={{ marginBottom: 12 }}><span>{t('teacherContent.description')}</span><input className="filter-input" value={description} onChange={(event) => setDescription(event.target.value)} style={{ width: '100%' }} /></label>
          <label className="form-field" style={{ marginBottom: 12 }}>
            <span>{t('teacherContent.contentType')}</span>
            <select className="filter-select" value={contentType} onChange={(event) => setContentType(event.target.value)} style={{ width: '100%' }}>
              <option value="pdf">{t('cms.contentTypes.pdf')}</option>
              <option value="video">{t('cms.contentTypes.video')}</option>
              <option value="audio">{t('cms.contentTypes.audio')}</option>
              <option value="interactive">{t('cms.contentTypes.interactive')}</option>
            </select>
          </label>
          <label className="form-field" style={{ marginBottom: 12 }}>
            <span>{t('teacherContent.subject')}</span>
            <select className="filter-select" value={subject} onChange={(event) => setSubject(event.target.value)} style={{ width: '100%' }}>
              <option value="">{t('teacherContent.allSubjects')}</option>
              {SUBJECT_OPTIONS.map((subjectOption) => <option key={subjectOption} value={subjectOption}>{t(`cms.subjects.${subjectOption}`, subjectOption)}</option>)}
            </select>
          </label>
          <label className="form-field" style={{ marginBottom: 12 }}>
            <span>{t('teacherContent.level')}</span>
            <select className="filter-select" value={levelBand} onChange={(event) => setLevelBand(event.target.value)} style={{ width: '100%' }}>
              <option value="">{t('teacherContent.allLevels')}</option>
              {LEVEL_OPTIONS.map((level) => <option key={level} value={level}>{level}</option>)}
            </select>
          </label>
          <label className="form-field" style={{ marginBottom: 12 }}><span>{t('teacherContent.file')}</span><input type="file" onChange={(event) => setFile(event.target.files?.[0] || null)} required /></label>
          {uploadMutation.isPending && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 4 }}>{t('teacherContent.uploading')} {progress}%</div>
              <div style={{ height: 6, background: 'var(--color-bg-secondary)', borderRadius: 3 }}>
                <div style={{ height: '100%', borderRadius: 3, background: 'var(--color-primary)', width: `${progress}%`, transition: 'width 0.3s' }} />
              </div>
            </div>
          )}
          <button type="submit" className="btn btn-primary" disabled={uploadMutation.isPending || !title.trim() || !file}>
            {uploadMutation.isPending ? t('app.loading') : t('teacherContent.upload')}
          </button>
        </form>
      )}
    </>
  );
}
