import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Funnel,
  FunnelChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useAnalyticsDashboard,
  useAnalyticsExport,
} from './useAnalytics';
import type {
  AttendancePayload,
  BillingPayload,
  Bucket,
  ComparisonMetric,
  EngagementPayload,
  ExportEntity,
  GradesPayload,
  OverviewPayload,
  RangePreset,
} from './analytics.service';

const RANGE_PRESETS: RangePreset[] = ['this_week', 'this_month', 'this_period', 'custom'];
const BUCKETS: Bucket[] = ['daily', 'weekly', 'monthly'];
const EXPORT_ENTITIES: ExportEntity[] = ['students', 'grades', 'attendance', 'invoices', 'payments'];

function buildRange(preset: RangePreset) {
  const today = new Date();
  const toDate = today.toISOString().slice(0, 10);
  const start = new Date(today);

  if (preset === 'this_week') {
    const day = today.getDay();
    const offset = day === 0 ? 6 : day - 1;
    start.setDate(today.getDate() - offset);
  } else if (preset === 'this_month') {
    start.setDate(1);
  } else if (preset === 'this_period') {
    start.setDate(today.getDate() - 29);
  }

  return {
    fromDate: start.toISOString().slice(0, 10),
    toDate,
  };
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function exportChart(container: HTMLDivElement | null, filename: string) {
  const svg = container?.querySelector('svg');
  if (!svg) {
    return;
  }

  const rect = svg.getBoundingClientRect();
  const width = Math.max(Math.round(rect.width), 900);
  const height = Math.max(Math.round(rect.height), 360);
  const serialized = new XMLSerializer().serializeToString(svg);
  const url = URL.createObjectURL(
    new Blob([serialized], { type: 'image/svg+xml;charset=utf-8' })
  );

  await new Promise<void>((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = width * 2;
      canvas.height = height * 2;
      const context = canvas.getContext('2d');

      if (!context) {
        URL.revokeObjectURL(url);
        reject(new Error('Canvas unavailable'));
        return;
      }

      context.scale(2, 2);
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, width, height);
      context.drawImage(image, 0, 0, width, height);
      canvas.toBlob((blob) => {
        URL.revokeObjectURL(url);
        if (blob) {
          downloadBlob(blob, filename);
        }
        resolve();
      }, 'image/png');
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Chart export failed'));
    };
    image.src = url;
  });
}

