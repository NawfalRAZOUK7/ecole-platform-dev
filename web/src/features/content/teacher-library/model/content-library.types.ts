import type { FormEvent } from 'react';
import type { ClassOption, ContentItem } from '@/features/lms/teacher/api/teacher.api';

export type ContentLibraryTab = 'browse' | 'upload' | 'submissions';

export const SUBJECT_OPTIONS = [
  'math',
  'french',
  'arabic',
  'science',
  'history',
  'geography',
  'english',
] as const;
export const LEVEL_OPTIONS = ['primaire', 'college', 'lycee'] as const;
export const REVIEW_STATUS_OPTIONS = ['PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED'] as const;

export interface ContentFiltersProps {
  filterLevel: string;
  filterOrigin: string;
  filterSubject: string;
  filterType: string;
  onChangeLevel: (value: string) => void;
  onChangeOrigin: (value: string) => void;
  onChangeSubject: (value: string) => void;
  onChangeType: (value: string) => void;
}

export interface ContentCardProps {
  item: ContentItem;
  reviewPending: boolean;
  onAssign?: (item: ContentItem) => void;
  onSubmitForReview: (contentId: string) => void;
}

export interface AssignContentModalProps {
  assignClassId: string;
  assignItem: ContentItem | null;
  assignNotes: string;
  classes: ClassOption[];
  isPending: boolean;
  onChangeClassId: (value: string) => void;
  onChangeNotes: (value: string) => void;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}
