import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT, STALE_DEFAULT, STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import {
  teacherService,
  type AttendanceSessionPayload,
  type ContentUploadPayload,
  type TeacherAssessmentsFilters,
  type TeacherAssignmentsFilters,
  type TeacherContentFilters,
  type TeacherCoursesFilters,
  type TeacherSubmissionFilters,
} from './teacher.service';

export const teacherQueryKeys = {
  all: ['teacher'] as const,
  classes: () => [...teacherQueryKeys.all, 'classes'] as const,
  periods: () => [...teacherQueryKeys.all, 'periods'] as const,
  classStudents: (classId: string | null | undefined) => [...teacherQueryKeys.all, 'class-students', classId] as const,
  courses: (filters: TeacherCoursesFilters) => [...teacherQueryKeys.all, 'courses', filters] as const,
  assignments: (filters: TeacherAssignmentsFilters) => [...teacherQueryKeys.all, 'assignments', filters] as const,
  assessments: (filters: TeacherAssessmentsFilters) => [...teacherQueryKeys.all, 'assessments', filters] as const,
  classProgress: (classId: string) => [...teacherQueryKeys.all, 'class-progress', classId] as const,
  contentLibrary: (filters: TeacherContentFilters) => [...teacherQueryKeys.all, 'content-library', filters] as const,
  assignableClasses: () => [...teacherQueryKeys.all, 'assignable-classes'] as const,
  contentSubmissions: (filters: TeacherContentFilters) => [...teacherQueryKeys.all, 'content-submissions', filters] as const,
  quizzes: () => [...teacherQueryKeys.all, 'quizzes'] as const,
  submissions: (filters: TeacherSubmissionFilters) => [...teacherQueryKeys.all, 'submissions', filters] as const,
};

export function useTeacherClasses() {
  return useQuery({
    queryKey: teacherQueryKeys.classes(),
    queryFn: async () => (await teacherService.listTeacherClasses()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useTeacherPeriods() {
  return useQuery({
    queryKey: teacherQueryKeys.periods(),
    queryFn: async () => (await teacherService.listTeacherPeriods()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useTeacherClassStudents(classId: string | null | undefined) {
  return useQuery({
    queryKey: teacherQueryKeys.classStudents(classId),
    queryFn: async () => (await teacherService.listClassStudents(classId!)).data,
    enabled: Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useTeacherCourses(filters: TeacherCoursesFilters) {
  return useInfiniteQuery({
    queryKey: teacherQueryKeys.courses(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      teacherService.listCourses({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateCourse() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      await teacherService.createCourse(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['teacher', 'courses'] });
    },
  });
}

export function useTeacherAssignments(filters: TeacherAssignmentsFilters) {
  return useInfiniteQuery({
    queryKey: teacherQueryKeys.assignments(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      teacherService.listAssignments({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateAssignment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      await teacherService.createAssignment(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['teacher', 'assignments'] });
    },
  });
}

export function useTeacherAssessments(filters: TeacherAssessmentsFilters) {
  return useInfiniteQuery({
    queryKey: teacherQueryKeys.assessments(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      teacherService.listAssessments({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      await teacherService.createAssessment(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['teacher', 'assessments'] });
    },
  });
}

export function usePublishAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (assessmentId: string) => {
      await teacherService.publishAssessment(assessmentId);
      return assessmentId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['teacher', 'assessments'] });
    },
  });
}

export function useCreateAttendanceSession() {
  return useMutation({
    mutationFn: async (payload: AttendanceSessionPayload) => {
      await teacherService.createAttendanceSession(payload);
    },
  });
}

export function useTeacherClassProgress(classId: string | null | undefined) {
  return useQuery({
    queryKey: classId ? teacherQueryKeys.classProgress(classId) : [...teacherQueryKeys.all, 'class-progress', 'pending'],
    queryFn: async () => (await teacherService.getClassProgress(classId!)).data.data,
    enabled: Boolean(classId),
    staleTime: STALE_RESULTS,
  });
}

export function useTeacherContentLibrary(filters: TeacherContentFilters) {
  return useInfiniteQuery({
    queryKey: teacherQueryKeys.contentLibrary(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      teacherService.listContentLibrary({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_CONTENT,
  });
}

export function useAssignableClasses() {
  return useQuery({
    queryKey: teacherQueryKeys.assignableClasses(),
    queryFn: async () => (await teacherService.listAssignableClasses()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useAssignContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { content_item_id: string; class_id: string; notes: string | null }) => {
      await teacherService.assignContent(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['teacher', 'content-library'] });
    },
  });
}

export function useSubmitContentForReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contentId: string) => {
      await teacherService.submitContentForReview(contentId);
      return contentId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['teacher', 'content-library'] });
    },
  });
}

export function useTeacherContentSubmissions(filters: TeacherContentFilters) {
  return useInfiniteQuery({
    queryKey: teacherQueryKeys.contentSubmissions(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      teacherService.listMyContentSubmissions({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useUploadContentItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      payload,
      onProgress,
    }: {
      payload: ContentUploadPayload;
      onProgress?: (progress: number) => void;
    }) => teacherService.uploadContentItem(payload, onProgress),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['teacher', 'content-library'] }),
        queryClient.invalidateQueries({ queryKey: ['teacher', 'content-submissions'] }),
      ]);
    },
  });
}

export function useTeacherQuizzes() {
  return useInfiniteQuery({
    queryKey: teacherQueryKeys.quizzes(),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      teacherService.listQuizzes({
        limit: 20,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateQuiz() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      await teacherService.createQuiz(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: teacherQueryKeys.quizzes() });
    },
  });
}

export function usePublishQuiz() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (quizId: string) => {
      await teacherService.publishQuiz(quizId);
      return quizId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: teacherQueryKeys.quizzes() });
    },
  });
}

export function useTeacherSubmissions(filters: TeacherSubmissionFilters) {
  return useInfiniteQuery({
    queryKey: teacherQueryKeys.submissions(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      teacherService.listTeacherSubmissions({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_RESULTS,
  });
}

export function useGradeSubmission() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      submissionId,
      payload,
    }: {
      submissionId: string;
      payload: Record<string, unknown>;
    }) => {
      await teacherService.gradeSubmission(submissionId, payload);
      return submissionId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['teacher', 'submissions'] });
    },
  });
}
