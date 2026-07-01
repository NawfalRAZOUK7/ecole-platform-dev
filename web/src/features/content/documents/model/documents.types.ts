import type { DocumentsTab } from '../api/documents.api';

export interface DocumentsPageProps {
  initialTab?: DocumentsTab;
}

export type DocumentViewMode = 'grid' | 'list';

export const RESOURCE_TYPES = [
  'lesson_plan',
  'worksheet',
  'presentation',
  'exam_template',
  'reference',
] as const;
