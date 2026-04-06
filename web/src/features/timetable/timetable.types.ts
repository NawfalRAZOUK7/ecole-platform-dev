import type { ClassOption, ExceptionForm, SlotForm, TimetableSlot } from './timetable.service';

export const DAYS = [1, 2, 3, 4, 5, 6] as const;

const SUBJECT_COLORS: Record<string, string> = {
  math: 'var(--color-surface-primary)',
  french: 'var(--color-surface-warning)',
  arabic: 'var(--color-surface-success)',
  science: 'var(--color-surface-success)',
  history: 'var(--color-surface-secondary)',
  geography: 'var(--color-surface-warning)',
  english: 'var(--color-surface-secondary)',
  islamic_studies: 'var(--color-surface-info)',
  art: 'var(--color-surface-warning)',
  sport: 'var(--color-surface-info)',
};

export function getSubjectColor(subject: string): string {
  const key = subject.toLowerCase().replace(/\s+/g, '_');
  return SUBJECT_COLORS[key] || 'var(--color-bg-secondary)';
}

export const EMPTY_SLOT_FORM: SlotForm = {
  class_id: '',
  academic_year_id: '',
  day_of_week: 1,
  start_time: '08:00',
  end_time: '09:00',
  subject: '',
  teacher_id: '',
  room: '',
};

export const EMPTY_EXCEPTION_FORM: ExceptionForm = {
  timetable_slot_id: '',
  exception_date: new Date().toISOString().slice(0, 10),
  exception_type: 'CANCELED',
  substitute_teacher_id: '',
  new_room: '',
  reason: '',
};

export interface TimetableFiltersProps {
  classes: ClassOption[];
  isAdmin: boolean;
  selectedClassId: string;
  weekStart: string;
  weekEnd: string;
  onChangeClass: (classId: string) => void;
}

export interface TimetableGridProps {
  days: readonly number[];
  isAdmin: boolean;
  role: string;
  slotsByDay: Map<number, TimetableSlot[]>;
  onDelete: (slotId: string) => void;
  onEdit: (slot: TimetableSlot) => void;
  onException: (slot: TimetableSlot) => void;
}

export interface SlotEditorProps {
  days: readonly number[];
  exceptionForm: ExceptionForm;
  isExceptionOpen: boolean;
  isSlotOpen: boolean;
  isSaving: boolean;
  editingSlotId: string | null;
  slotForm: SlotForm;
  onChangeExceptionForm: (value: ExceptionForm) => void;
  onChangeSlotForm: (value: SlotForm) => void;
  onCloseException: () => void;
  onCloseSlot: () => void;
  onSaveException: () => void;
  onSaveSlot: () => void;
}
