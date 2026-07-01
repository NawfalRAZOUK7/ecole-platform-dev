import { api, type ApiResponse } from '@/core/api/client';

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

interface BackendTimetableConstraint {
  id: string;
  school_id: string;
  academic_year_id: string;
  constraint_type:
    | 'teacher_unavailable'
    | 'room_capacity'
    | 'max_consecutive_classes'
    | 'max_hours_per_day'
    | 'subject_hours_per_week'
    | 'no_consecutive_same_subject';
  entity_id: string | null;
  params: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
}

interface BackendTimetableConstraintPayload {
  constraint_type: BackendTimetableConstraint['constraint_type'];
  entity_id: string | null;
  params: Record<string, unknown>;
}

const DEFAULT_MAX_CONSECUTIVE_CLASSES = 3;
const SCHOOL_DAY_START = '08:00';
const SCHOOL_DAY_END = '17:00';

function toMinutes(value: string): number {
  const [hours, minutes] = value.split(':').map(Number);
  return hours * 60 + minutes;
}

function toTimeString(totalMinutes: number): string {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

function toBackendDayOfWeek(dayOfWeek: number): number {
  return Math.min(6, Math.max(0, dayOfWeek - 1));
}

function toFrontendDayOfWeek(dayOfWeek: number): number {
  return dayOfWeek >= 0 && dayOfWeek <= 5 ? dayOfWeek + 1 : dayOfWeek;
}

function normalizeTeacherAvailability(
  constraints: BackendTimetableConstraint[],
): TeacherAvailability[] {
  const grouped = new Map<
    string,
    {
      teacher_id: string;
      day_of_week: number;
      unavailable: Array<{ start: number; end: number }>;
    }
  >();

  for (const constraint of constraints) {
    if (constraint.constraint_type !== 'teacher_unavailable') continue;

    const teacherId = constraint.entity_id ?? String(constraint.params.teacher_id ?? '').trim();
    const rawDay = Number(constraint.params.day);
    const start = String(constraint.params.start ?? '');
    const end = String(constraint.params.end ?? '');

    if (!teacherId || Number.isNaN(rawDay) || !start || !end) continue;

    const key = `${teacherId}:${rawDay}`;
    const entry = grouped.get(key) ?? {
      teacher_id: teacherId,
      day_of_week: toFrontendDayOfWeek(rawDay),
      unavailable: [],
    };
    entry.unavailable.push({ start: toMinutes(start), end: toMinutes(end) });
    grouped.set(key, entry);
  }

  const schoolStart = toMinutes(SCHOOL_DAY_START);
  const schoolEnd = toMinutes(SCHOOL_DAY_END);
  const availability: TeacherAvailability[] = [];

  for (const entry of grouped.values()) {
    const blocked = [...entry.unavailable]
      .filter((window) => window.end > window.start)
      .sort((left, right) => left.start - right.start);

    let cursor = schoolStart;

    for (const window of blocked) {
      const start = Math.max(schoolStart, window.start);
      const end = Math.min(schoolEnd, window.end);
      if (start > cursor) {
        availability.push({
          teacher_id: entry.teacher_id,
          day_of_week: entry.day_of_week,
          available_from: toTimeString(cursor),
          available_until: toTimeString(start),
        });
      }
      cursor = Math.max(cursor, end);
    }

    if (cursor < schoolEnd) {
      availability.push({
        teacher_id: entry.teacher_id,
        day_of_week: entry.day_of_week,
        available_from: toTimeString(cursor),
        available_until: toTimeString(schoolEnd),
      });
    }
  }

  return availability.sort((left, right) => {
    if (left.teacher_id !== right.teacher_id) {
      return left.teacher_id.localeCompare(right.teacher_id);
    }
    if (left.day_of_week !== right.day_of_week) {
      return left.day_of_week - right.day_of_week;
    }
    return left.available_from.localeCompare(right.available_from);
  });
}

function normalizeRoomConstraints(constraints: BackendTimetableConstraint[]): RoomConstraint[] {
  return constraints
    .filter((constraint) => constraint.constraint_type === 'room_capacity')
    .map((constraint) => ({
      room_name: String(constraint.params.room ?? '').trim(),
      capacity: Number(constraint.params.max_students ?? 0),
    }))
    .filter((constraint) => constraint.room_name && constraint.capacity > 0);
}

function normalizeMaxConsecutiveClasses(constraints: BackendTimetableConstraint[]): number {
  const maxConstraint = constraints.find(
    (constraint) => constraint.constraint_type === 'max_consecutive_classes',
  );
  const max = Number(maxConstraint?.params.max ?? 0);
  return Number.isFinite(max) && max > 0 ? max : DEFAULT_MAX_CONSECUTIVE_CLASSES;
}

function normalizeConstraints(
  constraints: BackendTimetableConstraint[],
  academicYearId: string,
): TimetableConstraints {
  return {
    academic_year_id: academicYearId,
    max_consecutive_classes: normalizeMaxConsecutiveClasses(constraints),
    teacher_availability: normalizeTeacherAvailability(constraints),
    room_constraints: normalizeRoomConstraints(constraints),
  };
}

function serializeMaxConsecutiveClasses(
  maxConsecutiveClasses: number,
): BackendTimetableConstraintPayload[] {
  if (!Number.isFinite(maxConsecutiveClasses) || maxConsecutiveClasses <= 0) {
    return [];
  }

  return [
    {
      constraint_type: 'max_consecutive_classes',
      entity_id: null,
      params: {
        max: maxConsecutiveClasses,
      },
    },
  ];
}

function serializeTeacherAvailability(
  availability: TeacherAvailability[],
): BackendTimetableConstraintPayload[] {
  const schoolStart = toMinutes(SCHOOL_DAY_START);
  const schoolEnd = toMinutes(SCHOOL_DAY_END);
  const constraints: BackendTimetableConstraintPayload[] = [];

  for (const item of availability) {
    const teacherId = item.teacher_id.trim();
    const availableFrom = toMinutes(item.available_from);
    const availableUntil = toMinutes(item.available_until);

    if (!teacherId || availableUntil <= availableFrom) continue;

    if (availableFrom > schoolStart) {
      constraints.push({
        constraint_type: 'teacher_unavailable',
        entity_id: teacherId,
        params: {
          day: toBackendDayOfWeek(item.day_of_week),
          start: SCHOOL_DAY_START,
          end: item.available_from,
        },
      });
    }

    if (availableUntil < schoolEnd) {
      constraints.push({
        constraint_type: 'teacher_unavailable',
        entity_id: teacherId,
        params: {
          day: toBackendDayOfWeek(item.day_of_week),
          start: item.available_until,
          end: SCHOOL_DAY_END,
        },
      });
    }
  }

  return constraints;
}

function serializeRoomConstraints(rooms: RoomConstraint[]): BackendTimetableConstraintPayload[] {
  return rooms
    .map((room) => ({
      constraint_type: 'room_capacity' as const,
      entity_id: null,
      params: {
        room: room.room_name.trim(),
        max_students: room.capacity,
      },
    }))
    .filter((room) => String(room.params.room).trim() && Number(room.params.max_students) > 0);
}

function serializeConstraints(payload: TimetableConstraints): BackendTimetableConstraintPayload[] {
  return [
    ...serializeMaxConsecutiveClasses(payload.max_consecutive_classes),
    ...serializeTeacherAvailability(payload.teacher_availability),
    ...serializeRoomConstraints(payload.room_constraints),
  ];
}

function normalizeConstraintEnvelope(
  academicYearId: string,
  constraints: BackendTimetableConstraint[],
  timestamp: string,
  version: string,
): ApiResponse<TimetableConstraints> {
  return {
    data: normalizeConstraints(constraints, academicYearId),
    meta: {
      timestamp,
      version,
    },
  };
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

export interface TimetableSlotFilters extends Record<string, string | number | undefined> {
  class_id?: string;
  teacher_id?: string;
  academic_year_id?: string;
  day_of_week?: number;
}

export interface TimetableExceptionFilters extends Record<string, string | number | undefined> {
  timetable_slot_id?: string;
  date_from?: string;
  date_to?: string;
  exception_type?: string;
}

export interface TimetableExceptionItem {
  id: string;
  timetable_slot_id: string;
  school_id: string;
  exception_date: string;
  exception_type: string;
  substitute_teacher_id: string | null;
  new_room: string | null;
  reason: string | null;
  created_at: string;
}

export interface TimetableSlotCreatePayload {
  class_id?: string;
  academic_year_id?: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  subject: string;
  teacher_id?: string;
  room?: string | null;
  is_recurring?: boolean;
  effective_from?: string | null;
  effective_until?: string | null;
}

export interface TimetableSlotBulkCreatePayload {
  slots: TimetableSlotCreatePayload[];
}

export interface TimetableSlotUpdatePayload {
  day_of_week?: number;
  start_time?: string;
  end_time?: string;
  subject?: string;
  teacher_id?: string;
  room?: string | null;
  is_recurring?: boolean;
  effective_from?: string | null;
  effective_until?: string | null;
}

export interface TimetableExceptionCreatePayload {
  timetable_slot_id: string;
  exception_date: string;
  exception_type: string;
  substitute_teacher_id?: string;
  new_room?: string;
  reason?: string;
}

export interface TimetableSlotDeleteResponse {
  id: string;
  deleted: boolean;
}

export const timetableService = {
  listClasses() {
    return api.list<ClassOption>('/teacher/classes');
  },

  getWeeklyTimetable(classId?: string) {
    return api.get<WeeklyResponse>(
      classId ? `/timetable/class/${classId}/weekly` : '/timetable/me/weekly',
    );
  },

  listSlots(params: TimetableSlotFilters = {}) {
    return api.list<TimetableSlot>('/timetable/slots', params);
  },

  createSlot(payload: TimetableSlotCreatePayload | TimetableSlotBulkCreatePayload) {
    return api.post<TimetableSlot | TimetableSlot[]>('/timetable/slots', payload);
  },

  updateSlot(slotId: string, payload: TimetableSlotUpdatePayload) {
    return api.put<TimetableSlot>(`/timetable/slots/${slotId}`, payload);
  },

  deleteSlot(slotId: string) {
    return api.delete<TimetableSlotDeleteResponse>(`/timetable/slots/${slotId}`);
  },

  listExceptions(params: TimetableExceptionFilters = {}) {
    return api.list<TimetableExceptionItem>('/timetable/exceptions', params);
  },

  createException(payload: TimetableExceptionCreatePayload) {
    return api.post<TimetableExceptionItem>('/timetable/exceptions', payload);
  },

  // ── Generation endpoints ────────────────────────────────────────────────

  async getConstraints(academicYearId: string) {
    const response = await api.list<BackendTimetableConstraint>('/timetable/constraints', {
      academic_year_id: academicYearId,
    });

    return normalizeConstraintEnvelope(
      academicYearId,
      response.data,
      response.meta.timestamp,
      response.meta.version,
    );
  },

  async saveConstraints(payload: TimetableConstraints) {
    const response = await api.post<BackendTimetableConstraint[]>('/timetable/constraints', {
      academic_year_id: payload.academic_year_id,
      constraints: serializeConstraints(payload),
    });

    return normalizeConstraintEnvelope(
      payload.academic_year_id,
      response.data,
      response.meta.timestamp,
      response.meta.version,
    );
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

  getClassWeekly(classId: string) {
    return api.get<WeeklyResponse>(`/timetable/class/${classId}/weekly`);
  },

  getTeacherWeekly(teacherId: string) {
    return api.get<WeeklyResponse>(`/timetable/teacher/${teacherId}/weekly`);
  },

  getMyWeekly() {
    return api.get<WeeklyResponse>('/timetable/me/weekly');
  },
};
