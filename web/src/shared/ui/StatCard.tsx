import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

interface Trend {
  direction: 'up' | 'down' | 'flat';
  percentage: number;
}

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: Trend;
  icon?: ReactNode;
}

export function StatCard({ label, value, trend, icon }: StatCardProps) {
  const { t } = useTranslation();
  const trendSymbol = trend?.direction === 'up' ? '↗' : trend?.direction === 'down' ? '↘' : '→';

  return (
    <article className="stat-card">
      <div className="stat-card__header">
        <span className="stat-card__label">{t(label)}</span>
        {icon && <span className="stat-card__icon">{icon}</span>}
      </div>
      <strong className="stat-card__value">{value}</strong>
      {trend && (
        <span className={`stat-card__trend stat-card__trend--${trend.direction}`}>
          <span aria-hidden="true">{trendSymbol}</span>
          <span>{trend.percentage}%</span>
        </span>
      )}
    </article>
  );
}
