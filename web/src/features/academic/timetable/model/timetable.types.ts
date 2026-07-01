import type { ClassOption, ExceptionForm, SlotForm, TimetableSlot } from '../api/timetable.api';
export { getSubjectColor } from '@/shared/ui/tokens';

export const DAYS = [1, 2, 3, 4, 5, 6] as const;

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
