/**
 * Parent Progress Overview — per-child progress summary cards with drill-down.
 *
 * Reference: Phase 12C — Parent Progress
 * Calls GET /progress/children for overview, navigates to /progress?studentId={id} for detail.
 */

import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useChildrenProgressOverview } from '../model/useProgress';

const BAR_COLORS = ['var(--color-primary)', 'var(--color-success)', 'var(--color-warning)'];

export function ParentProgressPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const childrenQuery = useChildrenProgressOverview();
  const data = childrenQuery.data;

  if (childrenQuery.isLoading) {
    return <LoadingState />;
  }

  if (childrenQuery.error || !data) {
    return (
      <ErrorBanner
        error={childrenQuery.error instanceof Error ? childrenQuery.error.message : t('app.error')}
        onRetry={() => void childrenQuery.refetch()}
      />
    );
  }

  const comparisonData = data.charts.comparison.labels.map((label, index) => {
    const point: Record<string, string | number> = { name: label };
    data.charts.comparison.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[index] ?? 0;
    });
    return point;
  });

  return (
    <div className="parent-progress">
      <h1 className="page-title">{t('progress.parentTitle')}</h1>

      <div className="child-progress-cards">
        {data.children.map((child) => (
          <div
            key={child.student_id}
            className="child-progress-card"
            onClick={() => navigate(`/progress?studentId=${child.student_id}`)}
          >
            <div className="child-card-header">
              <div className="child-avatar">{child.student_name.charAt(0).toUpperCase()}</div>
              <h3 className="child-name">{child.student_name}</h3>
            </div>
            <div className="child-metrics">
              <div className="child-metric">
                <span className="metric-label">{t('progress.gradeAvg')}</span>
                <span
                  className="metric-value"
                  style={{
                    color:
                      child.grade_average >= 80
                        ? 'var(--color-success)'
                        : child.grade_average >= 50
                          ? 'var(--color-warning)'
                          : 'var(--color-error)',
                  }}
                >
                  {child.grade_average.toFixed(1)}
                </span>
              </div>
              <div className="child-metric">
                <span className="metric-label">{t('progress.attendanceRate')}</span>
                <span className="metric-value">{child.attendance_rate.toFixed(0)}%</span>
              </div>
              <div className="child-metric">
                <span className="metric-label">{t('progress.contentRate')}</span>
                <span className="metric-value">{child.content_completion_rate.toFixed(0)}%</span>
              </div>
            </div>
            {child.latest_grade && (
              <div className="child-latest">
                {t('progress.latestGrade')}: <strong>{child.latest_grade.score}</strong> —{' '}
                {child.latest_grade.assignment}
              </div>
            )}
            <div className="child-card-action">{t('progress.viewDetails')} &rarr;</div>
          </div>
        ))}
      </div>

      {data.children.length > 1 && comparisonData.length > 0 && (
        <div className="chart-card" style={{ marginTop: 24 }}>
          <h3 className="chart-title">{t('progress.comparison')}</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              {data.charts.comparison.datasets.map((dataset, index) => (
                <Bar
                  key={dataset.label}
                  dataKey={dataset.label}
                  fill={BAR_COLORS[index % BAR_COLORS.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
