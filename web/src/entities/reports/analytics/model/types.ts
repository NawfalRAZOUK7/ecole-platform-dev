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
  /** G49 Phase 2.4: optional program/filière filter (UUID), forwarded to
   *  /analytics/attendance and /analytics/grades. */
  programId?: string;
}
