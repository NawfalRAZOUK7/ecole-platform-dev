import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { analyticsService } from '@/features/reports/analytics/api/analytics.api';
import { reportsService } from '@/features/reports/api/reports.api';
import { financialHealthService } from '@/features/reports/financial-health/api/financial-health.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

// ── analyticsService ──────────────────────────────────────────────────────────

describe('analyticsService', () => {
  const overviewPayload = {
    metrics: [
      {
        key: 'students',
        label: 'Total Students',
        value: { current: 200, previous: 180, change_percent: 11, trend: 'up' as const },
      },
    ],
  };

  const attendancePayload = {
    summary: {
      rate: { current: 90, previous: 88, change_percent: 2.3, trend: 'up' as const },
      total_records: 1000,
    },
    series: [],
  };

  const gradesPayload = {
    summary: {
      average: { current: 14, previous: 13, change_percent: 7.7, trend: 'up' as const },
      count: 500,
    },
    distribution: [],
  };

  const billingPayload = {
    summary: {
      invoiced: 100000,
      paid: 80000,
      outstanding: 20000,
      collection_rate: { current: 80, previous: 75, change_percent: 6.7, trend: 'up' as const },
    },
    series: [],
  };

  const engagementPayload = {
    summary: {
      registered_users: 200,
      dau: 50,
      mau: 150,
      active_users: { current: 50, previous: 45, change_percent: 11, trend: 'up' as const },
      engaged_users: 40,
    },
    funnel: [],
    feature_adoption: [],
  };

  it('getDashboard aggregates all analytics', async () => {
    server.use(
      http.get('/api/v1/analytics/overview', () =>
        HttpResponse.json({ data: overviewPayload, meta }),
      ),
      http.get('/api/v1/analytics/attendance', () =>
        HttpResponse.json({ data: attendancePayload, meta }),
      ),
      http.get('/api/v1/analytics/grades', () => HttpResponse.json({ data: gradesPayload, meta })),
      http.get('/api/v1/analytics/billing', () =>
        HttpResponse.json({ data: billingPayload, meta }),
      ),
      http.get('/api/v1/analytics/engagement', () =>
        HttpResponse.json({ data: engagementPayload, meta }),
      ),
    );

    const result = await analyticsService.getDashboard({
      fromDate: '2025-01-01',
      toDate: '2025-01-31',
      compare: false,
      attendanceBucket: 'daily',
      billingBucket: 'monthly',
      subject: '',
    });

    expect(result.overview.metrics).toHaveLength(1);
    expect(result.attendance.summary.total_records).toBe(1000);
    expect(result.grades.summary.count).toBe(500);
  });
});

// ── reportsService ────────────────────────────────────────────────────────────

