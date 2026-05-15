/**
 * Analytics Dashboard — KPI cards + trend charts with recharts.
 *
 * Reference: Phase 8A — Analytics Dashboard
 * Calls GET /kpis?period={days}.
 * Auto-refresh every 5 minutes.
 * Date range selector: 7d, 30d, 90d.
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Bar,
  BarChart,
  CartesianGrid,
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
import { useAdminAnalytics } from '@/features/admin/model/useAdmin';
import type { KpiItem } from '@/features/admin/api/admin.api';

const PERIODS = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
] as const;

export function AnalyticsPage() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState(7);
  const analyticsQuery = useAdminAnalytics(period);
  const dismissibleError = useDismissibleError(
    useMemo(() => toBannerError(analyticsQuery.error, t('app.error')), [analyticsQuery.error, t]),
  );
  const kpis = analyticsQuery.data?.kpis ?? [];
  const history = analyticsQuery.history;

  const adoptionKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-001');
  const usageKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-002');
  const authErrorKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-003');
  const latencyKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-004');
  const incidentKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-005');
  const conversionKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-006');

  const trendData = history.map((snapshot, index) => {
    const adoption = snapshot.find((k) => k.kpi_id === 'KPI-G1-001');
    const authErr = snapshot.find((k) => k.kpi_id === 'KPI-G1-003');
    const usage = snapshot.find((k) => k.kpi_id === 'KPI-G1-002');
    return {
      point: index + 1,
      adoption: adoption?.value ?? 0,
      authErrors: authErr?.value ?? 0,
      usage: usage?.value ?? 0,
    };
  });

  const barData = [
    {
      name: t('analytics.adoption'),
      value: adoptionKpi?.value ?? 0,
      numerator: adoptionKpi?.numerator ?? 0,
      denominator: adoptionKpi?.denominator ?? 0,
    },
    {
      name: t('analytics.usage'),
      value: usageKpi?.value ?? 0,
      numerator: usageKpi?.numerator ?? 0,
      denominator: usageKpi?.denominator ?? 0,
    },
    {
      name: t('analytics.conversion'),
      value: conversionKpi?.value ?? 0,
      numerator: conversionKpi?.numerator ?? 0,
      denominator: conversionKpi?.denominator ?? 0,
    },
  ];

  if (analyticsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <h1 className="page-title" style={{ margin: 0 }}>
          {t('analytics.title')}
        </h1>

        <div style={{ display: 'flex', gap: 8 }}>
          {PERIODS.map((item) => (
            <button
              key={item.days}
              className={`btn ${period === item.days ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setPeriod(item.days)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void analyticsQuery.refetch()}
      />

      <div className="stats-grid">
        <KpiCard title={t('analytics.adoption')} kpi={adoptionKpi} color="var(--color-success)" />
        <KpiCard title={t('analytics.usage')} kpi={usageKpi} color="var(--color-primary)" />
        <KpiCard
          title={t('analytics.authErrors')}
          kpi={authErrorKpi}
          color={
            authErrorKpi && authErrorKpi.value !== null && authErrorKpi.value > 1
              ? 'var(--color-error)'
              : 'var(--color-success)'
          }
        />
        <KpiCard title={t('analytics.latency')} kpi={latencyKpi} color="var(--color-accent)" />
        <KpiCard
          title={t('analytics.incidents')}
          kpi={incidentKpi}
          color="var(--color-secondary)"
        />
        <KpiCard title={t('analytics.conversion')} kpi={conversionKpi} color="var(--color-info)" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 24 }}>
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ marginBottom: 12, fontSize: 14, fontWeight: 600 }}>
            {t('analytics.trendTitle')}
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="point" />
              <YAxis unit="%" />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="adoption"
                stroke="var(--color-success)"
                name={t('analytics.adoption')}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="usage"
                stroke="var(--color-primary)"
                name={t('analytics.usage')}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="authErrors"
                stroke="var(--color-error)"
                name={t('analytics.authErrors')}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ marginBottom: 12, fontSize: 14, fontWeight: 600 }}>
            {t('analytics.breakdownTitle')}
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="name" />
              <YAxis unit="%" />
              <Tooltip
                formatter={(value, _name, entry) => {
                  const payload = entry?.payload as
                    | { numerator?: number; denominator?: number }
                    | undefined;
                  return [
                    `${value}% (${payload?.numerator ?? 0}/${payload?.denominator ?? 0})`,
                    '',
                  ];
                }}
              />
              <Bar dataKey="value" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div
        style={{
          textAlign: 'center',
          marginTop: 16,
          color: 'var(--color-text-secondary)',
          fontSize: 12,
        }}
      >
        {t('analytics.autoRefresh')}
        {kpis.length > 0 && kpis[0].computed_at && (
          <span>
            {' '}
            — {t('analytics.lastUpdated')}: {new Date(kpis[0].computed_at).toLocaleTimeString()}
          </span>
        )}
      </div>
    </div>
  );
}

function KpiCard({ title, kpi, color }: { title: string; kpi?: KpiItem; color: string }) {
  const { t } = useTranslation();

  const displayValue =
    kpi?.value !== null && kpi?.value !== undefined
      ? kpi.unit === 'percent'
        ? `${kpi.value}%`
        : kpi.unit === 'milliseconds'
          ? kpi.data_source === 'prometheus'
            ? t('analytics.prometheusSource')
            : `${kpi.value}ms`
          : `${kpi.value}`
      : '—';

  const subtitle =
    kpi?.numerator !== undefined && kpi?.denominator !== undefined
      ? `${kpi.numerator} / ${kpi.denominator}`
      : (kpi?.threshold ?? '');

  return (
    <div className="stat-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div className="stat-value" style={{ color }}>
        {displayValue}
      </div>
      <div className="stat-label">{title}</div>
      {subtitle && (
        <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 4 }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}
