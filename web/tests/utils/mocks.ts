import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import {
  createAttendanceRecord,
  createBudget,
  createClass,
  createGrade,
  createInvoice,
  createStudent,
  createUser,
  type AttendanceClassResponse,
} from './factories';

export function apiResponse<T>(data: T) {
  return HttpResponse.json({
    data,
    meta: {
      timestamp: new Date().toISOString(),
      version: 'test',
    },
  });
}

export function apiListResponse<T>(data: T[]) {
  return HttpResponse.json({
    data,
    meta: {
      next_cursor: null,
      has_more: false,
      timestamp: new Date().toISOString(),
      version: 'test',
    },
  });
}

export function apiErrorResponse(message: string, status = 500) {
  return HttpResponse.json(
    {
      error: {
        code: `ERR-SYS-${status}`,
        message,
        category: 'system',
        retryable: false,
        timestamp: new Date().toISOString(),
      },
    },
    { status },
  );
}

export const handlers = [
  http.get('/api/v1/auth/me', () => {
    return apiResponse(createUser());
  }),

  http.get('/api/v1/me/profile', () => {
    const user = createUser({ role: 'STD', full_name: 'Student Example' });

    return apiResponse({
      user_id: user.id,
      email: user.email,
      full_name: user.full_name,
      phone: null,
      role: user.role,
      school_id: user.school_id,
      student_profile: {
        student_number: 'STD-001',
        date_of_birth: '2017-09-01',
        class_level: 'ce2',
        nationality: 'MA',
      },
      parent_profile: null,
      teacher_profile: null,
    });
  }),

  http.get('/api/v1/teacher/classes', () => {
    return apiResponse([
      createClass({ id: 'class-1', code: '6A', name: 'Class 6A' }),
      createClass({ id: 'class-2', code: '6B', name: 'Class 6B' }),
    ]);
  }),

  http.get('/api/v1/teacher/periods', () => {
    return apiResponse([
      {
        id: 'period-1',
        label: 'Term 1',
        date_start: '2026-09-01',
        date_end: '2026-12-20',
      },
      {
        id: 'period-2',
        label: 'Term 2',
        date_start: '2027-01-10',
        date_end: '2027-03-30',
      },
    ]);
  }),

  http.get('/api/v1/attendance/class/:id', ({ params }) => {
    const classId = String(params.id);
    const studentA = createStudent({ full_name: 'Amine Student' });
    const studentB = createStudent({ full_name: 'Salma Student' });
    const payload: AttendanceClassResponse = {
      class_id: classId,
      stats: {
        total_students: 2,
        attendance_rate: 95,
        absent_count: 1,
        late_count: 0,
      },
      records: [
        createAttendanceRecord({
          class_id: classId,
          student_id: studentA.id,
          student_name: studentA.full_name,
          status: 'present',
        }),
        createAttendanceRecord({
          class_id: classId,
          student_id: studentB.id,
          student_name: studentB.full_name,
          status: 'absent',
          justified: true,
        }),
      ],
    };

    return apiResponse(payload);
  }),

  http.post('/api/v1/attendance/class/:id', () => {
    return apiResponse({});
  }),

  http.get('/api/v1/gradebook/:classId/:periodId', ({ params }) => {
    const classItem = createClass({ id: String(params.classId) });
    const studentA = createStudent({ full_name: 'Amine Student' });
    const studentB = createStudent({ full_name: 'Salma Student' });
    const quiz = createGrade({ assessment_id: 'assessment-quiz', title: 'Quiz 1', value: 16 });
    const exam = createGrade({
      assessment_id: 'assessment-exam',
      title: 'Exam 1',
      type: 'exam',
      weight: 2,
      value: 18,
    });
    const payload = {
      class_id: classItem.id,
      class_name: classItem.name,
      categories: [
        { id: 'category-quiz', name: 'Quiz', weight: quiz.weight },
        { id: 'category-exam', name: 'Exam', weight: exam.weight },
      ],
      assignments: [
        {
          assignment_id: quiz.assessment_id,
          title: quiz.title,
          category_id: 'category-quiz',
          total_points: 20,
          due_at: quiz.date,
        },
        {
          assignment_id: exam.assessment_id,
          title: exam.title,
          category_id: 'category-exam',
          total_points: 20,
          due_at: exam.date,
        },
      ],
      rows: [
        {
          student_id: studentA.id,
          student_name: studentA.full_name,
          assignments: [
            { assignment_id: quiz.assessment_id, score: quiz.value },
            { assignment_id: exam.assessment_id, score: exam.value },
          ],
          weighted_average: 17.3,
        },
        {
          student_id: studentB.id,
          student_name: studentB.full_name,
          assignments: [
            { assignment_id: quiz.assessment_id, score: 14 },
            { assignment_id: exam.assessment_id, score: 15 },
          ],
          weighted_average: 14.7,
        },
      ],
    };

    return apiResponse(payload);
  }),

  http.get('/api/v1/gradebook/transcript/:studentId', ({ params }) => {
    return apiResponse({
      student_id: String(params.studentId),
      student_name: 'Amine Student',
      periods: [
        {
          class_id: 'class-1',
          class_name: 'Class 6A',
          period_id: 'period-1',
          period_label: 'Term 1',
          weighted_average: 16,
          class_rank: 1,
        },
      ],
    });
  }),

  http.get('/api/v1/invoices', () => {
    return apiListResponse([
      createInvoice(),
      createInvoice({ id: 'invoice-2', status: 'paid', invoice_number: 'INV-2026-002' }),
    ]);
  }),

  http.get('/api/v1/budgets', () => {
    return apiListResponse([
      createBudget(),
      createBudget({ id: 'budget-2', name: 'Facilities', status: 'frozen' }),
    ]);
  }),
];

export const server = setupServer(...handlers);