describe('reportsService', () => {
  const reportJob = {
    id: 'job-1',
    type: 'student_report_card' as const,
    status: 'pending' as const,
    parameters: {},
    created_at: new Date().toISOString(),
    completed_at: null,
    expires_at: null,
    error_message: null,
    download_url: null,
    cache_hit: false,
  };

  const schedule = {
    id: 'sched-1',
    name: 'Weekly Report',
    report_type: 'class_summary' as const,
    cron_expression: '0 9 * * MON',
    parameters: {},
    is_active: true,
    created_at: new Date().toISOString(),
    last_run_at: null,
    next_run_at: null,
  };

  it('getReportOptions returns options', async () => {
    server.use(
      http.get('/api/v1/reports/options', () =>
        HttpResponse.json({ data: { classes: [], periods: [], students: [], parents: [] }, meta }),
      ),
    );
    const result = await reportsService.getReportOptions('student_report_card');
    expect(result.data.classes).toEqual([]);
  });

  it('listReportJobs returns jobs', async () => {
    server.use(
      http.get('/api/v1/reports', () => HttpResponse.json({ data: [reportJob], meta: listMeta })),
    );
    const result = await reportsService.listReportJobs({});
    expect(result.data).toHaveLength(1);
  });

  it('generateReport posts report generation', async () => {
    server.use(
      http.post('/api/v1/reports/generate', () => HttpResponse.json({ data: reportJob, meta })),
    );
    const result = await reportsService.generateReport({
      type: 'student_report_card',
      student_id: 'student-1',
    });
    expect(result.data.id).toBe('job-1');
  });

  it('createSchedule posts new schedule', async () => {
    server.use(
      http.post('/api/v1/reports/schedules', () => HttpResponse.json({ data: schedule, meta })),
    );
    const result = await reportsService.createSchedule({
      name: 'Weekly Report',
      report_type: 'class_summary',
      cron_expression: '0 9 * * MON',
    });
    expect(result.data.id).toBe('sched-1');
  });

  it('listSchedules returns schedules', async () => {
    server.use(
      http.get('/api/v1/reports/schedules', () =>
        HttpResponse.json({ data: [schedule], meta: listMeta }),
      ),
    );
    const result = await reportsService.listSchedules();
    expect(result.data).toHaveLength(1);
  });

  it('updateSchedule puts schedule', async () => {
    server.use(
      http.put('/api/v1/reports/schedules/sched-1', () =>
        HttpResponse.json({ data: { ...schedule, is_active: false }, meta }),
      ),
    );
    const result = await reportsService.updateSchedule('sched-1', { is_active: false });
    expect(result.data.is_active).toBe(false);
  });

  it('deleteSchedule deletes schedule', async () => {
    server.use(
      http.delete('/api/v1/reports/schedules/sched-1', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await reportsService.deleteSchedule('sched-1');
    expect(result).toBeDefined();
  });

  it('runSchedule posts immediate run', async () => {
    server.use(
      http.post('/api/v1/reports/schedules/sched-1/run', () =>
        HttpResponse.json({ data: reportJob, meta }),
      ),
    );
    const result = await reportsService.runSchedule('sched-1');
    expect(result.data.status).toBe('pending');
  });

  it('getJobStatus returns job status', async () => {
    server.use(
      http.get('/api/v1/reports/job-1/status', () =>
        HttpResponse.json({ data: { ...reportJob, status: 'ready' as const }, meta }),
      ),
    );
    const result = await reportsService.getJobStatus('job-1');
    expect(result.data.status).toBe('ready');
  });

  it('downloadReport returns download url', async () => {
    server.use(
      http.get('/api/v1/reports/job-1/download', () =>
        HttpResponse.json({ data: { download_url: 'https://example.com/report.pdf' }, meta }),
      ),
    );
    const result = await reportsService.downloadReport('job-1');
    expect(result.data.download_url).toBeTruthy();
  });
});

// ── financialHealthService ────────────────────────────────────────────────────

describe('financialHealthService', () => {
  it('listRetentionMetrics returns metrics', async () => {
    server.use(
      http.get('/api/v1/financial-health/retention', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await financialHealthService.listRetentionMetrics();
    expect(result.data).toEqual([]);
  });

  it('computeRetention posts computation', async () => {
    server.use(
      http.post('/api/v1/financial-health/retention/compute', () =>
        HttpResponse.json({
          data: { month: '2025-01', retention_rate: 95, enrolled: 200, renewed: 190 },
          meta,
        }),
      ),
    );
    const result = await financialHealthService.computeRetention({ month: '2025-01' });
    expect(result.data).toBeDefined();
  });

  it('listCashflowForecasts returns forecasts', async () => {
    server.use(
      http.get('/api/v1/financial-health/cashflow', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await financialHealthService.listCashflowForecasts();
    expect(result.data).toEqual([]);
  });

  it('computeCashflow posts computation', async () => {
    server.use(
      http.post('/api/v1/financial-health/cashflow/compute', () =>
        HttpResponse.json({ data: [], meta }),
      ),
    );
    const result = await financialHealthService.computeCashflow({
      start_month: '2025-01',
      end_month: '2025-06',
    });
    expect(result.data).toEqual([]);
  });

  it('getCostPerStudent returns cost analysis', async () => {
    server.use(
      http.get('/api/v1/financial-health/cost-per-student', () =>
        HttpResponse.json({
          data: {
            academic_year_id: 'year-1',
            total_cost: 500000,
            student_count: 100,
            cost_per_student: 5000,
          },
          meta,
        }),
      ),
    );
    const result = await financialHealthService.getCostPerStudent('year-1');
    expect(result.data.cost_per_student).toBe(5000);
  });

  it('getSnapshot returns financial snapshot', async () => {
    server.use(
      http.get('/api/v1/financial-health/snapshot', () =>
        HttpResponse.json({
          data: { snapshot_date: '2025-01-31', revenue: 100000, expenses: 80000, net: 20000 },
          meta,
        }),
      ),
    );
    const result = await financialHealthService.getSnapshot();
    expect(result.data).toBeDefined();
  });

  it('getDashboard returns financial health dashboard', async () => {
    server.use(
      http.get('/api/v1/financial-health/dashboard', () =>
        HttpResponse.json({ data: { collection_rate: 85, outstanding_amount: 50000 }, meta }),
      ),
    );
    const result = await financialHealthService.getDashboard();
    expect(result.data).toBeDefined();
  });

  it('getTrends returns trends data', async () => {
    server.use(
      http.get('/api/v1/financial-health/trends', () =>
        HttpResponse.json({ data: { months: 12, series: [] }, meta }),
      ),
    );
    const result = await financialHealthService.getTrends();
    expect(result.data).toBeDefined();
  });
});
