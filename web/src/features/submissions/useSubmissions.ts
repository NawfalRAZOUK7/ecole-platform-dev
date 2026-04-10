import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { submissionsService } from './submissions.service';

export const submissionsQueryKeys = {
  all: ['student-submissions'] as const,
  assignments: () => [...submissionsQueryKeys.all, 'assignments'] as const,
};

export function useSubmissionAssignments() {
  return useQuery({
    queryKey: submissionsQueryKeys.assignments(),
    queryFn: async () => (await submissionsService.listAssignments()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateStudentSubmission() {
  return useMutation({
    mutationFn: async (assignmentId: string) =>
      (await submissionsService.createSubmission(assignmentId)).data,
  });
}

export function useUploadSubmissionFile() {
  return useMutation({
    mutationFn: async ({
      submissionId,
      file,
      fileTypeHint,
      onProgress,
    }: {
      submissionId: string;
      file: File;
      fileTypeHint?: string;
      onProgress?: (completed: number) => void;
    }) => submissionsService.uploadSubmissionFile(submissionId, file, fileTypeHint, onProgress),
  });
}

export function useFinalizeStudentSubmission() {
  return useMutation({
    mutationFn: async (submissionId: string) => {
      await submissionsService.finalizeSubmission(submissionId);
    },
  });
}

export function useGenerateExercisePdf() {
  return useMutation({
    mutationFn: async (assignmentId: string) =>
      submissionsService.generateExercisePdf(assignmentId),
  });
}

export function useDownloadExercisePdf() {
  return useMutation({
    mutationFn: async (assignmentId: string) =>
      submissionsService.generateExercisePdf(assignmentId),
  });
}

export function useOverridePenalty() {
  return useMutation({
    mutationFn: async ({
      submissionId,
      payload,
    }: {
      submissionId: string;
      payload: { penalty_override: number; reason?: string };
    }) => submissionsService.overridePenalty(submissionId, payload),
  });
}

export function useUploadSubmissionFiles() {
  return useMutation({
    mutationFn: async ({ submissionId, files }: { submissionId: string; files: File[] }) =>
      submissionsService.uploadFiles(submissionId, files),
  });
}

export function useSubmissionFile(submissionId: string, fileId: string) {
  return useQuery({
    queryKey: [...submissionsQueryKeys.all, 'file', submissionId, fileId] as const,
    queryFn: async () => (await submissionsService.getFile(submissionId, fileId)).data,
    enabled: Boolean(submissionId && fileId),
    staleTime: STALE_DEFAULT,
  });
}

export function usePreviewSubmission(submissionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => (await submissionsService.previewSubmission(submissionId)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: submissionsQueryKeys.all });
    },
  });
}
