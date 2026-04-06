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
import { formatCurrency, formatDate } from '@/shared/i18n';
import { ErrorBanner, LoadingState, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useFinancialCostPerStudent, useFinancialDashboard, useFinancialTrends } from './useFinancialHealth';

export function FinancialDashboardPage() {
  const { t, i18n } = useTranslation();
  const [academicYearId, setAcademicYearId] = useState('');
  const [months, setMonths] = useState(12);
  const dashboardQuery = useFinancialDashboard();
  const trendsQuery = useFinancialTrends(months);
  const costQuery = useFinancialCostPerStudent(academicYearId);

  const error = dashboardQuery.error ?? trendsQuery.error ?? costQuery.error;

  const retentionTrend = useMemo(
    () =>
      (trendsQuery.data?.retention_metrics ?? []).map((item) => ({
        label: `${item.academic_year_from} → ${item.academic_year_to}`,
        rate: item.retention_rate,
      })),
    [trendsQuery.data?.retention_metrics]
  );

  const monthlyCashflowData = useMemo(() => {
    const cashflow = dashboardQuery.data?.cashflow;
    if (!cashflow) {
      return [];
    }

    const net = cashflow.expected_income - cashflow.expected_expenses;
    return [
      { label: t('financialHealth.income'), amount: cashflow.expected_income, fill: 'var(--color-success)' },
      { label: t('financialHealth.expenses'), amount: -cashflow.expected_expenses, fill: 'var(--color-danger)' },
      { label: t('financialHealth.netCashflow'), amount: net, fill: 'var(--color-primary)' },
    ];
  }, [dashboardQuery.data?.cashflow, t]);

  const costComparisonData = useMemo(() => {
    if (!costQuery.data) {
      return [];
    }

    return [
      { label: t('financialHealth.costPerStudent'), amount: costQuery.data.cost_per_student },
      { label: t('financialHealth.revenuePerStudent'), amount: costQuery.data.revenue_per_student },
      { label: t('financialHealth.marginPerStudent'), amount: costQuery.data.margin_per_student },
    ];
  }, [costQuery.data, t]);

  if ((dashboardQuery.isLoading && !dashboardQuery.data) || (trendsQuery.isLoading && !trendsQuery.data)) {
    return <LoadingState />;
  }

  const retentionRate = dashboardQuery.data?.retention?.retention_rate ?? 0;
  const monthlyCashflow =
    (dashboardQuery.data?.cashflow?.expected_income ?? 0) -
    (dashboardQuery.data?.cashflow?.expected_expenses ?? 0);
  const outstandingBalance = Math.max(
    (dashboardQuery.data?.snapshot?.total_receivable ?? 0) -
      (dashboardQuery.data?.snapshot?.total_collected ?? 0),
    dashboardQuery.data?.snapshot?.overdue_amount ?? 0
  );
  const latestSnapshot = dashboardQuery.data?.snapshot ?? null;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('financialHealth.title')}</h1>
        <p className="page-subtitle">{t('financialHealth.subtitle')}</p>
      </div>

      <ErrorBanner error={toBannerError(error, t('app.error'))} />

      <div className="filters-bar">
        <input
          className="filter-input"
          value={academicYearId}
          onChange={(event) => setAcademicYearId(event.target.value)}
          placeholder={t('financialHealth.academicYearIdPlaceholder')}
        />
        <select
          className="filter-select"
          value={String(months)}
          onChange={(event) => setMonths(Number(event.target.value))}
        >
          <option value="6">{t('financialHealth.lastMonths', { count: 6 })}</option>
          <option value="12">{t('financialHealth.lastMonths', { count: 12 })}</option>
          <option value="24">{t('financialHealth.lastMonths', { count: 24 })}</option>
        </select>
      </div>

      <div className="stats-grid">
        <StatCard
          label="financialHealth.retentionRate"
          value={`${retentionRate.toFixed(1)}%`}
          icon="📈"
        />
        <StatCard
          label="financialHealth.avgCostPerStudent"
          value={academicYearId ? formatCurrency(costQuery.data?.cost_per_student ?? 0) : t('financialHealth.awaitingAcademicYear')}
          icon="🎓"
        />
        <StatCard
          label="financialHealth.monthlyCashflow"
          value={formatCurrency(monthlyCashflow)}
          icon="💸"
        />
        <StatCard
          label="financialHealth.outstandingBalance"
          value={formatCurrency(outstandingBalance)}
          icon="🧾"
        />
      </div>

      <div className="budgets-analytics-page__charts">
        <div className="card budgets-page__chart">
          <div className="page-header page-header--compact">
            <div>
              <h2>{t('financialHealth.retentionTrend')}</h2>
              <p>{t('financialHealth.retentionTrendHint')}</p>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={retentionTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="label" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
              <Legend />
              <Line
                type="monotone"
                dataKey="rate"
                name={t('financialHealth.retentionRate')}
                stroke="var(--color-primary)"
                strokeWidth={3}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card budgets-page__chart">
          <div className="page-header page-header--compact">
            <div>
              <h2>{t('financialHealth.cashflowWaterfall')}</h2>
              <p>{t('financialHealth.cashflowWaterfallHint')}</p>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={monthlyCashflowData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Bar dataKey="amount" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card budgets-page__chart">
          <div className="page-header page-header--compact">
            <div>
              <h2>{t('financialHealth.costComparison')}</h2>
              <p>{t('financialHealth.costComparisonHint')}</p>
            </div>
          </div>
          {academicYearId ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={costComparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Bar dataKey="amount" fill="var(--color-accent)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <p>{t('financialHealth.enterAcademicYear')}</p>
            </div>
          )}
        </div>
      </div>

      {latestSnapshot ? (
        <div className="card">
          <h2>{t('financialHealth.latestSnapshot')}</h2>
          <p>
            {formatDate(latestSnapshot.snapshot_date, i18n.language)} · {t('financialHealth.collectionRate')}:{' '}
            {latestSnapshot.collection_rate.toFixed(1)}%
          </p>
          <p>
            {t('financialHealth.totalReceivable')}: {formatCurrency(latestSnapshot.total_receivable)} ·{' '}
            {t('financialHealth.totalCollected')}: {formatCurrency(latestSnapshot.total_collected)}
          </p>
        </div>
      ) : null}
    </div>
  );
}
