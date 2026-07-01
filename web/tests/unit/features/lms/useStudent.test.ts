import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect, beforeEach } from 'vitest';
import {
  usePublishedQuizzes,
  useQuizDetail,
  useStartQuizAttempt,
  useRespondToAttempt,
  useSubmitAttempt,
  useAttemptResults,
  useStudentClasses,
  useStudentWork,
  useClassStudentWork,
  useCreateEnrollment,
  useStudentClassContent,
  useUpdateContentProgress,
  studentQueryKeys,
} from '@/features/lms/student/model/useStudent';

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

function apiListResponse<T>(data: T[]) {
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

function apiErrorResponse() {
  return HttpResponse.json(
    {
      error: {
        code: 'ERR-SYS-500',
        message: 'fail',
        category: 'system',
        retryable: false,
        timestamp: new Date().toISOString(),
      },
    },
    { status: 500 },
  );
}

describe('studentQueryKeys', () => {
  it('generates correct keys', () => {
    expect(studentQueryKeys.all).toEqual(['student']);
    expect(studentQueryKeys.quizzes()).toEqual(['student', 'quizzes']);
    expect(studentQueryKeys.studentWork()).toEqual(['student', 'student-work']);
    expect(studentQueryKeys.classStudentWork('c1')).toEqual([
      'student',
      'class-student-work',
      'c1',
    ]);
    expect(studentQueryKeys.quizDetail('q1')).toEqual(['student', 'quiz-detail', 'q1']);
    expect(studentQueryKeys.attemptResults('a1')).toEqual(['student', 'attempt-results', 'a1']);
    expect(studentQueryKeys.classes()).toEqual(['student', 'classes']);
    expect(studentQueryKeys.classContent('c1')).toEqual(['student', 'class-content', 'c1']);
  });
});

describe('usePublishedQuizzes', () => {
  it('fetches published quizzes', async () => {
    server.use(
      http.get('/api/v1/quizzes', () =>
        apiResponse([
          {
            id: 'q1',
            title: 'Math Quiz',
            status: 'published',
            question_count: 5,
            total_points: 50,
            max_attempts: 1,
            time_limit_minutes: null,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => usePublishedQuizzes(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].id).toBe('q1');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/quizzes', () => apiErrorResponse()));
    const { result } = renderHook(() => usePublishedQuizzes(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useQuizDetail', () => {
  it('fetches quiz detail when quizId provided', async () => {
    server.use(
      http.get('/api/v1/quizzes/:quizId', () =>
        apiResponse({
          id: 'q1',
          school_id: null,
          created_by: 'teacher1',
          title: 'Math Quiz',
          description: null,
          subject: null,
          level_band: null,
          difficulty: null,
          time_limit_minutes: null,
          max_attempts: 1,
          shuffle_questions: false,
          status: 'published',
          total_points: 50,
          question_count: 5,
          questions: [],
        }),
      ),
    );
    const { result } = renderHook(() => useQuizDetail('q1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.id).toBe('q1');
  });

  it('is idle when quizId is null', () => {
    const { result } = renderHook(() => useQuizDetail(null), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useStartQuizAttempt', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useStartQuizAttempt(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('starts an attempt', async () => {
    server.use(
      http.post('/api/v1/quizzes/:id/start', () =>
        apiResponse({
          id: 'attempt-1',
          quiz_id: 'q1',
          student_id: 'stu1',
          attempt_no: 1,
          started_at: '2026-04-01',
          completed_at: null,
          score: null,
          max_score: 50,
          status: 'in_progress',
        }),
      ),
    );
    const { result } = renderHook(() => useStartQuizAttempt(), { wrapper: createWrapper() });
    await act(async () => {
      const data = await result.current.mutateAsync('q1');
      expect(data.id).toBe('attempt-1');
    });
  });
});

describe('useRespondToAttempt', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useRespondToAttempt(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useSubmitAttempt', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useSubmitAttempt(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useAttemptResults', () => {
  it('fetches attempt results', async () => {
    server.use(
      http.get('/api/v1/attempts/:attemptId/results', () =>
        apiResponse({
          attempt: {
            id: 'a1',
            quiz_id: 'q1',
            student_id: 'stu1',
            attempt_no: 1,
            started_at: '2026-04-01',
            completed_at: '2026-04-01',
            score: 45,
            max_score: 50,
            status: 'completed',
          },
          responses: [],
        }),
      ),
    );
    const { result } = renderHook(() => useAttemptResults('a1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.attempt.id).toBe('a1');
  });

  it('is idle when attemptId is null', () => {
    const { result } = renderHook(() => useAttemptResults(null), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useStudentClasses', () => {
  beforeEach(() => {
    server.resetHandlers();
    server.use(
      http.get('/api/v1/enrollments', () =>
        apiListResponse([{ class_id: 'c1', class_name: 'Class 6A' }]),
      ),
    );
  });

  it('fetches student classes', async () => {
    const { result } = renderHook(() => useStudentClasses(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].class_id).toBe('c1');
  });
});

describe('useStudentWork', () => {
  it('fetches student work', async () => {
    server.use(
      http.get('/api/v1/student-work', () =>
        apiResponse({
          items: [
            {
              id: 'w1',
              type: 'assignment',
              title: 'HW 1',
              status: 'submitted',
              due_at: null,
              total_points: 10,
              grading_type: null,
            },
          ],
          total: 1,
        }),
      ),
    );
    const { result } = renderHook(() => useStudentWork(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items[0].id).toBe('w1');
  });
});

describe('useClassStudentWork', () => {
  it('fetches class student work', async () => {
    server.use(
      http.get('/api/v1/student-work/class/:classId', () =>
        apiResponse({
          items: [
            {
              id: 'w1',
              type: 'assignment',
              title: 'HW 1',
              status: 'pending',
              due_at: null,
              total_points: 10,
              grading_type: null,
            },
          ],
          total: 1,
        }),
      ),
    );
    const { result } = renderHook(() => useClassStudentWork('c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('is idle when classId is null', () => {
    const { result } = renderHook(() => useClassStudentWork(null), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateEnrollment', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateEnrollment(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('creates an enrollment', async () => {
    server.use(
      http.post('/api/v1/enrollments', () =>
        apiResponse({
          id: 'enr1',
          student_id: 'stu1',
          class_id: 'c1',
          period_id: 'p1',
          school_id: 's1',
          status: 'active',
          program_id: null,
        }),
      ),
      http.get('/api/v1/enrollments', () => apiListResponse([])),
    );
    const { result } = renderHook(() => useCreateEnrollment(), { wrapper: createWrapper() });
    await act(async () => {
      const data = await result.current.mutateAsync({
        student_id: 'stu1',
        class_id: 'c1',
        period_id: 'p1',
      });
      expect(data.id).toBe('enr1');
    });
  });
});

describe('useStudentClassContent', () => {
  it('fetches class content', async () => {
    server.use(
      http.get('/api/v1/classes/:classId/content', () =>
        apiListResponse([
          {
            id: 'ci1',
            content_item_id: 'item1',
            title: 'Chapter 1',
            content_type: 'pdf',
            level_band: null,
            language: 'fr',
            subject: null,
            description: null,
            assigned_at: null,
            teacher_notes: null,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useStudentClassContent('c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('ci1');
  });

  it('is idle when classId is null', () => {
    const { result } = renderHook(() => useStudentClassContent(null), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useUpdateContentProgress', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useUpdateContentProgress(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});
