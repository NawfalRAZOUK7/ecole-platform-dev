import { useEffect, useMemo, useState } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';
import { rewardsQueryKeys } from '@/features/ai/rewards/model/useRewards';
import { rewardsService, type Badge } from '@/features/ai/rewards/api/rewards.api';
import {
  ErrorBanner,
  FileUpload,
  FormCheckbox,
  FormField,
  FormSelect,
  FormTextarea,
} from '@/shared/ui';

const BADGE_CRITERIA_TYPES = [
  'manual',
  'stars_total',
  'xp_total',
  'level_reached',
  'streak_days',
  'event_count',
] as const;

const badgeEditorSchema = z.object({
  code: z
    .string()
    .trim()
    .min(1, 'admin.badges.validation.code')
    .max(80, 'admin.badges.validation.code'),
  titleFr: z
    .string()
    .trim()
    .min(1, 'admin.badges.validation.title')
    .max(200, 'admin.badges.validation.title'),
  titleAr: z
    .string()
    .trim()
    .min(1, 'admin.badges.validation.title')
    .max(200, 'admin.badges.validation.title'),
  titleEn: z
    .string()
    .trim()
    .min(1, 'admin.badges.validation.title')
    .max(200, 'admin.badges.validation.title'),
  descriptionFr: z.string().trim().max(1000, 'admin.badges.validation.description'),
  descriptionAr: z.string().trim().max(1000, 'admin.badges.validation.description'),
  descriptionEn: z.string().trim().max(1000, 'admin.badges.validation.description'),
  icon: z.string().trim(),
  criteriaType: z
    .string()
    .trim()
    .min(1, 'admin.badges.validation.criteriaType')
    .max(100, 'admin.badges.validation.criteriaType'),
  criteriaValue: z.coerce
    .number()
    .int('admin.badges.validation.criteriaValue')
    .min(0, 'admin.badges.validation.criteriaValue'),
  displayOrder: z.coerce
    .number()
    .int('admin.badges.validation.displayOrder')
    .min(0, 'admin.badges.validation.displayOrder'),
  isActive: z.boolean(),
});

type BadgeEditorFormValues = z.infer<typeof badgeEditorSchema>;

interface BadgeEditorProps {
  badge?: Badge | null;
  onCancel: () => void;
  onSaved: (badge: Badge) => void;
}

function createDefaultValues(badge?: Badge | null): BadgeEditorFormValues {
  return {
    code: badge?.code ?? '',
    titleFr: badge?.titleFr ?? '',
    titleAr: badge?.titleAr ?? '',
    titleEn: badge?.titleEn ?? '',
    descriptionFr: badge?.descriptionFr ?? '',
    descriptionAr: badge?.descriptionAr ?? '',
    descriptionEn: badge?.descriptionEn ?? '',
    icon: badge?.icon ?? '',
    criteriaType: badge?.criteriaType ?? 'manual',
    criteriaValue: badge?.criteriaValue ?? 0,
    displayOrder: badge?.displayOrder ?? 0,
    isActive: badge?.isActive ?? true,
  };
}

function isImageLike(icon: string) {
  return (
    icon.startsWith('data:image/') ||
    icon.startsWith('http://') ||
    icon.startsWith('https://') ||
    icon.startsWith('/')
  );
}

function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result);
        return;
      }

      reject(new Error('admin.badges.uploadFailed'));
    };
    reader.onerror = () => reject(new Error('admin.badges.uploadFailed'));
    reader.readAsDataURL(file);
  });
}

