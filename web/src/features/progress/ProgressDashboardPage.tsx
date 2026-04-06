/**
 * Student Progress Dashboard — 4 charts (grade trend, content completion, activity scores, attendance).
 *
 * Reference: Phase 12C — Student Progress Dashboard
 * STD sees own progress via GET /progress/me.
 * PAR sees child progress via GET /progress/student/{id} (passed as ?studentId query param).
 */

import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
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
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useProgressDashboard } from './useProgress';

const PIE_COLORS = ['var(--color-success)', 'var(--color-warning)', 'var(--color-error)'];
const DONUT_COLORS = ['var(--color-success)', 'var(--color-error)', 'var(--color-primary)', 'var(--color-warning)'];

export function ProgressDashboardPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const studentId = searchParams.get('studentId');
  const progressQuery = useProgressDashboard(studentId);
  const data = progressQuery.data;

  if (progressQuery.isLoading) {
    return <LoadingState />;
  }

  if (progressQuery.error || !data) {
    return <ErrorBanner error={progressQuery.error instanceof Error ? progressQuery.error.message : t('app.error')} onRetry={() => void progressQuery.refetch()} />;
  }

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

  const assessmentBarData = data.assessment_results.labels.map((label, i) => ({
    name: label,
    [data.assessment_results.datasets[0]?.label || 'score']: data.assessment_results.datasets[0]?.data[i] ?? 0,
    [data.assessment_results.datasets[1]?.label || 'max']: data.assessment_results.datasets[1]?.data[i] ?? 0,
  }));

  const gradeKey = data.grade_trends.datasets[0]?.label || 'avg';
  const activityKey = data.activity_scores.datasets[0]?.label || 'score';
  const assessScoreKey = data.assessment_results.datasets[0]?.label || 'score';
  const assessMaxKey = data.assessment_results.datasets[1]?.label || 'max';

  return (
    <div className="progress-dashboard">
      <h1 className="page-title">
        {studentId ? `${t('progress.title')} — ${data.student_name}` : t('progress.myProgress')}
      </h1>

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

      <div className="progress-charts-grid">
        <div className="chart-card">
          <h3 className="chart-title">{t('progress.gradeTrend')}</h3>
          {gradeTrendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={gradeTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey={gradeKey} stroke="var(--color-primary)" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">{t('progress.noData')}</p>
          )}
        </div>

        <div className="chart-card">
          <h3 className="chart-title">{t('progress.contentCompletion')}</h3>
          {contentPieData.some((item) => item.value > 0) ? (
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
                  {contentPieData.map((_, index) => (
                    <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">{t('progress.noData')}</p>
          )}
        </div>

        <div className="chart-card">
          <h3 className="chart-title">{t('progress.activityScores')}</h3>
          {activityBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={activityBarData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey={activityKey} fill="var(--color-secondary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">{t('progress.noData')}</p>
          )}
        </div>

        <div className="chart-card">
          <h3 className="chart-title">{t('progress.attendance')}</h3>
          {attendanceDonutData.some((item) => item.value > 0) ? (
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
                  {attendanceDonutData.map((_, index) => (
                    <Cell key={index} fill={DONUT_COLORS[index % DONUT_COLORS.length]} />
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

        <div className="chart-card chart-card--wide">
          <h3 className="chart-title">{t('progress.assessmentResults')}</h3>
          {assessmentBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={assessmentBarData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
                <YAxis domain={[0, 'auto']} />
                <Tooltip />
                <Legend />
                <Bar dataKey={assessScoreKey} fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
                <Bar dataKey={assessMaxKey} fill="var(--color-border)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">{t('progress.noData')}</p>
          )}
        </div>
      </div>
    </div>
  );
}
