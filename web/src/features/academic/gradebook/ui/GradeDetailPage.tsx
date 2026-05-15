import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { formatDate } from '@/shared/i18n';
import { DataTable, ErrorBanner, Skeleton, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { StudentGradeRow } from '../model/gradebook.types';
import { useStudentGrades } from '../model/useGradebook';

type StudentGradeTableRow = StudentGradeRow & Record<string, unknown>;

function computeTrend(grades: StudentGradeRow[]) {
  const available = grades.filter((grade) => grade.value !== null);
  if (available.length < 2) {
    return 'stable';
  }

  const first = available[0].value ?? 0;
  const last = available[available.length - 1].value ?? 0;
  if (last > first) {
    return 'improving';
  }
  if (last < first) {
    return 'declining';
  }
  return 'stable';
}

export function GradeDetailPage() {
  const { t, i18n } = useTranslation();
  const { studentId = '' } = useParams();
  const studentGradesQuery = useStudentGrades(studentId);
  const summary = studentGradesQuery.data;
  const grades = summary?.grades ?? [];

  const trend = useMemo(() => computeTrend(grades), [grades]);
  const chartData = useMemo(
    () =>
      grades.map((grade) => ({
        label: grade.title,
        score: grade.value ?? 0,
      })),
    [grades],
  );

  const stats = useMemo(() => {
    const values = grades
      .map((grade) => grade.value)
      .filter((value): value is number => value !== null);

    return {
      overallAverage: summary?.overall_average ?? 0,
      highestGrade: values.length === 0 ? 0 : Math.max(...values),
      lowestGrade: values.length === 0 ? 0 : Math.min(...values),
    };
  }, [grades, summary?.overall_average]);

  const columns: ColumnDef<StudentGradeTableRow>[] = useMemo(
    () => [
      {
        key: 'title',
        header: 'gradebook.assessment',
        render: (value) => <strong>{String(value)}</strong>,
      },
      {
        key: 'date',
        header: 'gradebook.date',
        render: (value) => formatDate(String(value), i18n.language),
      },
      {
        key: 'value',
        header: 'gradebook.score',
        render: (value) => {
          const numericValue = typeof value === 'number' && !Number.isNaN(value) ? value : null;
          return numericValue === null ? '—' : numericValue.toFixed(1);
        },
      },
      {
        key: 'weight',
        header: 'gradebook.weight',
        render: (value) => `${Math.round(Number(value) * 100)}%`,
      },
    ],
    [i18n.language],
  );

  return (
    <div className="page grade-detail-page">
      <div className="page-header">
        <h1 className="page-title">{summary?.student_name ?? t('gradebook.studentView')}</h1>
        <p className="page-subtitle">{summary?.class_name ?? t('gradebook.noData')}</p>
      </div>

      <ErrorBanner error={toBannerError(studentGradesQuery.error, t('app.error'))} />

      {studentGradesQuery.isLoading ? (
        <div className="gradebook-page__loading">
          <Skeleton variant="card" count={4} />
        </div>
      ) : (
        <>
          <div className="gradebook-page__stats">
            <StatCard label="gradebook.overallAverage" value={stats.overallAverage.toFixed(2)} />
            <StatCard label="gradebook.highestGrade" value={stats.highestGrade.toFixed(2)} />
            <StatCard label="gradebook.lowestGrade" value={stats.lowestGrade.toFixed(2)} />
            <StatCard label="gradebook.trend" value={t(`gradebook.${trend}`)} />
          </div>

          <div className="card grade-detail-page__chart">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="label" />
                <YAxis domain={[0, 20]} />
                <Tooltip />
                <Bar dataKey="score">
                  {chartData.map((entry) => (
                    <Cell
                      key={entry.label}
                      fill={entry.score >= 10 ? 'var(--color-success)' : 'var(--color-error)'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <DataTable
            columns={columns}
            data={grades as StudentGradeTableRow[]}
            loading={studentGradesQuery.isLoading}
            emptyMessage="gradebook.noData"
            ariaLabel={t('gradebook.studentView')}
          />
        </>
      )}
    </div>
  );
}
