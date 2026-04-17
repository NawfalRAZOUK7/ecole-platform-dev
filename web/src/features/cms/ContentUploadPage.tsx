import { useEffect, useMemo, useState } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { FormField, FormSelect, FormTextarea } from '@/shared/ui';
import { CmsBulkUploadForm } from './CmsBulkUploadForm';
import { CmsUploadSuccess } from './CmsUploadSuccess';
import {
  ACCEPT_MAP,
  CONTENT_TYPES,
  LEVELS,
  SUBJECTS,
  buildCmsContentFormDefaults,
  cmsContentFormSchema,
  isStoryContentType,
  type BulkUploadResult,
  type CmsContentFormValues,
} from './content-upload.types';
import { useCreateCmsContent, useUploadCmsContentAsset } from './useCms';
import {
  fetchLevelMappings,
  buildLevelMap,
  type LevelAgeMapping,
} from '@/services/levels.service';

const languageOptions = [
  { value: 'fr', label: 'Francais' },
  { value: 'ar', label: 'Arabe' },
  { value: 'en', label: 'English' },
];

export function CmsContentUploadPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const createContentMutation = useCreateCmsContent();
  const uploadContentAssetMutation = useUploadCmsContentAsset();

  const methods = useForm<CmsContentFormValues>({
    resolver: zodResolver(cmsContentFormSchema) as Resolver<CmsContentFormValues>,
    defaultValues: buildCmsContentFormDefaults(),
  });

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
  const [bulkLevelBand, setBulkLevelBand] = useState('');
  const [bulkSubject, setBulkSubject] = useState('');
  const [bulkLanguage, setBulkLanguage] = useState('fr');

  const watchedContentType = methods.watch('content_type');
  const watchedTitle = methods.watch('title');
  const watchedLevelBand = methods.watch('level_band');
  const isStoryLike = isStoryContentType(watchedContentType);
  const [levelMap, setLevelMap] = useState<Record<string, LevelAgeMapping>>({});

  useEffect(() => {
    fetchLevelMappings()
      .then((mappings) => setLevelMap(buildLevelMap(mappings)))
      .catch(() => {
        // Non-critical — suggestions simply won't show
      });
  }, []);

  // Auto-suggest target_age fields when level_band changes (only if fields are empty)
  useEffect(() => {
    if (!watchedLevelBand || !levelMap[watchedLevelBand]) return;
    const mapping = levelMap[watchedLevelBand];
    const current = methods.getValues();
    if (!current.target_age_min) {
      methods.setValue('target_age_min', mapping.default_age_min);
    }
    if (!current.target_age_max) {
      methods.setValue('target_age_max', mapping.default_age_max);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchedLevelBand, levelMap]);

  const contentTypeOptions = useMemo(
    () =>
      CONTENT_TYPES.map((contentType) => ({
        value: contentType,
        label: `cms.contentTypes.${contentType}`,
      })),
    [],
  );
  const levelOptions = useMemo(() => LEVELS.map((level) => ({ value: level, label: level })), []);
  const subjectOptions = useMemo(
    () =>
      SUBJECTS.map((subject) => ({
        value: subject,
        label: `cms.subjects.${subject}`,
      })),
    [],
  );

  async function uploadFileWithProgress(contentId: string, file: File) {
    await uploadContentAssetMutation.mutateAsync({ contentId, file, onProgress: setProgress });
  }

  function resetSingleUpload() {
    setSuccess(false);
    setError(null);
    setMainFile(null);
    setThumbnailFile(null);
    setCreatedId(null);
    setProgress(0);
    methods.reset(buildCmsContentFormDefaults());
  }

  async function handleSubmit(values: CmsContentFormValues) {
    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      const created = await createContentMutation.mutateAsync({
        title: values.title.trim(),
        content_type: values.content_type,
        level_band: values.level_band || undefined,
        language: values.language || undefined,
        subject: values.subject || undefined,
        description: values.description.trim() || undefined,
        page_count: isStoryContentType(values.content_type) ? values.page_count : null,
        letter: isStoryContentType(values.content_type) ? values.letter.trim() || null : null,
        target_age_min: isStoryContentType(values.content_type) ? values.target_age_min : null,
        target_age_max: isStoryContentType(values.content_type) ? values.target_age_max : null,
        theme_color: isStoryContentType(values.content_type) ? values.theme_color : null,
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
    const results: BulkUploadResult[] = [];

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
          level_band: bulkLevelBand || undefined,
          language: bulkLanguage || undefined,
          subject: bulkSubject || undefined,
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
        <button
          type="button"
          className={`btn ${!bulkMode ? 'btn-primary' : ''}`}
          onClick={() => setBulkMode(false)}
        >
          {t('cms.upload.singleMode')}
        </button>
        <button
          type="button"
          className={`btn ${bulkMode ? 'btn-primary' : ''}`}
          onClick={() => setBulkMode(true)}
        >
          {t('cms.upload.bulkMode')}
        </button>
      </div>

      {bulkMode ? (
        <CmsBulkUploadForm
          bulkFiles={bulkFiles}
          bulkResults={bulkResults}
          language={bulkLanguage}
          levelBand={bulkLevelBand}
          progress={progress}
          subject={bulkSubject}
          uploading={uploading}
          onBulkUpload={() => void handleBulkUpload()}
          onChangeBulkFiles={setBulkFiles}
          onChangeLanguage={setBulkLanguage}
          onChangeLevelBand={setBulkLevelBand}
          onChangeSubject={setBulkSubject}
        />
      ) : (
        <FormProvider {...methods}>
          <form
            onSubmit={methods.handleSubmit((values) => void handleSubmit(values))}
            className="card"
            style={{ padding: 24 }}
          >
            <FormField<CmsContentFormValues>
              name="title"
              label="cms.upload.titleLabel"
              placeholder="cms.upload.titlePlaceholder"
              disabled={uploading}
            />

            <FormTextarea<CmsContentFormValues>
              name="description"
              label="cms.upload.description"
              rows={3}
              placeholder="cms.upload.descriptionPlaceholder"
              disabled={uploading}
            />

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <FormSelect<CmsContentFormValues>
                name="content_type"
                label="cms.upload.contentType"
                options={contentTypeOptions}
                disabled={uploading}
              />

              <div>
                <FormSelect<CmsContentFormValues>
                  name="level_band"
                  label="cms.upload.level"
                  options={levelOptions}
                  placeholder="cms.content.allLevels"
                  disabled={uploading}
                />
                {watchedLevelBand && levelMap[watchedLevelBand] ? (
                  <span
                    style={{
                      display: 'block',
                      fontSize: 11,
                      color: 'var(--color-text-secondary)',
                      marginTop: 2,
                    }}
                  >
                    {watchedLevelBand.toUpperCase()} → {levelMap[watchedLevelBand].default_age_min}
                    -{levelMap[watchedLevelBand].default_age_max} ans
                  </span>
                ) : null}
              </div>

              <FormSelect<CmsContentFormValues>
                name="subject"
                label="cms.upload.subject"
                options={subjectOptions}
                placeholder="cms.content.allSubjects"
                disabled={uploading}
              />

              <FormSelect<CmsContentFormValues>
                name="language"
                label="cms.upload.language"
                options={languageOptions}
                disabled={uploading}
              />
            </div>

            {isStoryLike ? (
              <div
                className="card"
                style={{
                  margin: '16px 0',
                  padding: 16,
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: 16,
                }}
              >
                <FormField<CmsContentFormValues>
                  name="page_count"
                  label="cms.fields.pageCount"
                  type="number"
                  disabled={uploading}
                />
                <FormField<CmsContentFormValues>
                  name="letter"
                  label="cms.fields.letter"
                  placeholder="cms.upload.letterPlaceholder"
                  disabled={uploading}
                />
                <FormField<CmsContentFormValues>
                  name="target_age_min"
                  label="cms.fields.targetAgeMin"
                  type="number"
                  disabled={uploading}
                />
                <FormField<CmsContentFormValues>
                  name="target_age_max"
                  label="cms.fields.targetAgeMax"
                  type="number"
                  disabled={uploading}
                />
                <FormField<CmsContentFormValues>
                  name="theme_color"
                  label="cms.fields.themeColor"
                  type="color"
                  disabled={uploading}
                />
              </div>
            ) : null}

            <div className="form-field">
              <label>{t('cms.upload.mainFile')}</label>
              <input
                type="file"
                accept={ACCEPT_MAP[watchedContentType] || '*'}
                disabled={uploading}
                onChange={(event) => setMainFile(event.target.files?.[0] || null)}
              />
              {mainFile && watchedContentType === 'video' && mainFile.size > 100 * 1024 * 1024 ? (
                <p
                  style={{
                    fontSize: 12,
                    color: 'var(--color-warning)',
                    marginTop: 4,
                  }}
                >
                  {t('cms.upload.largeFileWarning')}
                </p>
              ) : null}
            </div>

            <div className="form-field">
              <label>{t('cms.upload.thumbnail')}</label>
              <input
                type="file"
                accept="image/*"
                disabled={uploading}
                onChange={(event) => setThumbnailFile(event.target.files?.[0] || null)}
              />
              {thumbnailFile ? (
                <p style={{ fontSize: 12, marginTop: 4 }}>{thumbnailFile.name}</p>
              ) : null}
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
              <button
                type="submit"
                className="btn btn-primary"
                disabled={uploading || !watchedTitle.trim()}
              >
                {uploading ? t('cms.upload.uploading') : t('cms.upload.submit')}
              </button>
              <button type="button" className="btn" onClick={() => navigate('/cms')}>
                {t('app.cancel')}
              </button>
            </div>
          </form>
        </FormProvider>
      )}
    </div>
  );
}
