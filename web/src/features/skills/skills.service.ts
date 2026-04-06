import { api } from '@/services/api/client';
import type {
  CreateSkillDimensionPayload,
  CreateSkillMilestonePayload,
  SkillClassAnalytics,
  SkillDimension,
  SkillEvaluation,
  SkillLeaderboardEntry,
  SkillMilestone,
  SkillPassport,
  SkillProgressItem,
  SkillSchoolAnalytics,
} from './skills.types';

export const skillsService = {
  listDimensions(isActive?: boolean) {
    return api.list<SkillDimension>('/skills/dimensions', {
      is_active: isActive === undefined ? undefined : String(isActive),
    });
  },

  createDimension(payload: CreateSkillDimensionPayload) {
    return api.post<SkillDimension>('/skills/dimensions', payload);
  },

  listMilestones(dimensionId?: string, isActive?: boolean) {
    return api.list<SkillMilestone>('/skills/milestones', {
      dimension_id: dimensionId,
      is_active: isActive === undefined ? undefined : String(isActive),
    });
  },

  createMilestone(payload: CreateSkillMilestonePayload) {
    return api.post<SkillMilestone>('/skills/milestones', payload);
  },

  getStudentProgress(studentId: string, academicYearId: string) {
    return api.list<SkillProgressItem>(`/skills/progress/student/${studentId}`, {
      academic_year_id: academicYearId,
    });
  },

  evaluateStudent(studentId: string, academicYearId: string) {
    return api.post<SkillEvaluation>(`/skills/evaluate/${studentId}?academic_year_id=${encodeURIComponent(academicYearId)}`);
  },

  getPassport(studentId: string, academicYearId: string) {
    return api.get<SkillPassport>(`/skills/passport/${studentId}`, {
      academic_year_id: academicYearId,
    });
  },

  generatePassport(studentId: string, academicYearId: string) {
    return api.post<SkillPassport>(`/skills/passport/${studentId}/generate?academic_year_id=${encodeURIComponent(academicYearId)}`);
  },

  downloadPassportUrl(studentId: string, academicYearId: string) {
    return `/api/v1/skills/passport/${studentId}/download?academic_year_id=${encodeURIComponent(academicYearId)}`;
  },

  getClassAnalytics(classId: string, academicYearId: string) {
    return api.get<SkillClassAnalytics>(`/skills/analytics/class/${classId}`, {
      academic_year_id: academicYearId,
    });
  },

  getSchoolAnalytics(academicYearId: string) {
    return api.get<SkillSchoolAnalytics>('/skills/analytics/school', {
      academic_year_id: academicYearId,
    });
  },

  getLeaderboard(classId: string, academicYearId: string, limit = 10) {
    return api.list<SkillLeaderboardEntry>(`/skills/leaderboard/${classId}`, {
      academic_year_id: academicYearId,
      limit,
    });
  },
};
