import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT, STALE_DEFAULT, STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import { studentService, type EnrollmentPayload } from '@/features/lms/student/api/student.api';

export const studentQueryKeys = {
  all: ['student'] as const,
  quizzes: () => [...studentQueryKeys.all, 'quizzes'] as const,
  studentWork: () => [...studentQueryKeys.all, 'student-work'] as const,
  classStudentWork: (classId: string | null | undefined) =>
    [...studentQueryKeys.all, 'class-student-work', classId] as const,
  quizDetail: (quizId: string | null | undefined) =>
    [...studentQueryKeys.all, 'quiz-detail', quizId] as const,
  attemptResults: (attemptId: string | null | undefined) =>
    [...studentQueryKeys.all, 'attempt-results', attemptId] as const,
  classes: () => [...studentQueryKeys.all, 'classes'] as const,
  classContent: (classId: string | null | undefined) =>
    [...studentQueryKeys.all, 'class-content', classId] as const,
};

export function usePublishedQuizzes() {
  return useQuery({
    queryKey: studentQueryKeys.quizzes(),
    queryFn: async () => (await studentService.listPublishedQuizzes()).data,
    staleTime: STALE_RESULTS,
  });
}

export function useQuizDetail(quizId: string | null | undefined) {
  return useQuery({
    queryKey: studentQueryKeys.quizDetail(quizId),
    queryFn: async () => (await studentService.getQuizDetail(quizId!)).data,
    enabled: Boolean(quizId),
    staleTime: STALE_DEFAULT,
  });
}

export function useStartQuizAttempt() {
  return useMutation({
    mutationFn: async (quizId: string) => (await studentService.startQuizAttempt(quizId)).data,
  });
}

export function useRespondToAttempt() {
  return useMutation({
    mutationFn: async ({
      attemptId,
      questionId,
      studentAnswer,
    }: {
      attemptId: string;
      questionId: string;
      studentAnswer: unknown;
    }) => {
      await studentService.respondToAttempt(attemptId, {
        question_id: questionId,
        student_answer: studentAnswer,
      });
    },
  });
}

export function useSubmitAttempt() {
  return useMutation({
    mutationFn: async (attemptId: string) => {
      await studentService.submitAttempt(attemptId);
    },
  });
}

export function useAttemptResults(attemptId: string | null | undefined) {
  return useQuery({
    queryKey: studentQueryKeys.attemptResults(attemptId),
    queryFn: async () => (await studentService.getAttemptResults(attemptId!)).data,
    enabled: Boolean(attemptId),
    staleTime: STALE_RESULTS,
  });
}

export function useStudentClasses() {
  return useQuery({
    queryKey: studentQueryKeys.classes(),
    queryFn: async () => (await studentService.listStudentClasses()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useStudentWork() {
  return useQuery({
    queryKey: studentQueryKeys.studentWork(),
    queryFn: async () => (await studentService.listStudentWork()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useClassStudentWork(classId: string | null | undefined) {
  return useQuery({
    queryKey: studentQueryKeys.classStudentWork(classId),
    queryFn: async () => (await studentService.listClassStudentWork(classId!)).data,
    enabled: Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateEnrollment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: EnrollmentPayload) =>
      (await studentService.createEnrollment(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: studentQueryKeys.classes() });
    },
  });
}

export function useStudentClassContent(classId: string | null | undefined) {
  return useQuery({
    queryKey: studentQueryKeys.classContent(classId),
    queryFn: async () => (await studentService.listClassContent(classId!)).data,
    enabled: Boolean(classId),
    staleTime: STALE_CONTENT,
  });
}

export function useUpdateContentProgress() {
  return useMutation({
    mutationFn: async ({ contentItemId, status }: { contentItemId: string; status: string }) => {
      await studentService.updateContentProgress(contentItemId, status);
    },
  });
}
