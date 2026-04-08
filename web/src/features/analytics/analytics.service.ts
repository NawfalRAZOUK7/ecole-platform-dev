import { getAccessToken, api } from '@/services/api/client';

export type RangePreset = 'this_week' | 'this_month' | 'this_period' | 'custom';
export type Bucket = 'daily' | 'weekly' | 'monthly';
export type ExportEntity = 'students' | 'grades' | 'attendance' | 'invoices' | 'payments';

export interface ComparisonMetric {
  current: number;
  previous: number | null;
  change_percent: number | null;
  trend: 'up' | 'down' | 'flat';
}

export interface OverviewMetric {
  key: string;
  label: string;
  value: ComparisonMetric;
}

export interface OverviewPayload {
  metrics: OverviewMetric[];
}

export interface SeriesPoint {
  label: string;
  value: number;
  extra?: Record<string, number>;
}

export interface AttendancePayload {
  summary: {
    rate: ComparisonMetric;
    total_records: number;
  };
  series: SeriesPoint[];
}

export interface GradesPayload {
  summary: {
    average: ComparisonMetric;
    count: number;
  };
  distribution: Array<{ label: string; count: number }>;
}

export interface BillingPayload {
  summary: {
    invoiced: number;
    paid: number;
    outstanding: number;
    collection_rate: ComparisonMetric;
  };
  series: SeriesPoint[];
}

export interface EngagementPayload {
  summary: {
    registered_users: number;
    dau: number;
    mau: number;
    active_users: ComparisonMetric;
    engaged_users: number;
  };
  funnel: Array<{ label: string; value: number }>;
  feature_adoption: Array<{ feature: string; users: number; adoption_rate: number }>;
}

export interface AnalyticsDashboardFilters {
  fromDate: string;
  toDate: string;
  compare: boolean;
  attendanceBucket: Bucket;
  billingBucket: Bucket;
  subject: string;
}

export const analyticsService = {
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
      }),
      api.get<GradesPayload>('/analytics/grades', {
        ...baseParams,
        subject: filters.subject || undefined,
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

  async downloadExport(
    format: 'csv' | 'xlsx',
    entity: ExportEntity,
    filters: Record<string, string>,
  ) {
    const url = new URL(
      format === 'xlsx' ? '/api/v1/export/xlsx' : '/api/v1/export/csv',
      window.location.origin,
    );
    url.searchParams.set('entity', entity);
    url.searchParams.set('filters', JSON.stringify(filters));

    const headers: Record<string, string> = {
      Accept: '*/*',
      'Accept-Language': navigator.language || 'fr',
      'X-Correlation-Id': crypto.randomUUID(),
      'X-Client-Version': '0.1.0',
      'X-Client-Platform': 'web',
    };

    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.error?.message || 'Export failed');
    }

    return response.blob();
  },
};
