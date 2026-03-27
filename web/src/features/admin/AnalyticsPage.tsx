/**
 * Analytics Dashboard — KPI cards + trend charts with recharts.
 *
 * Reference: Phase 8A — Analytics Dashboard
 * Calls GET /kpis?period={days}.
 * Auto-refresh every 5 minutes.
 * Date range selector: 7d, 30d, 90d.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';

interface KpiItem {
  kpi_id: string;
  name: string;
  value: number | null;
  unit: string;
  numerator?: number;
  denominator?: number;
  period: string;
  threshold?: string;
  data_source?: string;
  note?: string;
  computed_at?: string;
}

interface KpisResponse {
  kpis: KpiItem[];
  period: string;
  computed_at: string;
}

const PERIODS = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
] as const;

const AUTO_REFRESH_MS = 5 * 60 * 1000; // 5 minutes

export function AnalyticsPage() {
  const { t } = useTranslation();
  const [kpis, setKpis] = useState<KpiItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState(7);
  const [history, setHistory] = useState<KpiItem[][]>([]);
  const refreshRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchKpis = useCallback(async () => {
    try {
      const resp = await api.get<KpisResponse>('/kpis', { period: period });
      setKpis(resp.data.kpis);
      setError(null);
      // Append to history for trend (keep last 10 data points)
      setHistory((prev) => {
        const next = [...prev, resp.data.kpis];
        return next.length > 10 ? next.slice(-10) : next;
      });
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [period, t]);

  useEffect(() => {
    setLoading(true);
    setHistory([]);
    fetchKpis().finally(() => setLoading(false));
  }, [fetchKpis]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    refreshRef.current = setInterval(() => {
      fetchKpis();
    }, AUTO_REFRESH_MS);
    return () => {
      if (refreshRef.current) clearInterval(refreshRef.current);
    };
  }, [fetchKpis]);

  // Build chart data from KPI items
  const adoptionKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-001');
  const usageKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-002');
  const authErrorKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-003');
  const latencyKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-004');
  const incidentKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-005');
  const conversionKpi = kpis.find((k) => k.kpi_id === 'KPI-G1-006');

  // Build trend data from history
  const trendData = history.map((snapshot, idx) => {
    const adoption = snapshot.find((k) => k.kpi_id === 'KPI-G1-001');
    const authErr = snapshot.find((k) => k.kpi_id === 'KPI-G1-003');
    const usage = snapshot.find((k) => k.kpi_id === 'KPI-G1-002');
    return {
      point: idx + 1,
      adoption: adoption?.value ?? 0,
      authErrors: authErr?.value ?? 0,
      usage: usage?.value ?? 0,
    };
  });

  // Bar chart data for current KPI breakdown
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

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 className="page-title" style={{ margin: 0 }}>{t('analytics.title')}</h1>

        {/* Period selector */}
        <div style={{ display: 'flex', gap: 8 }}>
          {PERIODS.map((p) => (
            <button
              key={p.days}
              className={`btn ${period === p.days ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setPeriod(p.days)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchKpis} />

      {/* KPI Cards */}
      <div className="stats-grid">
        <KpiCard
          title={t('analytics.adoption')}
          kpi={adoptionKpi}
          color="#4CAF50"
        />
        <KpiCard
          title={t('analytics.usage')}
          kpi={usageKpi}
          color="#2196F3"
        />
        <KpiCard
          title={t('analytics.authErrors')}
          kpi={authErrorKpi}
          color={authErrorKpi && authErrorKpi.value !== null && authErrorKpi.value > 1 ? '#F44336' : '#4CAF50'}
        />
        <KpiCard
          title={t('analytics.latency')}
          kpi={latencyKpi}
          color="#FF9800"
        />
        <KpiCard
          title={t('analytics.incidents')}
          kpi={incidentKpi}
          color="#9C27B0"
        />
        <KpiCard
          title={t('analytics.conversion')}
          kpi={conversionKpi}
          color="#009688"
        />
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 24 }}>
        {/* Trend Chart */}
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ marginBottom: 12, fontSize: 14, fontWeight: 600 }}>
            {t('analytics.trendTitle')}
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="point" />
              <YAxis unit="%" />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="adoption"
                stroke="#4CAF50"
                name={t('analytics.adoption')}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="usage"
                stroke="#2196F3"
                name={t('analytics.usage')}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="authErrors"
                stroke="#F44336"
                name={t('analytics.authErrors')}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart */}
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ marginBottom: 12, fontSize: 14, fontWeight: 600 }}>
            {t('analytics.breakdownTitle')}
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
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
              <Bar dataKey="value" fill="#2196F3" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Auto-refresh indicator */}
      <div style={{ textAlign: 'center', marginTop: 16, color: '#999', fontSize: 12 }}>
        {t('analytics.autoRefresh')}
        {kpis.length > 0 && kpis[0].computed_at && (
          <span> — {t('analytics.lastUpdated')}: {new Date(kpis[0].computed_at).toLocaleTimeString()}</span>
        )}
      </div>
    </div>
  );
}

function KpiCard({ title, kpi, color }: { title: string; kpi?: KpiItem; color: string }) {
  const { t } = useTranslation();

  const displayValue = kpi?.value !== null && kpi?.value !== undefined
    ? kpi.unit === 'percent'
      ? `${kpi.value}%`
      : kpi.unit === 'milliseconds'
        ? kpi.data_source === 'prometheus'
          ? t('analytics.prometheusSource')
          : `${kpi.value}ms`
        : `${kpi.value}`
    : '—';

  const subtitle = kpi?.numerator !== undefined && kpi?.denominator !== undefined
    ? `${kpi.numerator} / ${kpi.denominator}`
    : kpi?.threshold ?? '';

  return (
    <div className="stat-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div className="stat-value" style={{ color }}>{displayValue}</div>
      <div className="stat-label">{title}</div>
      {subtitle && (
        <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>{subtitle}</div>
      )}
    </div>
  );
}
