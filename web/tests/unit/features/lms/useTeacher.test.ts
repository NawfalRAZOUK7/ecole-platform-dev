import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useTeacherClasses,
  useTeacherPeriods,
  useTeacherClassStudents,
  useTeacherCourses,
  useCreateCourse,
  useTeacherAssignments,
  useCreateAssignment,
  useTeacherAssessments,
  useCreateAssessment,
  usePublishAssessment,
  useCreateAttendanceSession,
  useTeacherClassProgress,
  useTeacherContentLibrary,
  useAssignableClasses,
  useAssignContent,
  useTeacherQuizzes,
  useCreateQuiz,
  usePublishQuiz,
  useTeacherSubmissions,
  useGradeSubmission,
  useCreateClassAssignment,
  useClassDetail,
  useSubmitAssessmentResults,
  teacherQueryKeys,
} from '@/features/lms/teacher/model/useTeacher';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) =>
    QueryClientProvider({ client: queryClient, children });
}

function apiResponse<T>(data: T) {
  return HttpResponse.json({
    data,
    meta: { timestamp: new Date().toISOString(), version: 'test' },
  });
}

function apiListResponse<T>(data: T[], hasMore = false) {
  return HttpResponse.json({
    data,
    meta: {
      next_cursor: null,
      has_more: hasMore,
      timestamp: new Date().toISOString(),
      version: 'test',
    },
  });
}

function apiErrorResponse(message = 'Server error') {
  return HttpResponse.json(
    {
      error: {
        code: 'ERR-SYS-500',
        message,
        category: 'system',
        retryable: false,
        timestamp: new Date().toISOString(),
      },
    },
    { status: 500 },
  );
}

describe('teacherQueryKeys', () => {
  it('generates stable query keys', () => {
    expect(teacherQueryKeys.all).toEqual(['teacher']);
    expect(teacherQueryKeys.classes()).toEqual(['teacher', 'classes']);
    expect(teacherQueryKeys.periods()).toEqual(['teacher', 'periods']);
    expect(teacherQueryKeys.classStudents('c1')).toEqual(['teacher', 'class-students', 'c1']);
    expect(teacherQueryKeys.courses({})).toEqual(['teacher', 'courses', {}]);
    expect(teacherQueryKeys.classProgress('c1')).toEqual(['teacher', 'class-progress', 'c1']);
    expect(teacherQueryKeys.quizzes()).toEqual(['teacher', 'quizzes']);
  });
});

