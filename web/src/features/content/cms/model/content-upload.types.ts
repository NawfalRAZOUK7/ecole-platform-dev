import { z } from 'zod';

export const CONTENT_TYPES = [
  'video',
  'pdf',
  'audio',
  'interactive',
  'story',
  'coloring_book',
] as const;

export const STORY_CONTENT_TYPES = ['story', 'coloring_book'] as const;

export type CmsContentType = (typeof CONTENT_TYPES)[number];
export type StoryContentType = (typeof STORY_CONTENT_TYPES)[number];

export const LEVELS = [
  'maternelle',
  'cp',
  'ce1',
  'ce2',
  'cm1',
  'cm2',
  '6eme',
  '5eme',
  '4eme',
  '3eme',
  '2nde',
  '1ere',
  'terminale',
];

export const SUBJECTS = [
  'math',
  'french',
  'arabic',
  'science',
  'history',
  'geography',
  'english',
  'islamic_studies',
  'art',
  'sport',
];

export const ACCEPT_MAP: Record<string, string> = {
  video: '.mp4,.webm',
  pdf: '.pdf',
  audio: '.mp3,.wav,.ogg',
  interactive: '*',
  story: 'image/*,.pdf',
  coloring_book: 'image/*,.pdf',
};

export const STORY_PAGE_ASSET_TYPES = [
  'page_image',
  'illustration',
  'coloring_page',
  'audio_narration',
  'cover',
] as const;

export type StoryPageAssetType = (typeof STORY_PAGE_ASSET_TYPES)[number];

export interface CmsStoryMetadataFields {
  page_count: number | null;
  letter: string;
  target_age_min: number | null;
  target_age_max: number | null;
  theme_color: string;
}

export interface CmsContentFormValues extends CmsStoryMetadataFields {
  title: string;
  description: string;
  content_type: CmsContentType;
  level_band: string;
  subject: string;
  language: string;
  status: 'draft' | 'published' | 'archived';
}

export interface CmsStoryPage {
  id: string;
  content_item_id: string;
  file_path: string;
  checksum: string | null;
  mime_type: string | null;
  file_size: number | null;
  page_number: number | null;
  narration_text: string | null;
  has_activity: boolean;
  asset_type: string | null;
}

export interface StoryPageUploadValues {
  page_number: number;
  narration_text: string;
  has_activity: boolean;
  asset_type: string;
}

export interface BulkUploadResult {
  name: string;
  ok: boolean;
  error?: string;
}

function parseOptionalNumber(value: unknown): number | null | unknown {
  if (value === '' || value === null || value === undefined) {
    return null;
  }

  if (typeof value === 'number') {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? value : parsed;
  }

  return value;
}

export function isStoryContentType(value: string): value is StoryContentType {
  return STORY_CONTENT_TYPES.includes(value as StoryContentType);
}

const optionalPageCountField = z.preprocess(
  parseOptionalNumber,
  z.number().int().min(1, 'cms.validation.pageCount').nullable(),
);

const optionalAgeField = z.preprocess(
  parseOptionalNumber,
  z
    .number()
    .int()
    .min(2, 'cms.validation.targetAge')
    .max(18, 'cms.validation.targetAge')
    .nullable(),
);

export const cmsContentFormSchema = z
  .object({
    title: z.string().trim().min(1, 'cms.validation.title').max(300, 'cms.validation.title'),
    description: z.string().trim().max(2000, 'cms.validation.description'),
    content_type: z.enum(CONTENT_TYPES, {
      message: 'cms.validation.contentType',
    }),
    level_band: z.string().trim(),
    subject: z.string().trim(),
    language: z
      .string()
      .trim()
      .min(1, 'cms.validation.language')
      .max(10, 'cms.validation.language'),
    page_count: optionalPageCountField,
    letter: z
      .string()
      .trim()
      .max(3, 'cms.validation.letter')
      .refine((value) => value === '' || value.length >= 1, 'cms.validation.letter'),
    target_age_min: optionalAgeField,
    target_age_max: optionalAgeField,
    theme_color: z
      .string()
      .trim()
      .regex(/^#[0-9a-fA-F]{6}$/, 'cms.validation.themeColor'),
    status: z.enum(['draft', 'published', 'archived']),
  })
  .superRefine((values, context) => {
    if (!isStoryContentType(values.content_type)) {
      return;
    }

    if (values.page_count === null) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'cms.validation.pageCountRequired',
        path: ['page_count'],
      });
    }

    if (values.target_age_min === null) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'cms.validation.targetAgeRequired',
        path: ['target_age_min'],
      });
    }

    if (values.target_age_max === null) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'cms.validation.targetAgeRequired',
        path: ['target_age_max'],
      });
    }

    if (
      values.target_age_min !== null &&
      values.target_age_max !== null &&
      values.target_age_min > values.target_age_max
    ) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'cms.validation.targetAgeRange',
        path: ['target_age_max'],
      });
    }
  });

export const storyPageUploadSchema = z.object({
  page_number: z.coerce.number().int().min(1, 'cms.storyPages.validation.pageNumber'),
  narration_text: z.string().trim().max(2000, 'cms.storyPages.validation.narration'),
  has_activity: z.boolean(),
  asset_type: z
    .string()
    .trim()
    .min(1, 'cms.storyPages.validation.assetType')
    .max(50, 'cms.storyPages.validation.assetType'),
});

export function buildCmsContentFormDefaults(
  values?: Partial<CmsContentFormValues> | null,
): CmsContentFormValues {
  return {
    title: values?.title ?? '',
    description: values?.description ?? '',
    content_type: values?.content_type ?? 'pdf',
    level_band: values?.level_band ?? '',
    subject: values?.subject ?? '',
    language: values?.language ?? 'fr',
    page_count: values?.page_count ?? null,
    letter: values?.letter ?? '',
    target_age_min: values?.target_age_min ?? null,
    target_age_max: values?.target_age_max ?? null,
    theme_color: values?.theme_color ?? '#4F46E5',
    status: values?.status ?? 'draft',
  };
}
