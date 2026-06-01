import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { timetableService } from '@/features/academic/timetable/api/timetable.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

const slotData = {
  id: 'slot-1',
  day_of_week: 1,
  start_time: '08:00',
  end_time: '09:00',
  subject: 'Math',
  teacher_id: 'teacher-1',
  room: 'Room 1',
  is_recurring: true,
  class_id: 'class-1',
};

const weeklyData = {
  academic_year_id: 'year-1',
  week_start: '2025-01-06',
  week_end: '2025-01-10',
  slots: [slotData],
};

const jobData = {
  job_id: 'job-1',
  status: 'pending',
  progress: 0,
  error: null,
  created_at: new Date().toISOString(),
};

describe('timetableService', () => {
  it('listClasses returns class options', async () => {
    const classOpts = [{ id: 'c1', code: 'C1', name: 'Class 1' }];
    server.use(
      http.get('/api/v1/teacher/classes', () =>
        HttpResponse.json({ data: classOpts, meta: listMeta }),
      ),
    );
    const result = await timetableService.listClasses();
    expect(result.data).toEqual(classOpts);
  });

  it('getWeeklyTimetable without classId calls /timetable/me/weekly', async () => {
    server.use(
      http.get('/api/v1/timetable/me/weekly', () => HttpResponse.json({ data: weeklyData, meta })),
    );
    const result = await timetableService.getWeeklyTimetable();
    expect(result.data.slots).toHaveLength(1);
  });

  it('getWeeklyTimetable with classId calls /timetable/class/:id/weekly', async () => {
    server.use(
      http.get('/api/v1/timetable/class/class-1/weekly', () =>
        HttpResponse.json({ data: weeklyData, meta }),
      ),
    );
    const result = await timetableService.getWeeklyTimetable('class-1');
    expect(result.data.academic_year_id).toBe('year-1');
  });

  it('listSlots returns timetable slots', async () => {
    server.use(
      http.get('/api/v1/timetable/slots', () =>
        HttpResponse.json({ data: [slotData], meta: listMeta }),
      ),
    );
    const result = await timetableService.listSlots({ class_id: 'class-1' });
    expect(result.data).toHaveLength(1);
  });

  it('createSlot posts a new slot', async () => {
    server.use(
      http.post('/api/v1/timetable/slots', () => HttpResponse.json({ data: slotData, meta })),
    );
    const result = await timetableService.createSlot({
      day_of_week: 1,
      start_time: '08:00',
      end_time: '09:00',
      subject: 'Math',
    });
    expect(result.data).toMatchObject({ id: 'slot-1' });
  });

  it('updateSlot puts slot data', async () => {
    server.use(
      http.put('/api/v1/timetable/slots/slot-1', () =>
        HttpResponse.json({ data: { ...slotData, subject: 'Science' }, meta }),
      ),
    );
    const result = await timetableService.updateSlot('slot-1', { subject: 'Science' });
    expect(result.data.subject).toBe('Science');
  });

  it('deleteSlot deletes a slot', async () => {
    server.use(
      http.delete('/api/v1/timetable/slots/slot-1', () =>
        HttpResponse.json({ data: { id: 'slot-1', deleted: true }, meta }),
      ),
    );
    const result = await timetableService.deleteSlot('slot-1');
    expect(result.data.deleted).toBe(true);
  });

  it('listExceptions returns exceptions', async () => {
    const exc = {
      id: 'exc-1',
      timetable_slot_id: 'slot-1',
      school_id: 'school-1',
      exception_date: '2025-01-07',
      exception_type: 'cancelled',
      substitute_teacher_id: null,
      new_room: null,
      reason: null,
      created_at: new Date().toISOString(),
    };
    server.use(
      http.get('/api/v1/timetable/exceptions', () =>
        HttpResponse.json({ data: [exc], meta: listMeta }),
      ),
    );
    const result = await timetableService.listExceptions();
    expect(result.data).toHaveLength(1);
  });

  it('createException posts a new exception', async () => {
    const exc = {
      id: 'exc-1',
      timetable_slot_id: 'slot-1',
      school_id: 'school-1',
      exception_date: '2025-01-07',
      exception_type: 'cancelled',
      substitute_teacher_id: null,
      new_room: null,
      reason: null,
      created_at: new Date().toISOString(),
    };
    server.use(
      http.post('/api/v1/timetable/exceptions', () => HttpResponse.json({ data: exc, meta })),
    );
    const result = await timetableService.createException({
      timetable_slot_id: 'slot-1',
      exception_date: '2025-01-07',
      exception_type: 'cancelled',
    });
    expect(result.data.id).toBe('exc-1');
  });

  it('getConstraints returns normalized constraints', async () => {
    server.use(
      http.get('/api/v1/timetable/constraints', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await timetableService.getConstraints('year-1');
    expect(result.data.academic_year_id).toBe('year-1');
    expect(result.data.max_consecutive_classes).toBe(3);
  });

  it('saveConstraints posts constraints and returns normalized', async () => {
    server.use(
      http.post('/api/v1/timetable/constraints', () => HttpResponse.json({ data: [], meta })),
    );
    const result = await timetableService.saveConstraints({
      academic_year_id: 'year-1',
      max_consecutive_classes: 4,
      teacher_availability: [],
      room_constraints: [],
    });
    expect(result.data.academic_year_id).toBe('year-1');
  });

  it('triggerGeneration posts generate endpoint', async () => {
    server.use(
      http.post('/api/v1/timetable/generate', () => HttpResponse.json({ data: jobData, meta })),
    );
    const result = await timetableService.triggerGeneration({ academic_year_id: 'year-1' });
    expect(result.data.job_id).toBe('job-1');
  });

  it('getGenerationJob returns job status', async () => {
    server.use(
      http.get('/api/v1/timetable/generate/job-1', () =>
        HttpResponse.json({ data: jobData, meta }),
      ),
    );
    const result = await timetableService.getGenerationJob('job-1');
    expect(result.data.status).toBe('pending');
  });

  it('getGenerationPreview returns preview', async () => {
    const preview = { job_id: 'job-1', slots: [], warnings: [] };
    server.use(
      http.get('/api/v1/timetable/generate/job-1/preview', () =>
        HttpResponse.json({ data: preview, meta }),
      ),
    );
    const result = await timetableService.getGenerationPreview('job-1');
    expect(result.data.job_id).toBe('job-1');
  });

  it('applyGeneration posts apply endpoint', async () => {
    const applyResult = { applied: 10, skipped: 0 };
    server.use(
      http.post('/api/v1/timetable/generate/job-1/apply', () =>
        HttpResponse.json({ data: applyResult, meta }),
      ),
    );
    const result = await timetableService.applyGeneration('job-1');
    expect(result.data.applied).toBe(10);
  });

  it('getClassWeekly returns class weekly timetable', async () => {
    server.use(
      http.get('/api/v1/timetable/class/class-1/weekly', () =>
        HttpResponse.json({ data: weeklyData, meta }),
      ),
    );
    const result = await timetableService.getClassWeekly('class-1');
    expect(result.data.week_start).toBe('2025-01-06');
  });

  it('getTeacherWeekly returns teacher weekly timetable', async () => {
    server.use(
      http.get('/api/v1/timetable/teacher/teacher-1/weekly', () =>
        HttpResponse.json({ data: weeklyData, meta }),
      ),
    );
    const result = await timetableService.getTeacherWeekly('teacher-1');
    expect(result.data).toBeDefined();
  });

  it('getMyWeekly returns my weekly timetable', async () => {
    server.use(
      http.get('/api/v1/timetable/me/weekly', () => HttpResponse.json({ data: weeklyData, meta })),
    );
    const result = await timetableService.getMyWeekly();
    expect(result.data.slots).toHaveLength(1);
  });
});
