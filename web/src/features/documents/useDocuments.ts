import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT, STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import {
  documentsService,
  type CreateResourcePayload,
  type ResourceFilters,
  type UpdateResourcePayload,
  type UploadDocumentPayload,
} from './documents.service';

export const documentsQueryKeys = {
  all: ['documents'] as const,
  options: () => [...documentsQueryKeys.all, 'options'] as const,
  mine: () => [...documentsQueryKeys.all, 'mine'] as const,
  studentDocuments: (studentId: string | null) =>
    [...documentsQueryKeys.all, 'student-documents', studentId] as const,
  studentChecklist: (studentId: string | null) =>
    [...documentsQueryKeys.all, 'student-checklist', studentId] as const,
  document: (documentId: string | null) =>
    [...documentsQueryKeys.all, 'document', documentId] as const,
  resources: (filters: Omit<ResourceFilters, 'cursor'>) =>
    [...documentsQueryKeys.all, 'resources', filters] as const,
  resource: (resourceId: string | null) =>
    [...documentsQueryKeys.all, 'resource', resourceId] as const,
  versions: (docId: string | null) => [...documentsQueryKeys.all, 'versions', docId] as const,
  preview: (docId: string | null) => [...documentsQueryKeys.all, 'preview', docId] as const,
  resourceRating: (resourceId: string | null) =>
    [...documentsQueryKeys.all, 'resource-rating', resourceId] as const,
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

export function useDocument(documentId: string | null | undefined) {
  return useQuery({
    queryKey: documentsQueryKeys.document(documentId ?? null),
    queryFn: async () => (await documentsService.getDocument(documentId!)).data,
    enabled: Boolean(documentId),
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
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
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
      payload: UploadDocumentPayload;
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

function useCreateResourceMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      payload,
      onProgress,
      onRequestCreated,
    }: {
      payload: CreateResourcePayload;
      onProgress?: (progress: number) => void;
      onRequestCreated?: (xhr: XMLHttpRequest) => void;
    }) => documentsService.createResource(payload, onProgress, onRequestCreated),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['documents', 'resources'] });
    },
  });
}

export function useCreateResource() {
  return useCreateResourceMutation();
}

export function useUploadResource() {
  return useCreateResourceMutation();
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
      await Promise.all(
        documentIds.map((documentId) => documentsService.deleteDocument(documentId, hard)),
      );
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
    mutationFn: async (documentIds: string[]) =>
      (await documentsService.bulkDownload(documentIds)).data,
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

export function useDocumentVersions(docId: string | null | undefined) {
  return useQuery({
    queryKey: documentsQueryKeys.versions(docId ?? null),
    queryFn: async () => (await documentsService.getVersions(docId!)).data,
    enabled: Boolean(docId),
    staleTime: STALE_DEFAULT,
  });
}

export function useRestoreVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ docId, versionNum }: { docId: string; versionNum: number }) =>
      (await documentsService.restoreVersion(docId, versionNum)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: documentsQueryKeys.all });
    },
  });
}

export function useDocumentPreview(docId: string | null | undefined) {
  return useQuery({
    queryKey: documentsQueryKeys.preview(docId ?? null),
    queryFn: async () => (await documentsService.previewDocument(docId!)).data,
    enabled: Boolean(docId),
    staleTime: STALE_DEFAULT,
  });
}

export function useResourceRating(resourceId: string | null | undefined) {
  return useQuery({
    queryKey: documentsQueryKeys.resourceRating(resourceId ?? null),
    queryFn: async () => (await documentsService.getResourceRating(resourceId!)).data,
    enabled: Boolean(resourceId),
    staleTime: STALE_DEFAULT,
  });
}

export function useUploadStudentDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      studentId,
      payload,
      onProgress,
      onRequestCreated,
    }: {
      studentId: string;
      payload: UploadDocumentPayload;
      onProgress?: (progress: number) => void;
      onRequestCreated?: (xhr: XMLHttpRequest) => void;
    }) => documentsService.uploadStudentDocument(studentId, payload, onProgress, onRequestCreated),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: documentsQueryKeys.mine() }),
        queryClient.invalidateQueries({ queryKey: ['documents', 'student-documents'] }),
        queryClient.invalidateQueries({ queryKey: ['documents', 'student-checklist'] }),
      ]);
    },
  });
}

export function useUpdateResource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      resourceId,
      payload,
    }: {
      resourceId: string;
      payload: UpdateResourcePayload;
    }) => (await documentsService.updateResource(resourceId, payload)).data,
    onSuccess: async (resource) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['documents', 'resources'] }),
        queryClient.invalidateQueries({ queryKey: documentsQueryKeys.resource(resource.id) }),
      ]);
    },
  });
}

export function useDeleteResource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (resourceId: string) => {
      await documentsService.deleteResource(resourceId);
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
