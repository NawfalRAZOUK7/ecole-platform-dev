import { useEffect, useMemo, useState } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { FormField, FormSelect, FormTextarea, LoadingState } from '@/shared/ui';
import { StoryPagesEditor } from './StoryPagesEditor';
import {
  ACCEPT_MAP,
  CONTENT_TYPES,
  LEVELS,
  SUBJECTS,
  buildCmsContentFormDefaults,
  cmsContentFormSchema,
  isStoryContentType,
  type CmsContentFormValues,
  type CmsContentType,
} from './content-upload.types';
import {
  useCmsContentItem,
  useDeleteCmsContent,
  useUpdateCmsContent,
  useUploadCmsContentAsset,
} from './useCms';

const languageOptions = [
  { value: 'fr', label: 'Francais' },
  { value: 'ar', label: 'Arabe' },
  { value: 'en', label: 'English' },
];

const statusOptions = [
  { value: 'draft', label: 'cms.statuses.draft' },
  { value: 'published', label: 'cms.statuses.published' },
  { value: 'archived', label: 'cms.statuses.archived' },
] as const;

export function CmsContentEditPage() {
  const { contentId } = useParams<{ contentId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const contentQuery = useCmsContentItem(contentId);
  const updateContentMutation = useUpdateCmsContent();
  const deleteContentMutation = useDeleteCmsContent();
  const uploadContentAssetMutation = useUploadCmsContentAsset();

  const methods = useForm<CmsContentFormValues>({
    resolver: zodResolver(cmsContentFormSchema) as Resolver<CmsContentFormValues>,
    defaultValues: buildCmsContentFormDefaults(),
  });

  const [newFile, setNewFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const saving =
    updateContentMutation.isPending ||
    deleteContentMutation.isPending ||
    uploadContentAssetMutation.isPending;

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

  useEffect(() => {
    if (!contentQuery.data) {
      return;
    }

    methods.reset(
      buildCmsContentFormDefaults({
        title: contentQuery.data.title,
        description: contentQuery.data.description ?? '',
        content_type: contentQuery.data.content_type as CmsContentType,
        level_band: contentQuery.data.level_band ?? '',
        subject: contentQuery.data.subject ?? '',
        language: contentQuery.data.language ?? 'fr',
        page_count: contentQuery.data.page_count ?? null,
        letter: contentQuery.data.letter ?? '',
        target_age_min: contentQuery.data.target_age_min ?? null,
        target_age_max: contentQuery.data.target_age_max ?? null,
        theme_color: contentQuery.data.theme_color ?? '#4F46E5',
        status:
          contentQuery.data.status === 'published' || contentQuery.data.status === 'archived'
            ? contentQuery.data.status
            : 'draft',
      }),
    );
  }, [contentQuery.data, methods]);

  const watchedContentType = methods.watch('content_type');
  const watchedStatus = methods.watch('status');
  const isStoryLike = isStoryContentType(watchedContentType);

  if (contentQuery.isLoading) {
    return <LoadingState />;
  }

  if (!contentQuery.data) {
    return (
      <div className="page">
        <ErrorBanner
          error={
            error ||
            (contentQuery.error instanceof Error
              ? contentQuery.error.message
              : t('errors.not_found'))
          }
        />
        <button className="btn" onClick={() => navigate('/cms')}>
          {t('app.back')}
        </button>
      </div>
    );
  }

  async function handleSave(values: CmsContentFormValues) {
    setError(null);
    setSaved(false);

    try {
      await updateContentMutation.mutateAsync({
        contentId: contentId!,
        payload: {
          title: values.title.trim(),
          content_type: values.content_type,
          level_band: values.level_band || null,
          language: values.language || null,
          subject: values.subject || null,
          description: values.description.trim() || null,
          page_count: isStoryContentType(values.content_type) ? values.page_count : null,
          letter: isStoryContentType(values.content_type) ? values.letter.trim() || null : null,
          target_age_min: isStoryContentType(values.content_type) ? values.target_age_min : null,
          target_age_max: isStoryContentType(values.content_type) ? values.target_age_max : null,
          theme_color: isStoryContentType(values.content_type) ? values.theme_color : null,
          status: values.status,
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
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <h1 className="page-title">{t('cms.edit.title')}</h1>
        <button className="btn" onClick={() => navigate('/cms')}>
          {t('app.back')}
        </button>
      </div>

      <ErrorBanner
        error={error || (contentQuery.error instanceof Error ? contentQuery.error.message : null)}
        onDismiss={() => setError(null)}
      />
      {saved ? (
        <div
          className="alert alert-success"
          style={{ marginBottom: 16, padding: 12, borderRadius: 8 }}
        >
          {t('app.saved')}
        </div>
      ) : null}

      <FormProvider {...methods}>
        <form
          onSubmit={methods.handleSubmit((values) => void handleSave(values))}
          className="card"
          style={{ padding: 24 }}
        >
          <FormField<CmsContentFormValues>
            name="title"
            label="cms.upload.titleLabel"
            disabled={saving}
          />

          <FormTextarea<CmsContentFormValues>
            name="description"
            label="cms.upload.description"
            rows={4}
            disabled={saving}
          />

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
              gap: 12,
            }}
          >
            <FormSelect<CmsContentFormValues>
              name="content_type"
              label="cms.upload.contentType"
              options={contentTypeOptions}
              disabled={saving}
            />

            <FormSelect<CmsContentFormValues>
              name="level_band"
              label="cms.upload.level"
              options={levelOptions}
              placeholder="cms.content.allLevels"
              disabled={saving}
            />

            <FormSelect<CmsContentFormValues>
              name="subject"
              label="cms.upload.subject"
              options={subjectOptions}
              placeholder="cms.content.allSubjects"
              disabled={saving}
            />

            <FormSelect<CmsContentFormValues>
              name="language"
              label="cms.upload.language"
              options={languageOptions}
              disabled={saving}
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
                disabled={saving}
              />
              <FormField<CmsContentFormValues>
                name="letter"
                label="cms.fields.letter"
                placeholder="cms.upload.letterPlaceholder"
                disabled={saving}
              />
              <FormField<CmsContentFormValues>
                name="target_age_min"
                label="cms.fields.targetAgeMin"
                type="number"
                disabled={saving}
              />
              <FormField<CmsContentFormValues>
                name="target_age_max"
                label="cms.fields.targetAgeMax"
                type="number"
                disabled={saving}
              />
              <FormField<CmsContentFormValues>
                name="theme_color"
                label="cms.fields.themeColor"
                type="color"
                disabled={saving}
              />
            </div>
          ) : null}

          <FormSelect<CmsContentFormValues>
            name="status"
            label="cms.edit.status"
            options={[...statusOptions]}
            disabled={saving}
          />

          <div className="form-field">
            <label>{t('cms.edit.replaceFile')}</label>
            <input
              type="file"
              accept={ACCEPT_MAP[watchedContentType] || '*'}
              disabled={saving}
              onChange={(event) => setNewFile(event.target.files?.[0] || null)}
            />
            {newFile ? <p style={{ fontSize: 12, marginTop: 4 }}>{newFile.name}</p> : null}
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
            {watchedStatus !== 'archived' ? (
              <button type="button" className="btn btn-danger" onClick={() => void handleArchive()}>
                {t('cms.edit.archive')}
              </button>
            ) : null}
          </div>
        </form>
      </FormProvider>

      {contentId && isStoryLike ? (
        <StoryPagesEditor contentId={contentId} contentType={watchedContentType} />
      ) : null}
    </div>
  );
}
