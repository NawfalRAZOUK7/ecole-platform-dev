import { api } from '@/core/api/client';
import type {
  OverviewPayload,
  AttendancePayload,
  GradesPayload,
  BillingPayload,
  EngagementPayload,
  AnalyticsDashboardFilters,
} from '../model/types';

export const analyticsApi = {
  async getDashboard(filters: AnalyticsDashboardFilters) {
    const baseParams = {
      from: filters.fromDate,
      to: filters.toDate,
      compare: filters.compare ? 'true' : 'false',
    };

    const [overview, attendance, grades, billing, engagement] = await Promise.all([
      api.get<OverviewPayload>('/analytics/overview', baseParams),
      api.get<AttendancePayload>('/analytics/attendance', {
        ...baseParams,
        period: filters.attendanceBucket,
        program_id: filters.programId || undefined,
      }),
      api.get<GradesPayload>('/analytics/grades', {
        ...baseParams,
        subject: filters.subject || undefined,
        program_id: filters.programId || undefined,
      }),
      api.get<BillingPayload>('/analytics/billing', {
        ...baseParams,
        period: filters.billingBucket,
      }),
      api.get<EngagementPayload>('/analytics/engagement', baseParams),
    ]);

    return {
      overview: overview.data,
      attendance: attendance.data,
      grades: grades.data,
      billing: billing.data,
      engagement: engagement.data,
    };
  },
};
