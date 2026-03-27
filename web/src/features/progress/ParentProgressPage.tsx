/**
 * Parent Progress Overview — per-child progress summary cards with drill-down.
 *
 * Reference: Phase 12C — Parent Progress
 * Calls GET /progress/children for overview, navigates to /progress?studentId={id} for detail.
 */

import { useCallback, useEffect, useState } from 'react';
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
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';

/** Summary metrics for a single child, returned as part of the children overview. */
interface ChildSummary {
  student_id: string;
  student_name: string;
  grade_average: number;
  attendance_rate: number;
  content_completion_rate: number;
  /** Most recent graded assignment, if available. */
  latest_grade?: {
    score: number;
    assignment: string;
  };
}

interface ChartDataset {
  label: string;
  data: number[];
}

/** Response payload from `GET /progress/children` containing all children summaries and comparison chart data. */
interface ChildrenResponse {
  child_count: number;
  children: ChildSummary[];
  charts: {
    comparison: {
      labels: string[];
      datasets: ChartDataset[];
    };
  };
}

const BAR_COLORS = ['#2563eb', '#10b981', '#f59e0b'];

/**
 * Parent progress overview page.
 *
 * Shows a summary card per child with grade average, attendance rate, and
 * content completion. Clicking a card navigates to the full progress dashboard
 * for that child. When multiple children exist, a comparison bar chart is shown.
 *
 * @remarks
 * - Role: PAR only.
 * - API: `GET /progress/children`.
 * - Drill-down navigates to `/progress?studentId={id}`.
 */
export function ParentProgressPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [data, setData] = useState<ChildrenResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchChildren = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await api.get<{ data: ChildrenResponse }>('/progress/children');
      setData(resp.data.data);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    fetchChildren();
  }, [fetchChildren]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorBanner error={error} onRetry={fetchChildren} />;
  if (!data) return null;

  // Build comparison chart data
  const comparisonData = data.charts.comparison.labels.map((label, i) => {
    const point: Record<string, string | number> = { name: label };
    data.charts.comparison.datasets.forEach((ds) => {
      point[ds.label] = ds.data[i] ?? 0;
    });
    return point;
  });

  return (
    <div className="parent-progress">
      <h1 className="page-title">{t('progress.parentTitle')}</h1>

      {/* Child summary cards */}
      <div className="child-progress-cards">
        {data.children.map((child) => (
          <div
            key={child.student_id}
            className="child-progress-card"
            onClick={() => navigate(`/progress?studentId=${child.student_id}`)}
          >
            <div className="child-card-header">
              <div className="child-avatar">
                {child.student_name.charAt(0).toUpperCase()}
              </div>
              <h3 className="child-name">{child.student_name}</h3>
            </div>
            <div className="child-metrics">
              <div className="child-metric">
                <span className="metric-label">{t('progress.gradeAvg')}</span>
                <span className="metric-value" style={{ color: child.grade_average >= 80 ? '#10b981' : child.grade_average >= 50 ? '#f59e0b' : '#ef4444' }}>
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
                {t('progress.latestGrade')}: <strong>{child.latest_grade.score}</strong> — {child.latest_grade.assignment}
              </div>
            )}
            <div className="child-card-action">{t('progress.viewDetails')} &rarr;</div>
          </div>
        ))}
      </div>

      {/* Comparison chart */}
      {data.children.length > 1 && comparisonData.length > 0 && (
        <div className="chart-card" style={{ marginTop: 24 }}>
          <h3 className="chart-title">{t('progress.comparison')}</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              {data.charts.comparison.datasets.map((ds, i) => (
                <Bar key={ds.label} dataKey={ds.label} fill={BAR_COLORS[i % BAR_COLORS.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
