import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT } from '@/shared/hooks/useQueryDefaults';
import { complianceService } from './compliance.service';
import type {
  CreateCurriculumMappingPayload,
  CreateMenCurriculumPayload,
  CreateMenObjectivePayload,
  GenerateComplianceReportPayload,
} from './compliance.types';

export const complianceQueryKeys = {
  all: ['compliance'] as const,
  curricula: (filters: Record<string, string | boolean | undefined>) => [...complianceQueryKeys.all, 'curricula', filters] as const,
  objectives: (curriculumId: string, trimester?: number) => [...complianceQueryKeys.all, 'objectives', curriculumId, trimester || 'all'] as const,
  mappings: (filters: Record<string, string | undefined>) => [...complianceQueryKeys.all, 'mappings', filters] as const,
  dashboard: (filters: Record<string, string | undefined>) => [...complianceQueryKeys.all, 'dashboard', filters] as const,
  reports: (filters: Record<string, string | undefined>) => [...complianceQueryKeys.all, 'reports', filters] as const,
  report: (reportId: string) => [...complianceQueryKeys.all, 'report', reportId] as const,
};

export function useCurricula(filters: {
  level?: string;
  grade?: string;
  subject?: string;
  academic_year?: string;
} = {}) {
  return useQuery({
    queryKey: complianceQueryKeys.curricula(filters),
    queryFn: async () => (await complianceService.listCurricula({ ...filters, is_active: true })).data,
    staleTime: STALE_CONTENT,
  });
}

export function useCurriculumObjectives(curriculumId: string, trimester?: number) {
  return useQuery({
    queryKey: complianceQueryKeys.objectives(curriculumId, trimester),
    queryFn: async () => (await complianceService.listObjectives(curriculumId, trimester)).data,
    enabled: Boolean(curriculumId),
    staleTime: STALE_CONTENT,
  });
}

export function useCurriculumMappings(filters: {
  curriculum_id?: string;
  objective_id?: string;
  course_id?: string;
  content_item_id?: string;
} = {}) {
  return useQuery({
    queryKey: complianceQueryKeys.mappings(filters),
    queryFn: async () => (await complianceService.listMappings(filters)).data,
    staleTime: STALE_CONTENT,
  });
}

export function useComplianceDashboard(filters: {
  academic_year_id: string;
  level?: string;
  grade?: string;
  subject?: string;
}) {
  return useQuery({
    queryKey: complianceQueryKeys.dashboard(filters),
    queryFn: async () => (await complianceService.getDashboard(filters)).data,
    enabled: Boolean(filters.academic_year_id),
    staleTime: STALE_CONTENT,
  });
}

export function useComplianceReports(filters: {
  curriculum_id?: string;
  academic_year_id?: string;
} = {}) {
  return useQuery({
    queryKey: complianceQueryKeys.reports(filters),
    queryFn: async () => (await complianceService.listReports(filters)).data,
    staleTime: STALE_CONTENT,
  });
}

export function useComplianceReport(reportId: string) {
  return useQuery({
    queryKey: complianceQueryKeys.report(reportId),
    queryFn: async () => (await complianceService.getReport(reportId)).data,
    enabled: Boolean(reportId),
    staleTime: STALE_CONTENT,
  });
}

export function useCreateCurriculum() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateMenCurriculumPayload) => complianceService.createCurriculum(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: complianceQueryKeys.all });
    },
  });
}

export function useCreateObjective() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      curriculumId,
      payload,
    }: {
      curriculumId: string;
      payload: CreateMenObjectivePayload;
    }) => complianceService.createObjective(curriculumId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: complianceQueryKeys.all });
    },
  });
}

export function useCreateMapping() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateCurriculumMappingPayload) => complianceService.createMapping(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: complianceQueryKeys.all });
    },
  });
}

export function useDeleteMapping() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (mappingId: string) => complianceService.deleteMapping(mappingId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: complianceQueryKeys.all });
    },
  });
}

export function useGenerateComplianceReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: GenerateComplianceReportPayload) => complianceService.generateReport(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: complianceQueryKeys.all });
    },
  });
}
