/**
 * Class Progress Page — teacher sees class-wide averages + per-student breakdown.
 *
 * Reference: Phase 12C — Teacher Class Progress
 * Calls GET /progress/class/{classId}. Class selector from existing teacher classes.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';

interface StudentRow {
  student_id: string;
  student_name: string;
  grade_average: number;
  attendance_rate: number;
  content_completion_rate: number;
}

interface ClassAverages {
  grade_average: number;
  attendance_rate: number;
  content_completion_rate: number;
}

interface ChartDataset {
  label: string;
  data: number[];
}

interface ClassProgressData {
  class_id: string;
  class_name: string;
  student_count: number;
  students: StudentRow[];
  class_averages: ClassAverages;
  charts: {
    grade_comparison: { labels: string[]; datasets: ChartDataset[] };
    attendance_comparison: { labels: string[]; datasets: ChartDataset[] };
  };
}

interface ClassOption {
  id: string;
  name: string;
  code: string;
}

type SortKey = 'student_name' | 'grade_average' | 'attendance_rate' | 'content_completion_rate';

export function ClassProgressPage() {
  const { t } = useTranslation();
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [data, setData] = useState<ClassProgressData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('student_name');
  const [sortAsc, setSortAsc] = useState(true);

  // Fetch teacher's classes
  useEffect(() => {
    (async () => {
      try {
        const resp = await api.list<ClassOption>('/teacher/classes');
        const items = resp.data.data as unknown as ClassOption[];
        setClasses(items);
        if (items.length > 0) setSelectedClass(items[0].id);
      } catch (_) {}
    })();
  }, []);

  const fetchClassProgress = useCallback(async () => {
    if (!selectedClass) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await api.get<{ data: ClassProgressData }>(`/progress/class/${selectedClass}`);
      setData(resp.data.data);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }, [selectedClass, t]);

  useEffect(() => {
    fetchClassProgress();
  }, [fetchClassProgress]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === 'student_name');
    }
  };

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
    ? data.charts.grade_comparison.labels.map((label, i) => ({
        name: label,
        [data.charts.grade_comparison.datasets[0]?.label || 'grade']: data.charts.grade_comparison.datasets[0]?.data[i] ?? 0,
      }))
    : [];

  const sortArrow = (key: SortKey) =>
    sortKey === key ? (sortAsc ? ' ▲' : ' ▼') : '';

  const colorForGrade = (v: number) =>
    v >= 80 ? '#10b981' : v >= 50 ? '#f59e0b' : '#ef4444';

  return (
    <div className="class-progress">
      <h1 className="page-title">{t('progress.classTitle')}</h1>

      {/* Class selector */}
      <div className="class-selector">
        <label>{t('progress.selectClass')}</label>
        <select value={selectedClass} onChange={(e) => setSelectedClass(e.target.value)}>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
          ))}
        </select>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorBanner message={error} onRetry={fetchClassProgress} />}

      {data && !loading && (
        <>
          {/* Class averages */}
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

          {/* Grade comparison bar chart */}
          {gradeChartData.length > 0 && (
            <div className="chart-card">
              <h3 className="chart-title">{t('progress.gradeComparison')}</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={gradeChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar
                    dataKey={data.charts.grade_comparison.datasets[0]?.label || 'grade'}
                    fill="#2563eb"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Student table */}
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
                {sortedStudents.map((s) => (
                  <tr key={s.student_id}>
                    <td>{s.student_name}</td>
                    <td>
                      <span className="sparkline-value" style={{ color: colorForGrade(s.grade_average) }}>
                        {s.grade_average.toFixed(1)}
                      </span>
                    </td>
                    <td>{s.attendance_rate.toFixed(0)}%</td>
                    <td>{s.content_completion_rate.toFixed(0)}%</td>
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
