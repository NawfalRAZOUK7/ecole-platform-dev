import i18next from 'i18next';
import { api, getAccessToken } from '@/core/api/client';
import type {
  CashflowForecast,
  ComputeCashflowPayload,
  ComputeCostPerStudentPayload,
  ComputeFinancialSnapshotPayload,
  ComputeRetentionPayload,
  CostPerStudentAnalysis,
  FinancialExportResult,
  FinancialHealthDashboard,
  FinancialHealthTrends,
  FinancialSnapshot,
  RetentionMetric,
} from '@/entities/reports/financial-health/model/types';

const CLIENT_VERSION = '0.1.0';

async function downloadExport(format: 'csv' | 'pdf'): Promise<FinancialExportResult> {
  const headers: Record<string, string> = {
    Accept: format === 'pdf' ? 'application/pdf' : 'text/csv',
    'Accept-Language': i18next.language || 'fr',
    'X-Correlation-Id': crypto.randomUUID(),
    'X-Client-Version': CLIENT_VERSION,
    'X-Client-Platform': 'web',
  };

  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    format === 'pdf'
      ? '/api/v1/financial-health/export/pdf'
      : '/api/v1/financial-health/export/csv',
    {
      method: 'GET',
      headers,
      credentials: 'include',
    },
  );

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? `Unable to export financial report (${format})`);
  }

  return {
    blob: await response.blob(),
    filename: `financial-health.${format === 'pdf' ? 'pdf' : 'csv'}`,
  };
}

export const financialHealthService = {
  listRetentionMetrics(
    params: {
      skip?: number;
      limit?: number;
    } = {},
  ) {
    return api.list<RetentionMetric>('/financial-health/retention', params);
  },

  computeRetention(payload: ComputeRetentionPayload) {
    return api.post<RetentionMetric>('/financial-health/retention/compute', payload);
  },

  listCashflowForecasts(
    params: {
      start_month?: string;
      end_month?: string;
      skip?: number;
      limit?: number;
    } = {},
  ) {
    return api.list<CashflowForecast>('/financial-health/cashflow', params);
  },

  computeCashflow(payload: ComputeCashflowPayload) {
    return api.post<CashflowForecast[]>('/financial-health/cashflow/compute', payload);
  },

  getCostPerStudent(academicYearId: string) {
    return api.get<CostPerStudentAnalysis>('/financial-health/cost-per-student', {
      academic_year_id: academicYearId,
    });
  },

  computeCostPerStudent(payload: ComputeCostPerStudentPayload) {
    return api.post<CostPerStudentAnalysis>('/financial-health/cost-per-student/compute', payload);
  },

  getSnapshot(snapshotDate?: string) {
    return api.get<FinancialSnapshot>('/financial-health/snapshot', {
      snapshot_date: snapshotDate || undefined,
    });
  },

  computeSnapshot(payload: ComputeFinancialSnapshotPayload) {
    return api.post<FinancialSnapshot>('/financial-health/snapshot/compute', payload);
  },

  getDashboard() {
    return api.get<FinancialHealthDashboard>('/financial-health/dashboard');
  },

  getTrends(months = 12) {
    return api.get<FinancialHealthTrends>('/financial-health/trends', { months });
  },

  exportCsv() {
    return downloadExport('csv');
  },

  exportPdf() {
    return downloadExport('pdf');
  },
};
