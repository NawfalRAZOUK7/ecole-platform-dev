import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT, STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { documentsService, type ResourceFilters } from './documents.service';

export const documentsQueryKeys = {
  all: ['documents'] as const,
  options: () => [...documentsQueryKeys.all, 'options'] as const,
  mine: () => [...documentsQueryKeys.all, 'mine'] as const,
  studentDocuments: (studentId: string | null) => [...documentsQueryKeys.all, 'student-documents', studentId] as const,
  studentChecklist: (studentId: string | null) => [...documentsQueryKeys.all, 'student-checklist', studentId] as const,
  resources: (filters: Omit<ResourceFilters, 'cursor'>) => [...documentsQueryKeys.all, 'resources', filters] as const,
  resource: (resourceId: string | null) => [...documentsQueryKeys.all, 'resource', resourceId] as const,
};

export function useDocumentsOptions() {
  return useQuery({
    queryKey: documentsQueryKeys.options(),
    queryFn: async () => (await documentsService.getOptions()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useMyDocuments() {
  return useQuery({
    queryKey: documentsQueryKeys.mine(),
    queryFn: async () => (await documentsService.listMyDocuments()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useStudentDocuments(studentId: string | null | undefined, enabled = true) {
  return useQuery({
    queryKey: documentsQueryKeys.studentDocuments(studentId || null),
    queryFn: async () => (await documentsService.listStudentDocuments(studentId!)).data,
    enabled: enabled && Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

export function useStudentChecklist(studentId: string | null | undefined, enabled = true) {
  return useQuery({
    queryKey: documentsQueryKeys.studentChecklist(studentId || null),
    queryFn: async () => (await documentsService.getStudentChecklist(studentId!)).data,
    enabled: enabled && Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

export function useResources(filters: Omit<ResourceFilters, 'cursor'>) {
  return useInfiniteQuery({
    queryKey: documentsQueryKeys.resources(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      documentsService.listResources({
        limit: 24,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_CONTENT,
  });
}

export function useResourceDetail(resourceId: string | null | undefined) {
  return useQuery({
    queryKey: documentsQueryKeys.resource(resourceId || null),
    queryFn: async () => (await documentsService.getResource(resourceId!)).data,
    enabled: Boolean(resourceId),
    staleTime: STALE_CONTENT,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      payload,
      onProgress,
      onRequestCreated,
    }: {
      payload: {
        file: File;
        category: string;
        linkedStudentId?: string;
        expiresAt?: string;
        language: string;
      };
      onProgress?: (progress: number) => void;
      onRequestCreated?: (xhr: XMLHttpRequest) => void;
    }) => documentsService.uploadDocument(payload, onProgress, onRequestCreated),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: documentsQueryKeys.mine() }),
        queryClient.invalidateQueries({ queryKey: ['documents', 'student-documents'] }),
        queryClient.invalidateQueries({ queryKey: ['documents', 'student-checklist'] }),
      ]);
    },
  });
}

export function useUploadResource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      payload,
      onProgress,
      onRequestCreated,
    }: {
      payload: {
        file: File;
        title: string;
        description: string;
        subject: string;
        level: string;
        type: string;
        tags: string;
        visibility?: string;
        language: string;
      };
      onProgress?: (progress: number) => void;
      onRequestCreated?: (xhr: XMLHttpRequest) => void;
    }) => documentsService.uploadResource(payload, onProgress, onRequestCreated),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['documents', 'resources'] });
    },
  });
}

export function useBulkDeleteDocuments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      documentIds,
      hard,
      useBulkEndpoint,
    }: {
      documentIds: string[];
      hard?: boolean;
      useBulkEndpoint?: boolean;
    }) => {
      if (useBulkEndpoint && !hard) {
        await documentsService.bulkDelete(documentIds);
        return;
      }
      await Promise.all(documentIds.map((documentId) => documentsService.deleteDocument(documentId, hard)));
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: documentsQueryKeys.mine() }),
        queryClient.invalidateQueries({ queryKey: ['documents', 'student-documents'] }),
        queryClient.invalidateQueries({ queryKey: ['documents', 'student-checklist'] }),
      ]);
    },
  });
}

export function useBulkDownloadDocuments() {
  return useMutation({
    mutationFn: async (documentIds: string[]) => (await documentsService.bulkDownload(documentIds)).data,
  });
}

export function useRateResource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ resourceId, rating }: { resourceId: string; rating: number }) => {
      await documentsService.rateResource(resourceId, rating);
      return resourceId;
    },
    onSuccess: async (resourceId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['documents', 'resources'] }),
        queryClient.invalidateQueries({ queryKey: documentsQueryKeys.resource(resourceId) }),
      ]);
    },
  });
}
