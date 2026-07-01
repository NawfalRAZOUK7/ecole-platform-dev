export const EXTENDED_CONTENT_TYPES = [
  'video',
  'pdf',
  'audio',
  'interactive',
  'story',
  'coloring_book',
] as const;

export type ExtendedContentType = (typeof EXTENDED_CONTENT_TYPES)[number];

export type ContentDisplayType =
  | 'video'
  | 'audio'
  | 'document'
  | 'quiz'
  | 'story'
  | 'coloring_book'
  | 'link';

export function normalizeContentType(contentType: string | null | undefined): ContentDisplayType {
  const value = (contentType || '').toLowerCase();

  if (value === 'video') {
    return 'video';
  }

  if (value === 'audio') {
    return 'audio';
  }

  if (['document', 'pdf'].includes(value)) {
    return 'document';
  }

  if (value === 'quiz') {
    return 'quiz';
  }

  if (value === 'story') {
    return 'story';
  }

  if (value === 'coloring_book') {
    return 'coloring_book';
  }

  return 'link';
}

export function getContentTypeIcon(contentType: string | null | undefined): string {
  const normalized = normalizeContentType(contentType);

  if (normalized === 'video') {
    return '🎬';
  }

  if (normalized === 'audio') {
    return '🎧';
  }

  if (normalized === 'document') {
    return '📄';
  }

  if (normalized === 'quiz') {
    return '❓';
  }

  if (normalized === 'story') {
    return '📖';
  }

  if (normalized === 'coloring_book') {
    return '🎨';
  }

  return '🔗';
}
