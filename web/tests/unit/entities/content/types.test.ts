import { describe, expect, it } from 'vitest';
import {
  ACCEPT_MAP,
  CONTENT_TYPES,
  LEVELS,
  QUESTION_TYPES,
  STORY_CONTENT_TYPES,
  STORY_PAGE_ASSET_TYPES,
  SUBJECTS,
  buildCmsContentFormDefaults,
  cmsContentFormSchema,
  defaultQuestion,
  isStoryContentType,
  nextKey,
  storyPageUploadSchema,
} from '@/entities/content/cms/model/types';

describe('QUESTION_TYPES constant', () => {
  it('contains all 5 expected question types', () => {
    expect(QUESTION_TYPES).toEqual(['MCQ', 'TRUE_FALSE', 'FILL_IN', 'DRAG_DROP', 'MATCHING']);
  });
});

describe('nextKey()', () => {
  it('returns a string starting with q_', () => {
    const key = nextKey();
    expect(key).toMatch(/^q_\d+$/);
  });

  it('increments on each call', () => {
    const a = nextKey();
    const b = nextKey();
    const numA = parseInt(a.slice(2), 10);
    const numB = parseInt(b.slice(2), 10);
    expect(numB).toBe(numA + 1);
  });
});

describe('defaultQuestion()', () => {
  it('creates MCQ question with options array', () => {
    const q = defaultQuestion('MCQ', 1);
    expect(q.question_type).toBe('MCQ');
    expect(Array.isArray(q.options)).toBe(true);
    expect(Array.isArray(q.correct_answer)).toBe(true);
    expect(q.points).toBe(1);
    expect(q.order).toBe(1);
  });

  it('creates TRUE_FALSE question', () => {
    const q = defaultQuestion('TRUE_FALSE', 2);
    expect(q.question_type).toBe('TRUE_FALSE');
    expect(q.options).toBeNull();
    expect(q.correct_answer).toBe(true);
  });

  it('creates FILL_IN question', () => {
    const q = defaultQuestion('FILL_IN', 3);
    expect(q.question_type).toBe('FILL_IN');
    expect(q.options).toBeNull();
    expect(Array.isArray(q.correct_answer)).toBe(true);
  });

  it('creates DRAG_DROP question with items/zones', () => {
    const q = defaultQuestion('DRAG_DROP', 4);
    expect(q.question_type).toBe('DRAG_DROP');
    const options = q.options as { items: unknown[]; zones: unknown[] };
    expect(Array.isArray(options.items)).toBe(true);
    expect(Array.isArray(options.zones)).toBe(true);
  });

  it('creates MATCHING question with left/right pairs', () => {
    const q = defaultQuestion('MATCHING', 5);
    expect(q.question_type).toBe('MATCHING');
    const options = q.options as { left: unknown[]; right: unknown[] };
    expect(Array.isArray(options.left)).toBe(true);
    expect(Array.isArray(options.right)).toBe(true);
  });
});

describe('CONTENT_TYPES constant', () => {
  it('includes video, pdf, audio, interactive, story, coloring_book', () => {
    expect(CONTENT_TYPES).toContain('video');
    expect(CONTENT_TYPES).toContain('pdf');
    expect(CONTENT_TYPES).toContain('audio');
    expect(CONTENT_TYPES).toContain('interactive');
    expect(CONTENT_TYPES).toContain('story');
    expect(CONTENT_TYPES).toContain('coloring_book');
  });
});

describe('STORY_CONTENT_TYPES constant', () => {
  it('contains story and coloring_book', () => {
    expect(STORY_CONTENT_TYPES).toContain('story');
    expect(STORY_CONTENT_TYPES).toContain('coloring_book');
  });
});

describe('LEVELS constant', () => {
  it('contains standard French school levels', () => {
    expect(LEVELS).toContain('maternelle');
    expect(LEVELS).toContain('cp');
    expect(LEVELS).toContain('terminale');
  });
});

describe('SUBJECTS constant', () => {
  it('contains expected subjects', () => {
    expect(SUBJECTS).toContain('math');
    expect(SUBJECTS).toContain('french');
    expect(SUBJECTS).toContain('arabic');
  });
});

describe('ACCEPT_MAP constant', () => {
  it('maps video to mp4/webm extensions', () => {
    expect(ACCEPT_MAP.video).toBe('.mp4,.webm');
  });

  it('maps pdf to .pdf extension', () => {
    expect(ACCEPT_MAP.pdf).toBe('.pdf');
  });

  it('maps story to image/* and .pdf', () => {
    expect(ACCEPT_MAP.story).toBe('image/*,.pdf');
  });
});