export function AnalyticsDashboardPage() {
  const { t } = useTranslation();
  const attendanceChartRef = useRef<HTMLDivElement | null>(null);
  const gradesChartRef = useRef<HTMLDivElement | null>(null);
  const billingChartRef = useRef<HTMLDivElement | null>(null);
  const engagementChartRef = useRef<HTMLDivElement | null>(null);

  const initialRange = buildRange('this_month');
  const [rangePreset, setRangePreset] = useState<RangePreset>('this_month');
  const [fromDate, setFromDate] = useState(initialRange.fromDate);
  const [toDate, setToDate] = useState(initialRange.toDate);
  const [compare, setCompare] = useState(true);
  const [attendanceBucket, setAttendanceBucket] = useState<Bucket>('weekly');
  const [billingBucket, setBillingBucket] = useState<Bucket>('monthly');
  const [subject, setSubject] = useState('');
  const [exportEntity, setExportEntity] = useState<ExportEntity>('attendance');
  const dashboardQuery = useAnalyticsDashboard({
    fromDate,
    toDate,
    compare,
    attendanceBucket,
    billingBucket,
    subject,
  });
  const exportMutation = useAnalyticsExport();
  const overview: OverviewPayload | null = dashboardQuery.data?.overview ?? null;
  const attendance: AttendancePayload | null = dashboardQuery.data?.attendance ?? null;
  const grades: GradesPayload | null = dashboardQuery.data?.grades ?? null;
  const billing: BillingPayload | null = dashboardQuery.data?.billing ?? null;
  const engagement: EngagementPayload | null = dashboardQuery.data?.engagement ?? null;
  const dismissibleError = useDismissibleError(
    toBannerError(dashboardQuery.error ?? exportMutation.error, t('app.error'))
  );

  useEffect(() => {
    if (rangePreset === 'custom') {
      return;
    }

    const nextRange = buildRange(rangePreset);
    setFromDate(nextRange.fromDate);
    setToDate(nextRange.toDate);
  }, [rangePreset]);

  const overviewMap = useMemo(() => {
    return Object.fromEntries(
      (overview?.metrics || []).map((item) => [item.key, item.value])
    ) as Record<string, ComparisonMetric>;
  }, [overview]);

  const billingWaterfall = useMemo(() => {
    if (!billing) {
      return [];
    }

    return [
      { label: t('analytics.stages.invoiced'), value: billing.summary.invoiced },
      { label: t('analytics.stages.paid'), value: billing.summary.paid },
      { label: t('analytics.stages.outstanding'), value: billing.summary.outstanding },
    ];
  }, [billing, t]);

  if (dashboardQuery.isLoading || !overview || !attendance || !grades || !billing || !engagement) {
    return <LoadingState />;
  }

  return (
    <div className="page analytics-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('analytics.title')}</h1>
          <p className="page-subtitle">{t('analytics.subtitle')}</p>
        </div>
        <div className="analytics-toolbar">
          <div className="analytics-toolbar__group">
            {RANGE_PRESETS.map((preset) => (
              <button
                key={preset}
                className={`btn ${rangePreset === preset ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setRangePreset(preset)}
              >
                {t(`analytics.presets.${preset}`)}
              </button>
            ))}
          </div>
          <label className="form-checkbox">
            <input type="checkbox" checked={compare} onChange={(event) => setCompare(event.target.checked)} />
            <span>{t('analytics.compare')}</span>
          </label>
        </div>
      </div>

      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} onRetry={() => void dashboardQuery.refetch()} />

      {rangePreset === 'custom' && (
        <div className="card analytics-filters">
          <label className="form-field">
            <span>{t('analytics.from')}</span>
            <input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} />
          </label>
          <label className="form-field">
            <span>{t('analytics.to')}</span>
            <input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} />
          </label>
        </div>
      )}

      <section className="analytics-kpis">
        <KpiCard title={t('analytics.kpis.activeUsers')} metric={overviewMap.active_users} />
        <KpiCard title={t('analytics.kpis.attendanceRate')} metric={overviewMap.attendance_rate} suffix="%" />
        <KpiCard title={t('analytics.kpis.averageGrade')} metric={overviewMap.average_grade} />
        <KpiCard title={t('analytics.kpis.collectionRate')} metric={overviewMap.collection_rate} suffix="%" />
      </section>

      <section className="analytics-grid">
        <article className="card chart-card" ref={attendanceChartRef}>
          <div className="chart-card__header">
            <div>
              <h2>{t('analytics.charts.attendance')}</h2>
              <p>{t('analytics.charts.attendanceHint')}</p>
            </div>
            <div className="page-actions">
              <select className="filter-select" value={attendanceBucket} onChange={(event) => setAttendanceBucket(event.target.value as Bucket)}>
                {BUCKETS.map((item) => (
                  <option key={item} value={item}>
                    {t(`analytics.buckets.${item}`)}
                  </option>
                ))}
              </select>
              <button className="btn btn-secondary btn-sm" onClick={() => void exportChart(attendanceChartRef.current, 'attendance-trend.png')}>
                {t('analytics.exportPng')}
              </button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={attendance.series}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2} name={t('analytics.kpis.attendanceRate')} />
            </LineChart>
          </ResponsiveContainer>
        </article>

        <article className="card chart-card" ref={gradesChartRef}>
          <div className="chart-card__header">
            <div>
              <h2>{t('analytics.charts.grades')}</h2>
              <p>{t('analytics.charts.gradesHint')}</p>
            </div>
            <div className="page-actions">
              <input
                className="analytics-subject-filter"
                placeholder={t('analytics.subjectPlaceholder')}
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
              />
              <button className="btn btn-secondary btn-sm" onClick={() => void exportChart(gradesChartRef.current, 'grade-distribution.png')}>
                {t('analytics.exportPng')}
              </button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={grades.distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#16a34a" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>

        <article className="card chart-card" ref={billingChartRef}>
          <div className="chart-card__header">
            <div>
              <h2>{t('analytics.charts.billing')}</h2>
              <p>{t('analytics.charts.billingHint')}</p>
            </div>
            <div className="page-actions">
              <select className="filter-select" value={billingBucket} onChange={(event) => setBillingBucket(event.target.value as Bucket)}>
                {BUCKETS.map((item) => (
                  <option key={item} value={item}>
                    {t(`analytics.buckets.${item}`)}
                  </option>
                ))}
              </select>
              <button className="btn btn-secondary btn-sm" onClick={() => void exportChart(billingChartRef.current, 'billing-waterfall.png')}>
                {t('analytics.exportPng')}
              </button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={billingWaterfall}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#f59e0b" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>

        <article className="card chart-card" ref={engagementChartRef}>
          <div className="chart-card__header">
            <div>
              <h2>{t('analytics.charts.engagement')}</h2>
              <p>{t('analytics.charts.engagementHint')}</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => void exportChart(engagementChartRef.current, 'engagement-funnel.png')}>
              {t('analytics.exportPng')}
            </button>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <FunnelChart>
              <Tooltip />
              <Funnel dataKey="value" data={engagement.funnel} isAnimationActive fill="#0f766e" />
            </FunnelChart>
          </ResponsiveContainer>
        </article>
      </section>

      <section className="card analytics-export-card">
        <div className="chart-card__header">
          <div>
            <h2>{t('analytics.exportDataTitle')}</h2>
            <p>{t('analytics.exportDataSubtitle')}</p>
          </div>
          <div className="page-actions">
            <select className="filter-select" value={exportEntity} onChange={(event) => setExportEntity(event.target.value as ExportEntity)}>
              {EXPORT_ENTITIES.map((item) => (
                <option key={item} value={item}>
                  {t(`analytics.exportEntities.${item}`)}
                </option>
              ))}
            </select>
            <button
              className="btn btn-secondary"
              onClick={() => {
                void exportMutation.mutateAsync({
                  format: 'csv',
                  entity: exportEntity,
                  filters: {
                    from_date: fromDate,
                    to_date: toDate,
                    subject,
                  },
                }).then((blob) => downloadBlob(blob, `${exportEntity}.csv`));
              }}
            >
              CSV
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                void exportMutation.mutateAsync({
                  format: 'xlsx',
                  entity: exportEntity,
                  filters: {
                    from_date: fromDate,
                    to_date: toDate,
                    subject,
                  },
                }).then((blob) => downloadBlob(blob, `${exportEntity}.xlsx`));
              }}
            >
              XLSX
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

function KpiCard({
  title,
  metric,
  suffix = '',
}: {
  title: string;
  metric: ComparisonMetric | undefined;
  suffix?: string;
}) {
  if (!metric) {
    return null;
  }

  const delta = metric.change_percent;
  const deltaClass = delta === null || delta === 0 ? 'delta-flat' : delta > 0 ? 'delta-positive' : 'delta-negative';

  return (
    <article className="card analytics-kpi-card">
      <span className="analytics-kpi-card__label">{title}</span>
      <strong className="analytics-kpi-card__value">
        {metric.current.toFixed(2)}
        {suffix}
      </strong>
      <span className={`analytics-kpi-card__delta ${deltaClass}`}>
        {delta === null ? '—' : `${delta > 0 ? '+' : ''}${delta.toFixed(1)}%`}
      </span>
    </article>
  );
}
