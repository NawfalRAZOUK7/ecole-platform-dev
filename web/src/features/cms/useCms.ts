import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT, STALE_DEFAULT, STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import {
  cmsService,
  type CmsContentFilters,
  type CmsLibraryFilters,
  type CmsSubmissionFilters,
} from './cms.service';
import type { CmsStoryPage, StoryPageUploadValues } from './content-upload.types';

export const cmsQueryKeys = {
  all: ['cms'] as const,
  quizzes: () => [...cmsQueryKeys.all, 'quizzes'] as const,
  quiz: (quizId: string | null) => [...cmsQueryKeys.all, 'quiz', quizId] as const,
  content: (filters: Omit<CmsContentFilters, 'cursor'>) =>
    [...cmsQueryKeys.all, 'content', filters] as const,
  libraryContent: (filters: Omit<CmsLibraryFilters, 'cursor' | 'limit'>) =>
    [...cmsQueryKeys.all, 'library-content', filters] as const,
  librarySubmissions: (filters: Omit<CmsLibraryFilters, 'cursor' | 'limit'>) =>
    [...cmsQueryKeys.all, 'library-submissions', filters] as const,
  classContent: (classId: string | null) =>
    [...cmsQueryKeys.all, 'class-content', classId] as const,
  contentItem: (contentId: string | null) =>
    [...cmsQueryKeys.all, 'content-item', contentId] as const,
  storyPages: (contentId: string | null) =>
    [...cmsQueryKeys.all, 'story-pages', contentId] as const,
  submissions: (filters: Omit<CmsSubmissionFilters, 'cursor'>) =>
    [...cmsQueryKeys.all, 'submissions', filters] as const,
  analytics: () => [...cmsQueryKeys.all, 'analytics'] as const,
  pendingBadge: () => [...cmsQueryKeys.all, 'pending-badge'] as const,
};

export function useCmsQuizzes() {
  return useQuery({
    queryKey: cmsQueryKeys.quizzes(),
    queryFn: async () => (await cmsService.listQuizzes({ limit: 50 })).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useCmsQuiz(quizId: string | null | undefined) {
  return useQuery({
    queryKey: cmsQueryKeys.quiz(quizId || null),
    queryFn: async () => (await cmsService.getQuiz(quizId!)).data,
    enabled: Boolean(quizId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateCmsQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) =>
      (await cmsService.createQuiz(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: cmsQueryKeys.quizzes() });
    },
  });
}

export function useUpdateCmsQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      quizId,
      payload,
    }: {
      quizId: string;
      payload: Record<string, unknown>;
    }) => {
      await cmsService.updateQuiz(quizId, payload);
    },
    onSuccess: async (_, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.quizzes() }),
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.quiz(variables.quizId) }),
      ]);
    },
  });
}

export function usePublishCmsQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (quizId: string) => {
      await cmsService.publishQuiz(quizId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: cmsQueryKeys.quizzes() });
    },
  });
}

export function useCmsContent(filters: Omit<CmsContentFilters, 'cursor'>) {
  return useInfiniteQuery({
    queryKey: cmsQueryKeys.content(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      cmsService.listContent({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_CONTENT,
  });
}

export function useCmsContentItem(contentId: string | null | undefined) {
  return useQuery({
    queryKey: cmsQueryKeys.contentItem(contentId || null),
    queryFn: async () => cmsService.getContent(contentId!),
    enabled: Boolean(contentId),
    staleTime: STALE_CONTENT,
  });
}

export function useCmsLibraryContent(filters: Omit<CmsLibraryFilters, 'cursor' | 'limit'>) {
  return useInfiniteQuery({
    queryKey: cmsQueryKeys.libraryContent(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      cmsService.listLibraryContent({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_CONTENT,
  });
}

export function useCmsAssignLibraryContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      content_item_id: string;
      class_id: string;
      notes: string | null;
    }) => {
      await cmsService.assignLibraryContent(payload);
    },
    onSuccess: async (_, payload) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cms', 'library-content'] }),
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.classContent(payload.class_id) }),
      ]);
    },
  });
}

export function useCmsUnassignLibraryContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (assignmentId: string) => {
      await cmsService.removeLibraryAssignment(assignmentId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['cms', 'class-content'] });
    },
  });
}

export function useCmsSubmitLibraryContentForReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contentItemId: string) => {
      await cmsService.submitLibraryContentForReview(contentItemId);
      return contentItemId;
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cms', 'library-content'] }),
        queryClient.invalidateQueries({ queryKey: ['cms', 'library-submissions'] }),
      ]);
    },
  });
}

export function useCmsLibrarySubmissions(filters: Omit<CmsLibraryFilters, 'cursor' | 'limit'>) {
  return useInfiniteQuery({
    queryKey: cmsQueryKeys.librarySubmissions(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      cmsService.listLibrarySubmissions({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useCmsClassContent(classId: string | null | undefined) {
  return useQuery({
    queryKey: cmsQueryKeys.classContent(classId || null),
    queryFn: async () => (await cmsService.listClassContent(classId!)).data,
    enabled: Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateCmsContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) =>
      (await cmsService.createContent(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['cms', 'content'] });
    },
  });
}

export function useUpdateCmsContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      contentId,
      payload,
    }: {
      contentId: string;
      payload: Record<string, unknown>;
    }) => {
      await cmsService.updateContent(contentId, payload);
    },
    onSuccess: async (_, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cms', 'content'] }),
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.contentItem(variables.contentId) }),
      ]);
    },
  });
}

export function useDeleteCmsContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (contentId: string) => {
      await cmsService.deleteContent(contentId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['cms', 'content'] });
    },
  });
}

export function useUploadCmsContentAsset() {
  return useMutation({
    mutationFn: async ({
      contentId,
      file,
      onProgress,
    }: {
      contentId: string;
      file: File;
      onProgress?: (progress: number) => void;
    }) => cmsService.uploadContentAsset(contentId, file, onProgress),
  });
}

export function useCmsStoryPages(contentId: string | null | undefined) {
  return useQuery({
    queryKey: cmsQueryKeys.storyPages(contentId || null),
    queryFn: async () => (await cmsService.listStoryPages(contentId!)).data,
    enabled: Boolean(contentId),
    staleTime: STALE_CONTENT,
  });
}

export function useUploadCmsStoryPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      contentId,
      file,
      payload,
    }: {
      contentId: string;
      file: File;
      payload: StoryPageUploadValues;
    }) => (await cmsService.uploadStoryPage(contentId, file, payload)).data,
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.storyPages(variables.contentId) }),
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.contentItem(variables.contentId) }),
      ]);
    },
  });
}

export function useDeleteCmsStoryPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ contentId, assetId }: { contentId: string; assetId: string }) =>
      cmsService.deleteContentAsset(contentId, assetId),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.storyPages(variables.contentId) }),
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.contentItem(variables.contentId) }),
      ]);
    },
  });
}

export function useReorderCmsStoryPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      contentId,
      page,
      pageNumber,
    }: {
      contentId: string;
      page: CmsStoryPage;
      pageNumber: number;
    }) => cmsService.reorderStoryPage(contentId, page, pageNumber),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.storyPages(variables.contentId) }),
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.contentItem(variables.contentId) }),
      ]);
    },
  });
}

export function useCmsSubmissions(filters: Omit<CmsSubmissionFilters, 'cursor'>) {
  return useInfiniteQuery({
    queryKey: cmsQueryKeys.submissions(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      cmsService.listSubmissions({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_RESULTS,
  });
}

export function useReviewCmsSubmission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      submissionId,
      payload,
    }: {
      submissionId: string;
      payload: Record<string, unknown>;
    }) => {
      await cmsService.reviewSubmission(submissionId, payload);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cms', 'submissions'] }),
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.pendingBadge() }),
        queryClient.invalidateQueries({ queryKey: cmsQueryKeys.analytics() }),
      ]);
    },
  });
}

export function useCmsAnalytics() {
  return useQuery({
    queryKey: cmsQueryKeys.analytics(),
    queryFn: async () => cmsService.getAnalyticsSnapshot(),
    staleTime: STALE_RESULTS,
  });
}

export function useCmsPendingSubmissionBadge() {
  return useQuery({
    queryKey: cmsQueryKeys.pendingBadge(),
    queryFn: async () => cmsService.getPendingSubmissionBadge(),
    staleTime: STALE_DEFAULT,
    refetchInterval: 60_000,
  });
}