describe('useTeacherClasses', () => {
  it('fetches classes successfully', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () =>
        apiResponse([{ id: 'class-1', code: '6A', name: 'Class 6A' }]),
      ),
    );
    const { result } = renderHook(() => useTeacherClasses(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].id).toBe('class-1');
  });

  it('handles error state', async () => {
    server.use(http.get('/api/v1/teacher/classes', () => apiErrorResponse()));
    const { result } = renderHook(() => useTeacherClasses(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it('respects enabled=false', () => {
    const { result } = renderHook(() => useTeacherClasses(false), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useTeacherPeriods', () => {
  it('fetches periods successfully', async () => {
    server.use(
      http.get('/api/v1/teacher/periods', () =>
        apiResponse([
          { id: 'p1', label: 'Term 1', date_start: '2026-09-01', date_end: '2026-12-20' },
        ]),
      ),
    );
    const { result } = renderHook(() => useTeacherPeriods(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('p1');
  });

  it('handles error state', async () => {
    server.use(http.get('/api/v1/teacher/periods', () => apiErrorResponse()));
    const { result } = renderHook(() => useTeacherPeriods(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useTeacherClassStudents', () => {
  it('fetches students when classId provided', async () => {
    server.use(
      http.get('/api/v1/teacher/classes/:classId/students', () =>
        apiResponse([{ id: 's1', full_name: 'Alice', email: 'alice@test.com' }]),
      ),
    );
    const { result } = renderHook(() => useTeacherClassStudents('class-1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('s1');
  });

  it('does not fetch when classId is null', () => {
    const { result } = renderHook(() => useTeacherClassStudents(null), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useTeacherCourses', () => {
  it('fetches courses as infinite query', async () => {
    server.use(
      http.get('/api/v1/courses', () =>
        apiListResponse([
          { id: 'course-1', class_id: 'c1', title: 'Math', description: null, status: 'active' },
        ]),
      ),
    );
    const { result } = renderHook(() => useTeacherCourses({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data).toHaveLength(1);
  });

  it('handles error state', async () => {
    server.use(http.get('/api/v1/courses', () => apiErrorResponse()));
    const { result } = renderHook(() => useTeacherCourses({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCreateCourse', () => {
  it('calls mutation and is idle initially', () => {
    const { result } = renderHook(() => useCreateCourse(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('succeeds on post', async () => {
    server.use(
      http.post('/api/v1/courses', () => apiResponse(null)),
      http.get('/api/v1/courses', () => apiListResponse([])),
    );
    const { result } = renderHook(() => useCreateCourse(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({ title: 'New Course', class_id: 'c1' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useTeacherAssignments', () => {
  it('fetches assignments', async () => {
    server.use(
      http.get('/api/v1/assignments', () =>
        apiListResponse([
          {
            id: 'a1',
            course_id: 'c1',
            title: 'HW 1',
            description: null,
            due_at: null,
            total_points: 10,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useTeacherAssignments({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data[0].id).toBe('a1');
  });
});

describe('useCreateAssignment', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateAssignment(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useTeacherAssessments', () => {
  it('fetches assessments', async () => {
    server.use(
      http.get('/api/v1/assessments', () =>
        apiListResponse([
          {
            id: 'as1',
            class_id: 'c1',
            title: 'Quiz 1',
            due_at: null,
            window_end: null,
            total_points: 20,
            status: 'draft',
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useTeacherAssessments({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data[0].id).toBe('as1');
  });
});

describe('useCreateAssessment', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateAssessment(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('usePublishAssessment', () => {
  it('publishes successfully', async () => {
    server.use(
      http.post('/api/v1/assessments/:id/publish', () => apiResponse(null)),
      http.get('/api/v1/assessments', () => apiListResponse([])),
    );
    const { result } = renderHook(() => usePublishAssessment(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync('as-1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCreateAttendanceSession', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateAttendanceSession(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useTeacherClassProgress', () => {
  it('fetches class progress when classId provided', async () => {
    server.use(
      http.get('/api/v1/progress/class/:classId', () =>
        apiResponse({
          data: {
            class_id: 'c1',
            class_name: 'Class 6A',
            student_count: 20,
            students: [],
            class_averages: { grade_average: 15, attendance_rate: 90, content_completion_rate: 80 },
            charts: {
              grade_comparison: { labels: [], datasets: [] },
              attendance_comparison: { labels: [], datasets: [] },
            },
          },
        }),
      ),
    );
    const { result } = renderHook(() => useTeacherClassProgress('c1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.class_id).toBe('c1');
  });

  it('does not fetch without classId', () => {
    const { result } = renderHook(() => useTeacherClassProgress(null), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useTeacherContentLibrary', () => {
  it('fetches content library', async () => {
    server.use(
      http.get('/api/v1/content/library', () =>
        apiListResponse([
          {
            id: 'ci1',
            school_id: 's1',
            title: 'Story 1',
            content_type: 'pdf',
            level_band: null,
            language: 'fr',
            subject: null,
            description: null,
            origin: 'school',
            status: 'active',
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useTeacherContentLibrary({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data[0].id).toBe('ci1');
  });
});

describe('useAssignableClasses', () => {
  it('fetches assignable classes', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () =>
        apiListResponse([{ id: 'class-1', code: '6A', name: 'Class 6A' }]),
      ),
    );
    const { result } = renderHook(() => useAssignableClasses(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useAssignContent', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useAssignContent(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useTeacherQuizzes', () => {
  it('fetches quizzes', async () => {
    server.use(
      http.get('/api/v1/quizzes', () =>
        apiListResponse([
          {
            id: 'q1',
            school_id: null,
            title: 'Quiz 1',
            description: null,
            subject: null,
            level_band: null,
            difficulty: null,
            status: 'draft',
            question_count: 5,
            total_points: 50,
            time_limit_minutes: null,
            max_attempts: 1,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useTeacherQuizzes(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data[0].id).toBe('q1');
  });
});

describe('useCreateQuiz', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateQuiz(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('usePublishQuiz', () => {
  it('publishes a quiz', async () => {
    server.use(
      http.post('/api/v1/quizzes/:id/publish', () => apiResponse(null)),
      http.get('/api/v1/quizzes', () => apiListResponse([])),
    );
    const { result } = renderHook(() => usePublishQuiz(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync('q-1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe('q-1');
  });
});

describe('useTeacherSubmissions', () => {
  it('fetches submissions', async () => {
    server.use(
      http.get('/api/v1/teacher/submissions', () =>
        apiListResponse([
          {
            id: 'sub1',
            assignment_id: 'a1',
            assignment_title: 'HW',
            assignment_total_points: 10,
            student_id: 's1',
            student_name: 'Alice',
            status: 'submitted',
            submitted_at: null,
            grade: null,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useTeacherSubmissions({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data[0].id).toBe('sub1');
  });
});

describe('useGradeSubmission', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useGradeSubmission(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useCreateClassAssignment', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateClassAssignment(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useClassDetail', () => {
  it('fetches class detail', async () => {
    server.use(
      http.get('/api/v1/classes/:classId', () =>
        apiResponse({ id: 'c1', code: '6A', name: 'Class 6A', academic_year_id: 'ay1' }),
      ),
    );
    const { result } = renderHook(() => useClassDetail('c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.id).toBe('c1');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/classes/:classId', () => apiErrorResponse()));
    const { result } = renderHook(() => useClassDetail('c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useSubmitAssessmentResults', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useSubmitAssessmentResults(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});
