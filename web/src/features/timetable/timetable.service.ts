import { api } from '@/services/api/client';

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
};
