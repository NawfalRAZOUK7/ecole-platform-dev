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
import { useProgressDashboard } from '../model/useProgress';

const PIE_COLORS = ['var(--color-success)', 'var(--color-warning)', 'var(--color-error)'];
const DONUT_COLORS = [
  'var(--color-success)',
  'var(--color-error)',
  'var(--color-primary)',
  'var(--color-warning)',
];

function emptyChart() {
  return { labels: [], datasets: [] };
}

function metric(value: number | null | undefined): number {
  return value ?? 0;
}

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
    return (
      <ErrorBanner
        error={progressQuery.error instanceof Error ? progressQuery.error.message : t('app.error')}
        onRetry={() => void progressQuery.refetch()}
      />
    );
  }

  const gradeTrends = data.grade_trends ?? emptyChart();
  const contentCompletion = data.content_completion ?? {
    ...emptyChart(),
    summary: { total: 0, completed: 0, completion_rate: 0 },
  };
  const activityScores = data.activity_scores ?? emptyChart();
  const attendanceOverview = data.attendance?.overview ?? {
    ...emptyChart(),
    summary: { total: 0, present: 0, attendance_rate: 0 },
  };
  const assessmentResults = data.assessment_results ?? emptyChart();

  const gradeTrendData = gradeTrends.labels.map((label, i) => ({
    month: label,
    [gradeTrends.datasets[0]?.label || 'avg']: metric(gradeTrends.datasets[0]?.data[i]),
  }));

  const contentPieData = contentCompletion.labels.map((label, i) => ({
    name: label,
    value: metric(contentCompletion.datasets[0]?.data[i]),
  }));

  const activityBarData = activityScores.labels.map((label, i) => ({
    month: label,
    [activityScores.datasets[0]?.label || 'score']: metric(activityScores.datasets[0]?.data[i]),
  }));

  const attendanceDonutData = attendanceOverview.labels.map((label, i) => ({
    name: label,
    value: metric(attendanceOverview.datasets[0]?.data[i]),
  }));

  const assessmentBarData = assessmentResults.labels.map((label, i) => ({
    name: label,
    [assessmentResults.datasets[0]?.label || 'score']: metric(assessmentResults.datasets[0]?.data[i]),
    [assessmentResults.datasets[1]?.label || 'max']: metric(assessmentResults.datasets[1]?.data[i]),
  }));

  const gradeKey = gradeTrends.datasets[0]?.label || 'avg';
  const activityKey = activityScores.datasets[0]?.label || 'score';
  const assessScoreKey = assessmentResults.datasets[0]?.label || 'score';
  const assessMaxKey = assessmentResults.datasets[1]?.label || 'max';

  return (
    <div className="progress-dashboard">
      <h1 className="page-title">
        {studentId ? `${t('progress.title')} — ${data.student_name}` : t('progress.myProgress')}
      </h1>

      <div className="progress-summary-cards">
        <div className="summary-card">
          <span className="summary-label">{t('progress.gradeAvg')}</span>
          <span className="summary-value">
            {gradeTrends.datasets[0]?.data.length
              ? (
                  gradeTrends.datasets[0].data.reduce((a, b) => a + metric(b), 0) /
                  gradeTrends.datasets[0].data.length
                ).toFixed(1)
              : '—'}
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">{t('progress.contentRate')}</span>
          <span className="summary-value">
            {metric(contentCompletion.summary.completion_rate).toFixed(0)}%
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">{t('progress.attendanceRate')}</span>
          <span className="summary-value">
            {metric(attendanceOverview.summary.attendance_rate).toFixed(0)}%
          </span>
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
                <Line
                  type="monotone"
                  dataKey={gradeKey}
                  stroke="var(--color-primary)"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
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
            {t('progress.attendanceRate')}:{' '}
            <strong>{metric(attendanceOverview.summary.attendance_rate).toFixed(1)}%</strong> (
            {attendanceOverview.summary.present}/{attendanceOverview.summary.total})
          </div>
        </div>

        <div className="chart-card chart-card--wide">
          <h3 className="chart-title">{t('progress.assessmentResults')}</h3>
          {assessmentBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={assessmentBarData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 10 }}
                  angle={-20}
                  textAnchor="end"
                  height={50}
                />
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
