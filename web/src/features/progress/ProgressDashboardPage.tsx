/**
 * Student Progress Dashboard — 4 charts (grade trend, content completion, activity scores, attendance).
 *
 * Reference: Phase 12C — Student Progress Dashboard
 * STD sees own progress via GET /progress/me.
 * PAR sees child progress via GET /progress/student/{id} (passed as ?studentId query param).
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import { api, ApiClientError } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';

interface ChartDataset {
  label: string;
  data: number[];
}

interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

interface AttendanceData {
  overview: ChartData & { summary: { total: number; present: number; attendance_rate: number } };
  trend: ChartData;
}

interface ContentCompletion extends ChartData {
  summary: { total: number; completed: number; completion_rate: number };
}

interface ProgressData {
  student_id: string;
  student_name: string;
  grade_trends: ChartData;
  content_completion: ContentCompletion;
  activity_scores: ChartData;
  attendance: AttendanceData;
  assessment_results: ChartData;
}

const PIE_COLORS = ['#10b981', '#f59e0b', '#ef4444'];
const DONUT_COLORS = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b'];

export function ProgressDashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const studentId = searchParams.get('studentId');
  const [data, setData] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProgress = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = studentId
        ? `/progress/student/${studentId}`
        : '/progress/me';
      const resp = await api.get<{ data: ProgressData }>(endpoint);
      setData(resp.data.data);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }, [studentId, t]);

  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorBanner message={error} onRetry={fetchProgress} />;
  if (!data) return null;

  // Transform chart data for recharts
  const gradeTrendData = data.grade_trends.labels.map((label, i) => ({
    month: label,
    [data.grade_trends.datasets[0]?.label || 'avg']: data.grade_trends.datasets[0]?.data[i] ?? 0,
  }));

  const contentPieData = data.content_completion.labels.map((label, i) => ({
    name: label,
    value: data.content_completion.datasets[0]?.data[i] ?? 0,
  }));

  const activityBarData = data.activity_scores.labels.map((label, i) => ({
    month: label,
    [data.activity_scores.datasets[0]?.label || 'score']: data.activity_scores.datasets[0]?.data[i] ?? 0,
  }));

  const attendanceDonutData = data.attendance.overview.labels.map((label, i) => ({
    name: label,
    value: data.attendance.overview.datasets[0]?.data[i] ?? 0,
  }));

  const gradeKey = data.grade_trends.datasets[0]?.label || 'avg';
  const activityKey = data.activity_scores.datasets[0]?.label || 'score';

  return (
    <div className="progress-dashboard">
      <h1 className="page-title">
        {studentId ? `${t('progress.title')} — ${data.student_name}` : t('progress.myProgress')}
      </h1>

      {/* Summary cards */}
      <div className="progress-summary-cards">
        <div className="summary-card">
          <span className="summary-label">{t('progress.gradeAvg')}</span>
          <span className="summary-value">
            {data.grade_trends.datasets[0]?.data.length
              ? (data.grade_trends.datasets[0].data.reduce((a, b) => a + b, 0) / data.grade_trends.datasets[0].data.length).toFixed(1)
              : '—'}
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">{t('progress.contentRate')}</span>
          <span className="summary-value">{data.content_completion.summary.completion_rate.toFixed(0)}%</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">{t('progress.attendanceRate')}</span>
          <span className="summary-value">{data.attendance.overview.summary.attendance_rate.toFixed(0)}%</span>
        </div>
      </div>

      {/* Charts grid */}
      <div className="progress-charts-grid">
        {/* Grade Trend Line Chart */}
        <div className="chart-card">
          <h3 className="chart-title">{t('progress.gradeTrend')}</h3>
          {gradeTrendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={gradeTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey={gradeKey} stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">{t('progress.noData')}</p>
          )}
        </div>

        {/* Content Completion Pie Chart */}
        <div className="chart-card">
          <h3 className="chart-title">{t('progress.contentCompletion')}</h3>
          {contentPieData.some((d) => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={contentPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {contentPieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">{t('progress.noData')}</p>
          )}
        </div>

        {/* Activity Scores Bar Chart */}
        <div className="chart-card">
          <h3 className="chart-title">{t('progress.activityScores')}</h3>
          {activityBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={activityBarData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey={activityKey} fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">{t('progress.noData')}</p>
          )}
        </div>

        {/* Attendance Donut Chart */}
        <div className="chart-card">
          <h3 className="chart-title">{t('progress.attendance')}</h3>
          {attendanceDonutData.some((d) => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={attendanceDonutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {attendanceDonutData.map((_, i) => (
                    <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">{t('progress.noData')}</p>
          )}
          <div className="attendance-summary">
            {t('progress.attendanceRate')}: <strong>{data.attendance.overview.summary.attendance_rate.toFixed(1)}%</strong>
            {' '}({data.attendance.overview.summary.present}/{data.attendance.overview.summary.total})
          </div>
        </div>
      </div>
    </div>
  );
}
