import { useEffect, useMemo, useState } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import {
  ConfirmDialog,
  DataTable,
  ErrorBanner,
  FormCheckbox,
  FormField,
  FormTextarea,
  LoadingState,
} from '@/shared/ui';
import type { ColumnDef } from '@/shared/ui/DataTable';
import {
  STORY_PAGE_ASSET_TYPES,
  storyPageUploadSchema,
  type CmsContentType,
  type CmsStoryPage,
  type StoryPageUploadValues,
} from './content-upload.types';
import {
  useCmsStoryPages,
  useDeleteCmsStoryPage,
  useReorderCmsStoryPage,
  useUploadCmsStoryPage,
} from './useCms';

type StoryPageRow = CmsStoryPage & Record<string, unknown>;
type StoryPageUploadFormValues = StoryPageUploadValues;

interface StoryPagesEditorProps {
  contentId: string;
  contentType: CmsContentType;
}

const assetTypeOptions = STORY_PAGE_ASSET_TYPES.map((assetType) => ({
  value: assetType,
  label: `cms.storyPages.assetTypes.${assetType}`,
}));

export function StoryPagesEditor({ contentId, contentType }: StoryPagesEditorProps) {
  const { t } = useTranslation();
  const pagesQuery = useCmsStoryPages(contentId);
  const uploadMutation = useUploadCmsStoryPage();
  const deleteMutation = useDeleteCmsStoryPage();
  const reorderMutation = useReorderCmsStoryPage();
  const [file, setFile] = useState<File | null>(null);
  const [pendingDelete, setPendingDelete] = useState<CmsStoryPage | null>(null);
  const [pageNumberEdits, setPageNumberEdits] = useState<Record<string, string>>({});
  const [localError, setLocalError] = useState<string | null>(null);

  const methods = useForm<StoryPageUploadFormValues>({
    resolver: zodResolver(storyPageUploadSchema) as Resolver<StoryPageUploadFormValues>,
    defaultValues: {
      page_number: (pagesQuery.data?.length ?? 0) + 1,
      narration_text: '',
      has_activity: false,
      asset_type: contentType === 'coloring_book' ? 'coloring_page' : 'page_image',
    },
  });

  useEffect(() => {
    if (!pagesQuery.data) {
      return;
    }

    setPageNumberEdits((current) => {
      const next = { ...current };
      for (const page of pagesQuery.data) {
        if (next[page.id] === undefined) {
          next[page.id] = page.page_number ? String(page.page_number) : '';
        }
      }
      return next;
    });

    methods.reset({
      page_number:
        pagesQuery.data.length > 0
          ? Math.max(...pagesQuery.data.map((page) => page.page_number || 0)) + 1
          : 1,
      narration_text: '',
      has_activity: false,
      asset_type: contentType === 'coloring_book' ? 'coloring_page' : 'page_image',
    });
    setFile(null);
  }, [contentType, methods, pagesQuery.data]);

  const error =
    localError ||
    (pagesQuery.error instanceof Error
      ? pagesQuery.error.message
      : uploadMutation.error instanceof Error
        ? uploadMutation.error.message
        : deleteMutation.error instanceof Error
          ? deleteMutation.error.message
          : reorderMutation.error instanceof Error
            ? reorderMutation.error.message
            : null);

  const columns: ColumnDef<StoryPageRow>[] = useMemo(
    () => [
      { key: 'page_number', header: 'cms.storyPages.table.pageNumber' },
      {
        key: 'asset_type',
        header: 'cms.storyPages.table.assetType',
        render: (value) =>
          t(`cms.storyPages.assetTypes.${String(value)}`, {
            defaultValue: String(value || '—'),
          }),
      },
      {
        key: 'narration_text',
        header: 'cms.storyPages.table.narration',
        render: (value) => String(value || '—'),
      },
      {
        key: 'has_activity',
        header: 'cms.storyPages.table.activity',
        render: (value) =>
          value ? t('cms.storyPages.hasActivity') : t('cms.storyPages.noActivity'),
      },
      {
        key: 'file_path',
        header: 'cms.storyPages.table.file',
        render: (value) => String(value).split('/').pop() || String(value),
      },
      {
        key: 'id',
        header: 'cms.storyPages.table.actions',
        sortable: false,
        render: (_value, row) => (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              type="number"
              min={1}
              value={pageNumberEdits[row.id] ?? String(row.page_number ?? '')}
              onChange={(event) =>
                setPageNumberEdits((current) => ({
                  ...current,
                  [row.id]: event.target.value,
                }))
              }
              style={{ width: 84 }}
              aria-label={t('cms.storyPages.table.pageNumber')}
            />
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={reorderMutation.isPending}
              onClick={() => void handleReorder(row)}
            >
              {t('cms.storyPages.reorder')}
            </button>
            <button
              type="button"
              className="btn btn-danger btn-sm"
              disabled={deleteMutation.isPending}
              onClick={() => setPendingDelete(row)}
            >
              {t('cms.storyPages.delete')}
            </button>
          </div>
        ),
      },
    ],
    [deleteMutation.isPending, pageNumberEdits, reorderMutation.isPending, t],
  );

  async function handleUpload(values: StoryPageUploadFormValues) {
    setLocalError(null);
    if (!file) {
      setLocalError(t('cms.storyPages.validation.file'));
      return;
    }

    await uploadMutation.mutateAsync({
      contentId,
      file,
      payload: values,
    });
  }

  async function handleReorder(page: CmsStoryPage) {
    setLocalError(null);
    const nextValue = pageNumberEdits[page.id] ?? '';
    const nextPageNumber = Number(nextValue);

    if (!Number.isInteger(nextPageNumber) || nextPageNumber < 1) {
      setLocalError(t('cms.storyPages.validation.pageNumber'));
      return;
    }

    if (nextPageNumber === page.page_number) {
      return;
    }

    await reorderMutation.mutateAsync({
      contentId,
      page,
      pageNumber: nextPageNumber,
    });
  }

  async function confirmDelete() {
    if (!pendingDelete) {
      return;
    }

    await deleteMutation.mutateAsync({
      contentId,
      assetId: pendingDelete.id,
    });
    setPendingDelete(null);
  }

  if (pagesQuery.isLoading && !pagesQuery.data) {
    return <LoadingState />;
  }

  return (
    <section className="card" style={{ padding: 24, marginTop: 20 }}>
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>{t('cms.storyPages.title')}</h2>
        <p style={{ margin: '8px 0 0', color: 'var(--color-text-secondary)' }}>
          {t('cms.storyPages.subtitle', {
            contentType: t(`cms.contentTypes.${contentType}`),
          })}
        </p>
      </div>

      <ErrorBanner
        error={error}
        onDismiss={() => setLocalError(null)}
        onRetry={error ? () => void pagesQuery.refetch() : undefined}
      />

      <FormProvider {...methods}>
        <form
          onSubmit={methods.handleSubmit((values) => void handleUpload(values))}
          className="card"
          style={{
            padding: 16,
            marginBottom: 20,
            display: 'grid',
            gap: 16,
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          }}
        >
          <FormField<StoryPageUploadFormValues>
            name="page_number"
            label="cms.storyPages.fields.pageNumber"
            type="number"
            disabled={uploadMutation.isPending}
          />
          <div className="form-field">
            <label>{t('cms.storyPages.fields.assetType')}</label>
            <select
              className="form-select__input"
              disabled={uploadMutation.isPending}
              {...methods.register('asset_type')}
            >
              {assetTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {t(option.label)}
                </option>
              ))}
            </select>
          </div>
          <FormTextarea<StoryPageUploadFormValues>
            name="narration_text"
            label="cms.storyPages.fields.narrationText"
            rows={3}
            disabled={uploadMutation.isPending}
            className="story-pages__narration"
          />
          <FormCheckbox<StoryPageUploadFormValues>
            name="has_activity"
            label="cms.storyPages.fields.hasActivity"
            disabled={uploadMutation.isPending}
          />
          <div className="form-field">
            <label>{t('cms.storyPages.fields.file')}</label>
            <input
              type="file"
              accept="image/*,audio/*,.pdf"
              disabled={uploadMutation.isPending}
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
            {file ? <p style={{ marginTop: 4, fontSize: 12 }}>{file.name}</p> : null}
          </div>
          <div style={{ display: 'flex', alignItems: 'end' }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={uploadMutation.isPending || !file}
            >
              {uploadMutation.isPending ? t('app.loading') : t('cms.storyPages.upload')}
            </button>
          </div>
        </form>
      </FormProvider>

      <DataTable<StoryPageRow>
        columns={columns}
        data={(pagesQuery.data ?? []) as StoryPageRow[]}
        loading={pagesQuery.isLoading}
        emptyMessage="cms.storyPages.empty"
        sortable={false}
        ariaLabel={t('cms.storyPages.title')}
      />

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="cms.storyPages.deleteConfirmTitle"
        message="cms.storyPages.deleteConfirmMessage"
        confirmLabel="cms.storyPages.delete"
        variant="danger"
        loading={deleteMutation.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => void confirmDelete()}
      />
    </section>
  );
}
