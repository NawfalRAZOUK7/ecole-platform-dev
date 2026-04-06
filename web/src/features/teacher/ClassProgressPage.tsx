/**
 * Class Progress Page — teacher sees class-wide averages + per-student breakdown.
 *
 * Reference: Phase 12C — Teacher Class Progress
 * Calls GET /progress/class/{classId}. Class selector from existing teacher classes.
 */

import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useTeacherClassProgress, useTeacherClasses } from './useTeacher';

type SortKey = 'student_name' | 'grade_average' | 'attendance_rate' | 'content_completion_rate';

export function ClassProgressPage() {
  const { t } = useTranslation();
  const [selectedClass, setSelectedClass] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('student_name');
  const [sortAsc, setSortAsc] = useState(true);

  const classesQuery = useTeacherClasses();
  const progressQuery = useTeacherClassProgress(selectedClass || null);
  const classes = classesQuery.data ?? [];
  const data = progressQuery.data ?? null;
  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(classesQuery.error ?? progressQuery.error, t('app.error')),
      [classesQuery.error, progressQuery.error, t]
    )
  );

  useEffect(() => {
    if (!selectedClass && classes.length > 0) {
      setSelectedClass(classes[0].id);
    }
  }, [classes, selectedClass]);

  const sortedStudents = data
    ? [...data.students].sort((a, b) => {
        const av = a[sortKey];
        const bv = b[sortKey];
        if (typeof av === 'string') {
          return sortAsc ? av.localeCompare(bv as string) : (bv as string).localeCompare(av);
        }
        return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
      })
    : [];

  const gradeChartData = data
    ? data.charts.grade_comparison.labels.map((label, index) => ({
        name: label,
        [data.charts.grade_comparison.datasets[0]?.label || 'grade']: data.charts.grade_comparison.datasets[0]?.data[index] ?? 0,
      }))
    : [];

  const sortArrow = (key: SortKey) => (sortKey === key ? (sortAsc ? ' ▲' : ' ▼') : '');
  const colorForGrade = (value: number) => (value >= 80 ? 'var(--color-success)' : value >= 50 ? 'var(--color-warning)' : 'var(--color-error)');

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
      return;
    }
    setSortKey(key);
    setSortAsc(key === 'student_name');
  }

  if (classesQuery.isLoading || progressQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="class-progress">
      <h1 className="page-title">{t('progress.classTitle')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void Promise.all([classesQuery.refetch(), selectedClass ? progressQuery.refetch() : Promise.resolve(null)])}
      />

      <div className="class-selector">
        <label>{t('progress.selectClass')}</label>
        <select value={selectedClass} onChange={(e) => setSelectedClass(e.target.value)}>
          {classes.map((item) => (
            <option key={item.id} value={item.id}>{item.name} ({item.code})</option>
          ))}
        </select>
      </div>

      {data && (
        <>
          <div className="progress-summary-cards">
            <div className="summary-card">
              <span className="summary-label">{t('progress.classGradeAvg')}</span>
              <span className="summary-value">{data.class_averages.grade_average.toFixed(1)}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">{t('progress.classAttendance')}</span>
              <span className="summary-value">{data.class_averages.attendance_rate.toFixed(0)}%</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">{t('progress.classContent')}</span>
              <span className="summary-value">{data.class_averages.content_completion_rate.toFixed(0)}%</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">{t('progress.studentCount')}</span>
              <span className="summary-value">{data.student_count}</span>
            </div>
          </div>

          {gradeChartData.length > 0 && (
            <div className="chart-card">
              <h3 className="chart-title">{t('progress.gradeComparison')}</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={gradeChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey={data.charts.grade_comparison.datasets[0]?.label || 'grade'} fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="progress-table-card">
            <h3 className="chart-title">{t('progress.perStudent')}</h3>
            <table className="progress-table">
              <thead>
                <tr>
                  <th onClick={() => handleSort('student_name')} style={{ cursor: 'pointer' }}>
                    {t('progress.studentName')}{sortArrow('student_name')}
                  </th>
                  <th onClick={() => handleSort('grade_average')} style={{ cursor: 'pointer' }}>
                    {t('progress.gradeAvg')}{sortArrow('grade_average')}
                  </th>
                  <th onClick={() => handleSort('attendance_rate')} style={{ cursor: 'pointer' }}>
                    {t('progress.attendanceRate')}{sortArrow('attendance_rate')}
                  </th>
                  <th onClick={() => handleSort('content_completion_rate')} style={{ cursor: 'pointer' }}>
                    {t('progress.contentRate')}{sortArrow('content_completion_rate')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedStudents.map((student) => (
                  <tr key={student.student_id}>
                    <td>{student.student_name}</td>
                    <td>
                      <span className="sparkline-value" style={{ color: colorForGrade(student.grade_average) }}>
                        {student.grade_average.toFixed(1)}
                      </span>
                    </td>
                    <td>{student.attendance_rate.toFixed(0)}%</td>
                    <td>{student.content_completion_rate.toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
