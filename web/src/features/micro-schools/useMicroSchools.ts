import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { microSchoolsService } from './micro-schools.service';
import type {
  CreateMicroPaymentPayload,
  CreateMicroResourcePayload,
  CreateMicroSchoolPayload,
  EnrollStudentPayload,
} from './micro-schools.types';

export const microSchoolsQueryKeys = {
  all: ['micro-schools'] as const,
  list: (filters: Record<string, string | number | undefined>) =>
    [...microSchoolsQueryKeys.all, 'list', filters] as const,
  detail: (id: string) => [...microSchoolsQueryKeys.all, 'detail', id] as const,
  enrollments: (id: string) => [...microSchoolsQueryKeys.all, 'enrollments', id] as const,
  payments: (id: string) => [...microSchoolsQueryKeys.all, 'payments', id] as const,
  resources: (id: string) => [...microSchoolsQueryKeys.all, 'resources', id] as const,
  progress: (id: string) => [...microSchoolsQueryKeys.all, 'progress', id] as const,
};

export function useMicroSchools(filters: Record<string, string | number | undefined> = {}) {
  return useQuery({
    queryKey: microSchoolsQueryKeys.list(filters),
    queryFn: async () => (await microSchoolsService.listMicroSchools(filters)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useMicroSchoolDetail(id: string) {
  return useQuery({
    queryKey: microSchoolsQueryKeys.detail(id),
    queryFn: async () => (await microSchoolsService.getMicroSchoolDetail(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useMicroSchoolEnrollments(id: string) {
  return useQuery({
    queryKey: microSchoolsQueryKeys.enrollments(id),
    queryFn: async () => (await microSchoolsService.getEnrollments(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useMicroSchoolPayments(id: string) {
  return useQuery({
    queryKey: microSchoolsQueryKeys.payments(id),
    queryFn: async () => (await microSchoolsService.getPayments(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useMicroSchoolResources(id: string) {
  return useQuery({
    queryKey: microSchoolsQueryKeys.resources(id),
    queryFn: async () => (await microSchoolsService.getResources(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useMicroSchoolProgress(id: string) {
  return useQuery({
    queryKey: microSchoolsQueryKeys.progress(id),
    queryFn: async () => (await microSchoolsService.getProgress(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateMicroSchool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateMicroSchoolPayload) =>
      microSchoolsService.createMicroSchool(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: microSchoolsQueryKeys.all });
    },
  });
}

export function useEnrollMicroStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ microSchoolId, payload }: { microSchoolId: string; payload: EnrollStudentPayload }) =>
      microSchoolsService.enrollStudent(microSchoolId, payload),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({ queryKey: microSchoolsQueryKeys.enrollments(variables.microSchoolId) });
    },
  });
}

export function useUnenrollMicroStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ microSchoolId, enrollmentId }: { microSchoolId: string; enrollmentId: string }) =>
      microSchoolsService.unenrollStudent(microSchoolId, enrollmentId),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({ queryKey: microSchoolsQueryKeys.enrollments(variables.microSchoolId) });
    },
  });
}

export function useCreateMicroPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ microSchoolId, payload }: { microSchoolId: string; payload: CreateMicroPaymentPayload }) =>
      microSchoolsService.createPayment(microSchoolId, payload),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({ queryKey: microSchoolsQueryKeys.payments(variables.microSchoolId) });
    },
  });
}

export function useCreateMicroResource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ microSchoolId, payload }: { microSchoolId: string; payload: CreateMicroResourcePayload }) =>
      microSchoolsService.addResource(microSchoolId, payload),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({ queryKey: microSchoolsQueryKeys.resources(variables.microSchoolId) });
    },
  });
}