export function BadgeEditor({ badge, onCancel, onSaved }: BadgeEditorProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [uploadError, setUploadError] = useState<string | null>(null);
  const form = useForm<BadgeEditorFormValues>({
    resolver: zodResolver(badgeEditorSchema) as Resolver<BadgeEditorFormValues>,
    defaultValues: createDefaultValues(badge),
  });
  const { reset, setValue, watch } = form;
  const iconValue = watch('icon');

  useEffect(() => {
    reset(createDefaultValues(badge));
    setUploadError(null);
  }, [badge, reset]);

  const criteriaOptions = useMemo(() => {
    const optionValues = new Set<string>(BADGE_CRITERIA_TYPES);

    if (badge?.criteriaType) {
      optionValues.add(badge.criteriaType);
    }

    return Array.from(optionValues).map((value) => ({
      value,
      label: `admin.badges.criteriaTypes.${value}`,
    }));
  }, [badge?.criteriaType]);

  const saveMutation = useMutation({
    mutationFn: async (values: BadgeEditorFormValues) => {
      const payload: Partial<Badge> = {
        code: values.code.trim(),
        titleFr: values.titleFr.trim(),
        titleAr: values.titleAr.trim(),
        titleEn: values.titleEn.trim(),
        descriptionFr: values.descriptionFr.trim() || null,
        descriptionAr: values.descriptionAr.trim() || null,
        descriptionEn: values.descriptionEn.trim() || null,
        icon: values.icon.trim() || null,
        criteriaType: values.criteriaType.trim(),
        criteriaValue: values.criteriaValue,
        displayOrder: values.displayOrder,
        isActive: values.isActive,
      };

      if (badge?.id) {
        return rewardsService.updateBadge(badge.id, payload);
      }

      return rewardsService.createBadge(payload);
    },
    onSuccess: async (savedBadge) => {
      await queryClient.invalidateQueries({ queryKey: rewardsQueryKeys.badges() });
      onSaved(savedBadge);
    },
  });

  async function applySelectedFiles(files: File[]) {
    if (files.length === 0) {
      return;
    }

    setUploadError(null);

    try {
      const dataUrl = await readFileAsDataUrl(files[0]);
      setValue('icon', dataUrl, {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      });
    } catch (error) {
      setUploadError(
        error instanceof Error
          ? t(error.message, { defaultValue: error.message })
          : t('admin.badges.uploadFailed'),
      );
    }
  }

  function handleFilesSelected(files: File[]) {
    void applySelectedFiles(files);
  }

  return (
    <FormProvider {...form}>
      <form
        onSubmit={form.handleSubmit((values) => {
          void saveMutation.mutateAsync(values);
        })}
      >
        <h2 style={{ margin: '0 0 16px' }}>
          {t(badge ? 'admin.badges.editTitle' : 'admin.badges.createTitle')}
        </h2>

        <ErrorBanner
          error={
            uploadError ?? (saveMutation.error instanceof Error ? saveMutation.error.message : null)
          }
          onDismiss={() => {
            setUploadError(null);
            saveMutation.reset();
          }}
        />

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 16,
          }}
        >
          <FormField<BadgeEditorFormValues> name="code" label="admin.badges.form.code" />
          <FormSelect<BadgeEditorFormValues>
            name="criteriaType"
            label="admin.badges.form.criteriaType"
            options={criteriaOptions}
          />
          <FormField<BadgeEditorFormValues>
            name="criteriaValue"
            label="admin.badges.form.criteriaValue"
            type="number"
          />
          <FormField<BadgeEditorFormValues>
            name="displayOrder"
            label="admin.badges.form.displayOrder"
            type="number"
          />
          <FormField<BadgeEditorFormValues> name="titleFr" label="admin.badges.form.titleFr" />
          <FormField<BadgeEditorFormValues> name="titleAr" label="admin.badges.form.titleAr" />
          <FormField<BadgeEditorFormValues> name="titleEn" label="admin.badges.form.titleEn" />
        </div>

        <div style={{ marginTop: 16, display: 'grid', gap: 16 }}>
          <FormTextarea<BadgeEditorFormValues>
            name="descriptionFr"
            label="admin.badges.form.descriptionFr"
            rows={3}
          />
          <FormTextarea<BadgeEditorFormValues>
            name="descriptionAr"
            label="admin.badges.form.descriptionAr"
            rows={3}
          />
          <FormTextarea<BadgeEditorFormValues>
            name="descriptionEn"
            label="admin.badges.form.descriptionEn"
            rows={3}
          />
        </div>

        <div className="card" style={{ marginTop: 16, padding: 16 }}>
          <div style={{ display: 'grid', gap: 12 }}>
            <div className="form-field" style={{ marginBottom: 0 }}>
              <label className="form-field__label" htmlFor="badge-icon-input">
                {t('admin.badges.form.icon')}
              </label>
              <input
                id="badge-icon-input"
                type="text"
                className="form-field__input"
                value={iconValue}
                placeholder={t('admin.badges.form.iconPlaceholder')}
                onChange={(event) =>
                  setValue('icon', event.target.value, {
                    shouldDirty: true,
                    shouldTouch: true,
                    shouldValidate: true,
                  })
                }
              />
            </div>

            <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {t('admin.badges.form.iconHint')}
            </div>

            <FileUpload onFilesSelected={handleFilesSelected} accept="image/*" maxFiles={1} />

            {iconValue ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 600 }}>{t('admin.badges.currentIcon')}</span>
                {isImageLike(iconValue) ? (
                  <img
                    src={iconValue}
                    alt={t('admin.badges.previewAlt')}
                    style={{
                      width: 56,
                      height: 56,
                      objectFit: 'cover',
                      borderRadius: 12,
                      border: '1px solid var(--color-border)',
                    }}
                  />
                ) : (
                  <span style={{ fontSize: 32 }}>{iconValue}</span>
                )}
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() =>
                    setValue('icon', '', {
                      shouldDirty: true,
                      shouldTouch: true,
                      shouldValidate: true,
                    })
                  }
                >
                  {t('admin.badges.removeIcon')}
                </button>
              </div>
            ) : null}
          </div>
        </div>

        <div style={{ marginTop: 16 }}>
          <FormCheckbox<BadgeEditorFormValues> name="isActive" label="admin.badges.form.isActive" />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            {t('app.cancel')}
          </button>
          <button type="submit" className="btn btn-primary" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? t('app.loading') : t('app.save')}
          </button>
        </div>
      </form>
    </FormProvider>
  );
}