describe('STORY_PAGE_ASSET_TYPES constant', () => {
  it('contains page_image, illustration, and other types', () => {
    expect(STORY_PAGE_ASSET_TYPES).toContain('page_image');
    expect(STORY_PAGE_ASSET_TYPES).toContain('illustration');
    expect(STORY_PAGE_ASSET_TYPES).toContain('coloring_page');
    expect(STORY_PAGE_ASSET_TYPES).toContain('audio_narration');
    expect(STORY_PAGE_ASSET_TYPES).toContain('cover');
  });
});

describe('isStoryContentType()', () => {
  it('returns true for story', () => {
    expect(isStoryContentType('story')).toBe(true);
  });

  it('returns true for coloring_book', () => {
    expect(isStoryContentType('coloring_book')).toBe(true);
  });

  it('returns false for video', () => {
    expect(isStoryContentType('video')).toBe(false);
  });

  it('returns false for pdf', () => {
    expect(isStoryContentType('pdf')).toBe(false);
  });

  it('returns false for empty string', () => {
    expect(isStoryContentType('')).toBe(false);
  });

  it('returns false for unknown type', () => {
    expect(isStoryContentType('unknown')).toBe(false);
  });
});

describe('buildCmsContentFormDefaults()', () => {
  it('returns defaults when called with no arguments', () => {
    const defaults = buildCmsContentFormDefaults();
    expect(defaults.title).toBe('');
    expect(defaults.content_type).toBe('pdf');
    expect(defaults.language).toBe('fr');
    expect(defaults.status).toBe('draft');
    expect(defaults.theme_color).toBe('#4F46E5');
    expect(defaults.page_count).toBeNull();
    expect(defaults.target_age_min).toBeNull();
    expect(defaults.target_age_max).toBeNull();
    expect(defaults.letter).toBe('');
  });

  it('merges provided values over defaults', () => {
    const result = buildCmsContentFormDefaults({
      title: 'My Video',
      content_type: 'video',
      status: 'published',
    });
    expect(result.title).toBe('My Video');
    expect(result.content_type).toBe('video');
    expect(result.status).toBe('published');
    expect(result.language).toBe('fr');
  });

  it('handles null argument gracefully', () => {
    const defaults = buildCmsContentFormDefaults(null);
    expect(defaults.title).toBe('');
  });
});

describe('cmsContentFormSchema', () => {
  const validBase = {
    title: 'Test Title',
    description: '',
    content_type: 'pdf',
    level_band: 'ce2',
    subject: 'math',
    language: 'fr',
    page_count: null,
    letter: '',
    target_age_min: null,
    target_age_max: null,
    theme_color: '#4F46E5',
    status: 'draft',
  };

  it('validates a valid pdf content item', () => {
    const result = cmsContentFormSchema.safeParse(validBase);
    expect(result.success).toBe(true);
  });

  it('fails when title is empty', () => {
    const result = cmsContentFormSchema.safeParse({ ...validBase, title: '' });
    expect(result.success).toBe(false);
  });

  it('fails when language is missing', () => {
    const result = cmsContentFormSchema.safeParse({ ...validBase, language: '' });
    expect(result.success).toBe(false);
  });

  it('fails with invalid theme_color', () => {
    const result = cmsContentFormSchema.safeParse({ ...validBase, theme_color: 'not-a-color' });
    expect(result.success).toBe(false);
  });

  it('fails when story content type has missing page_count', () => {
    const result = cmsContentFormSchema.safeParse({
      ...validBase,
      content_type: 'story',
      page_count: null,
      target_age_min: 5,
      target_age_max: 8,
      theme_color: '#FF0000',
    });
    expect(result.success).toBe(false);
  });

  it('passes when story content type has all required fields', () => {
    const result = cmsContentFormSchema.safeParse({
      ...validBase,
      content_type: 'story',
      page_count: 10,
      target_age_min: 5,
      target_age_max: 8,
      theme_color: '#FF0000',
    });
    expect(result.success).toBe(true);
  });

  it('fails when target_age_min > target_age_max for story', () => {
    const result = cmsContentFormSchema.safeParse({
      ...validBase,
      content_type: 'story',
      page_count: 5,
      target_age_min: 10,
      target_age_max: 7,
      theme_color: '#FF0000',
    });
    expect(result.success).toBe(false);
  });
});

describe('storyPageUploadSchema', () => {
  it('validates a valid story page upload', () => {
    const result = storyPageUploadSchema.safeParse({
      page_number: 1,
      narration_text: 'Once upon a time...',
      has_activity: false,
      asset_type: 'page_image',
    });
    expect(result.success).toBe(true);
  });

  it('fails when page_number is 0', () => {
    const result = storyPageUploadSchema.safeParse({
      page_number: 0,
      narration_text: '',
      has_activity: false,
      asset_type: 'page_image',
    });
    expect(result.success).toBe(false);
  });

  it('fails when asset_type is empty', () => {
    const result = storyPageUploadSchema.safeParse({
      page_number: 1,
      narration_text: '',
      has_activity: false,
      asset_type: '',
    });
    expect(result.success).toBe(false);
  });
});
