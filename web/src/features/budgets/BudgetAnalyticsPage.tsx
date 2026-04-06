import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ErrorBanner, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import { useBudgetAnalytics } from './useBudgets';

const madFormatter = new Intl.NumberFormat('fr-MA', {
  style: 'currency',
  currency: 'MAD',
});

export function BudgetAnalyticsPage() {
  const { t, i18n } = useTranslation();
  const analyticsQuery = useBudgetAnalytics();

  const trendData = useMemo(
    () =>
      (analyticsQuery.data?.spending_trend ?? []).map((item) => ({
        ...item,
        label: formatDate(item.date, i18n.language, { day: '2-digit', month: 'short' }),
      })),
    [analyticsQuery.data?.spending_trend, i18n.language]
  );

  return (
    <div className="page budgets-analytics-page">
      <div className="page-header">
        <h1 className="page-title">{t('budgets.analytics')}</h1>
      </div>

      <ErrorBanner error={toBannerError(analyticsQuery.error, t('app.error'))} />

      <div className="gradebook-page__stats">
        <StatCard label="budgets.totalBudget" value={madFormatter.format(analyticsQuery.data?.total_budget ?? 0)} />
        <StatCard label="budgets.totalSpent" value={madFormatter.format(analyticsQuery.data?.total_spent ?? 0)} />
        <StatCard label="budgets.remaining" value={madFormatter.format(analyticsQuery.data?.remaining ?? 0)} />
        <StatCard label="budgets.requestCount" value={analyticsQuery.data?.request_count ?? 0} />
      </div>

      <div className="budgets-analytics-page__charts">
        <div className="card budgets-page__chart">
          <h2 className="attendance-page__section-title">{t('budgets.spendingTrend')}</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip formatter={(value: number) => madFormatter.format(value)} />
              <Line dataKey="amount" stroke="var(--color-primary)" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card budgets-page__chart">
          <h2 className="attendance-page__section-title">{t('budgets.categoryBreakdown')}</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={analyticsQuery.data?.category_breakdown ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip formatter={(value: number) => madFormatter.format(value)} />
              <Bar dataKey="amount" fill="var(--color-accent)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
