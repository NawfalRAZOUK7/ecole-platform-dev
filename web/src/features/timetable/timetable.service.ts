import { api } from '@/services/api/client';

// ─── Generation types ───────────────────────────────────────────────────────

export interface TeacherAvailability {
  teacher_id: string;
  day_of_week: number; // 1=Mon … 6=Sat
  available_from: string; // HH:MM
  available_until: string; // HH:MM
}

export interface RoomConstraint {
  room_name: string;
  capacity: number;
}

export interface TimetableConstraints {
  academic_year_id: string;
  max_consecutive_classes: number;
  teacher_availability: TeacherAvailability[];
  room_constraints: RoomConstraint[];
}

export type GenerationJobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface GenerationJob {
  job_id: string;
  status: GenerationJobStatus;
  progress: number; // 0-100
  error: string | null;
  created_at: string;
}

export interface GeneratedSlot {
  day_of_week: number;
  start_time: string;
  end_time: string;
  subject: string;
  teacher_id: string;
  room: string | null;
  class_id: string;
}

export interface GenerationPreview {
  job_id: string;
  slots: GeneratedSlot[];
  warnings: string[];
}

export interface ApplyResult {
  applied: number;
  skipped: number;
}

// ─── Timetable viewing types ─────────────────────────────────────────────────

export interface TimetableSlot {
  id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  subject: string;
  teacher_id: string;
  room: string | null;
  is_recurring: boolean;
  class_id: string;
  class_name?: string;
  exception?: {
    exception_type: string;
    substitute_teacher_id?: string;
    new_room?: string;
    reason?: string;
  } | null;
}

export interface WeeklyResponse {
  academic_year_id: string;
  week_start: string;
  week_end: string;
  slots: TimetableSlot[];
}

export interface SlotForm {
  class_id: string;
  academic_year_id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  subject: string;
  teacher_id: string;
  room: string;
}

export interface ExceptionForm {
  timetable_slot_id: string;
  exception_date: string;
  exception_type: string;
  substitute_teacher_id: string;
  new_room: string;
  reason: string;
}

export interface ClassOption {
  id: string;
  code: string;
  name: string;
}

export const timetableService = {
  listClasses() {
    return api.list<ClassOption>('/classes');
  },

  getWeeklyTimetable(classId?: string) {
    return api.get<WeeklyResponse>(classId ? `/timetable/class/${classId}/weekly` : '/timetable/me/weekly');
  },

  createSlot(payload: Record<string, unknown>) {
    return api.post<void>('/timetable/slots', payload);
  },

  updateSlot(slotId: string, payload: Record<string, unknown>) {
    return api.put<void>(`/timetable/slots/${slotId}`, payload);
  },

  deleteSlot(slotId: string) {
    return api.delete<void>(`/timetable/slots/${slotId}`);
  },

  createException(payload: Record<string, unknown>) {
    return api.post<void>('/timetable/exceptions', payload);
  },

  // ── Generation endpoints ────────────────────────────────────────────────

  getConstraints() {
    return api.get<TimetableConstraints>('/timetable/constraints');
  },

  saveConstraints(payload: TimetableConstraints) {
    return api.post<TimetableConstraints>('/timetable/constraints', payload);
  },

  triggerGeneration(payload: { academic_year_id: string }) {
    return api.post<GenerationJob>('/timetable/generate', payload);
  },

  getGenerationJob(jobId: string) {
    return api.get<GenerationJob>(`/timetable/generate/${jobId}`);
  },

  getGenerationPreview(jobId: string) {
    return api.get<GenerationPreview>(`/timetable/generate/${jobId}/preview`);
  },

  applyGeneration(jobId: string) {
    return api.post<ApplyResult>(`/timetable/generate/${jobId}/apply`, {});
  },
};
