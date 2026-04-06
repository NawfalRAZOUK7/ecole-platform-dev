import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT } from '@/shared/hooks/useQueryDefaults';
import { skillsService } from './skills.service';
import type {
  CreateSkillDimensionPayload,
  CreateSkillMilestonePayload,
} from './skills.types';

export const skillsQueryKeys = {
  all: ['skills'] as const,
  dimensions: () => [...skillsQueryKeys.all, 'dimensions'] as const,
  milestones: (dimensionId?: string) => [...skillsQueryKeys.all, 'milestones', dimensionId || 'all'] as const,
  progress: (studentId: string, academicYearId: string) =>
    [...skillsQueryKeys.all, 'progress', studentId, academicYearId] as const,
  passport: (studentId: string, academicYearId: string) =>
    [...skillsQueryKeys.all, 'passport', studentId, academicYearId] as const,
  classAnalytics: (classId: string, academicYearId: string) =>
    [...skillsQueryKeys.all, 'class-analytics', classId, academicYearId] as const,
  schoolAnalytics: (academicYearId: string) =>
    [...skillsQueryKeys.all, 'school-analytics', academicYearId] as const,
  leaderboard: (classId: string, academicYearId: string, limit: number) =>
    [...skillsQueryKeys.all, 'leaderboard', classId, academicYearId, limit] as const,
};

export function useSkillDimensions() {
  return useQuery({
    queryKey: skillsQueryKeys.dimensions(),
    queryFn: async () => (await skillsService.listDimensions(true)).data,
    staleTime: STALE_CONTENT,
  });
}

export function useSkillMilestones(dimensionId?: string) {
  return useQuery({
    queryKey: skillsQueryKeys.milestones(dimensionId),
    queryFn: async () => (await skillsService.listMilestones(dimensionId, true)).data,
    staleTime: STALE_CONTENT,
  });
}

export function useStudentSkillProgress(studentId: string, academicYearId: string) {
  return useQuery({
    queryKey: skillsQueryKeys.progress(studentId, academicYearId),
    queryFn: async () => (await skillsService.getStudentProgress(studentId, academicYearId)).data,
    enabled: Boolean(studentId && academicYearId),
    staleTime: STALE_CONTENT,
  });
}

export function useSkillPassport(studentId: string, academicYearId: string) {
  return useQuery({
    queryKey: skillsQueryKeys.passport(studentId, academicYearId),
    queryFn: async () => (await skillsService.getPassport(studentId, academicYearId)).data,
    enabled: Boolean(studentId && academicYearId),
    staleTime: STALE_CONTENT,
    retry: false,
  });
}

export function useClassSkillAnalytics(classId: string, academicYearId: string) {
  return useQuery({
    queryKey: skillsQueryKeys.classAnalytics(classId, academicYearId),
    queryFn: async () => (await skillsService.getClassAnalytics(classId, academicYearId)).data,
    enabled: Boolean(classId && academicYearId),
    staleTime: STALE_CONTENT,
  });
}

export function useSchoolSkillAnalytics(academicYearId: string) {
  return useQuery({
    queryKey: skillsQueryKeys.schoolAnalytics(academicYearId),
    queryFn: async () => (await skillsService.getSchoolAnalytics(academicYearId)).data,
    enabled: Boolean(academicYearId),
    staleTime: STALE_CONTENT,
  });
}

export function useSkillLeaderboard(classId: string, academicYearId: string, limit: number) {
  return useQuery({
    queryKey: skillsQueryKeys.leaderboard(classId, academicYearId, limit),
    queryFn: async () => (await skillsService.getLeaderboard(classId, academicYearId, limit)).data,
    enabled: Boolean(classId && academicYearId),
    staleTime: STALE_CONTENT,
  });
}

export function useCreateSkillDimension() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateSkillDimensionPayload) => skillsService.createDimension(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: skillsQueryKeys.all });
    },
  });
}

export function useCreateSkillMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateSkillMilestonePayload) => skillsService.createMilestone(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: skillsQueryKeys.all });
    },
  });
}

export function useEvaluateStudentSkills() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      studentId,
      academicYearId,
    }: {
      studentId: string;
      academicYearId: string;
    }) => skillsService.evaluateStudent(studentId, academicYearId),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: skillsQueryKeys.progress(variables.studentId, variables.academicYearId) }),
        queryClient.invalidateQueries({ queryKey: skillsQueryKeys.passport(variables.studentId, variables.academicYearId) }),
        queryClient.invalidateQueries({ queryKey: skillsQueryKeys.all }),
      ]);
    },
  });
}

export function useGenerateSkillPassport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      studentId,
      academicYearId,
    }: {
      studentId: string;
      academicYearId: string;
    }) => skillsService.generatePassport(studentId, academicYearId),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: skillsQueryKeys.passport(variables.studentId, variables.academicYearId) }),
        queryClient.invalidateQueries({ queryKey: skillsQueryKeys.all }),
      ]);
    },
  });
}
