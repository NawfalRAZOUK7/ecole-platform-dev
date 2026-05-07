import { memo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

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

const TREND_ICONS = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
};

const TREND_COLORS = {
  up: 'var(--color-success)',
  down: 'var(--color-danger)',
  flat: 'var(--color-text-secondary)',
};

export const StatCard = memo(function StatCard({ label, value, trend, icon }: StatCardProps) {
  const { t } = useTranslation();
  const TrendIcon = trend ? TREND_ICONS[trend.direction] : null;
  const trendColor = trend ? TREND_COLORS[trend.direction] : undefined;

  return (
    <article className="stat-card">
      <div className="stat-card__header">
        <span className="stat-card__label">{t(label)}</span>
        {icon && <span className="stat-card__icon">{icon}</span>}
      </div>
      <strong className="stat-card__value">{value}</strong>
      {trend && TrendIcon && (
        <span className="stat-card__trend" style={{ color: trendColor }}>
          <TrendIcon size={14} strokeWidth={2} style={{ marginInlineEnd: '4px' }} />
          <span>{trend.percentage}%</span>
        </span>
      )}
    </article>
  );
});
