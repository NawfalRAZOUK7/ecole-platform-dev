import { useQuery } from '@tanstack/react-query';
import { STALE_DEFAULT, STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import { progressService } from '@/features/academic/progress/api/progress.api';
import { teacherService } from '@/features/lms/teacher/api/teacher.api';
import { rewardsService } from '../api/rewards.api';

export const rewardsQueryKeys = {
  all: ['rewards'] as const,
  mine: () => [...rewardsQueryKeys.all, 'mine'] as const,
  student: (studentId: string | null) => [...rewardsQueryKeys.all, 'student', studentId] as const,
  history: (studentId: string | null, limit: number) =>
    [...rewardsQueryKeys.all, 'history', studentId, limit] as const,
  leaderboard: (classId: string | null, limit: number) =>
    [...rewardsQueryKeys.all, 'leaderboard', classId, limit] as const,
  badges: () => [...rewardsQueryKeys.all, 'badges'] as const,
  classes: () => [...rewardsQueryKeys.all, 'classes'] as const,
  classStudents: (classId: string | null) =>
    [...rewardsQueryKeys.all, 'class-students', classId] as const,
  children: () => [...rewardsQueryKeys.all, 'children'] as const,
};

export function useMyRewards(enabled = true) {
  return useQuery({
    queryKey: rewardsQueryKeys.mine(),
    queryFn: async () => rewardsService.getMyRewards(),
    enabled,
    staleTime: STALE_RESULTS,
  });
}

export function useStudentRewards(
  studentId: string | null | undefined,
  enabled = Boolean(studentId),
) {
  return useQuery({
    queryKey: rewardsQueryKeys.student(studentId || null),
    queryFn: async () => rewardsService.getStudentRewards(studentId!),
    enabled,
    staleTime: STALE_RESULTS,
  });
}

export function useStudentRewardHistory(
  studentId: string | null | undefined,
  limit = 10,
  enabled = Boolean(studentId),
) {
  return useQuery({
    queryKey: rewardsQueryKeys.history(studentId || null, limit),
    queryFn: async () => rewardsService.getStudentHistory(studentId!, limit),
    enabled,
    staleTime: STALE_RESULTS,
  });
}

export function useRewardLeaderboard(
  classId: string | null | undefined,
  limit = 10,
  enabled = Boolean(classId),
) {
  return useQuery({
    queryKey: rewardsQueryKeys.leaderboard(classId || null, limit),
    queryFn: async () => rewardsService.getLeaderboard(classId!, limit),
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useRewardBadges(enabled = true) {
  return useQuery({
    queryKey: rewardsQueryKeys.badges(),
    queryFn: async () => rewardsService.getBadges(),
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useRewardChildren(enabled: boolean) {
  return useQuery({
    queryKey: rewardsQueryKeys.children(),
    queryFn: async () => {
      try {
        const r = await progressService.getChildrenOverview();
        return r?.data?.data?.children ?? [];
      } catch {
        return [];
      }
    },
    enabled,
    staleTime: STALE_RESULTS,
  });
}

export function useRewardClasses(enabled: boolean) {
  return useQuery({
    queryKey: rewardsQueryKeys.classes(),
    queryFn: async () => (await teacherService.listTeacherClasses()).data,
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useRewardClassStudents(
  classId: string | null | undefined,
  enabled = Boolean(classId),
) {
  return useQuery({
    queryKey: rewardsQueryKeys.classStudents(classId || null),
    queryFn: async () => (await teacherService.listClassStudents(classId!)).data,
    enabled,
    staleTime: STALE_DEFAULT,
  });
}
