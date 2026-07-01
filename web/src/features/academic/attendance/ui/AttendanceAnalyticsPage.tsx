import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { useAuth } from '@/app/providers/AuthContext';
import { formatDate } from '@/shared/i18n';
import { useTeacherClasses } from '@/features/lms/teacher/model/useTeacher';
import { attendanceService } from '../api/attendance.api';
import { useAttendanceAlerts, useAttendanceTrends } from '../model/useAttendance';
import { useProgramsQuery } from '@/features/academic/programs/model/usePrograms';
import { Badge, DataTable, ErrorBanner, Skeleton, Tabs } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { AttendanceAlert } from '../model/attendance.types';

const TODAY = new Date().toISOString().split('T')[0];
type AttendanceAlertTableRow = AttendanceAlert & Record<string, unknown>;

function getDateOffset(offset: number) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return date.toISOString().split('T')[0];
}

export function AttendanceAnalyticsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedProgramId, setSelectedProgramId] = useState('');
  const [from, setFrom] = useState(getDateOffset(-29));
  const [to, setTo] = useState(TODAY);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const classesQuery = useTeacherClasses();
  const programsQuery = useProgramsQuery(true);
  const trendsQuery = useAttendanceTrends(selectedClassId, { from, to });
  const alertsQuery = useAttendanceAlerts(user?.school_id ?? '', selectedProgramId || undefined);

  useEffect(() => {
    if (!selectedClassId && (classesQuery.data?.length ?? 0) > 0) {
      setSelectedClassId(classesQuery.data?.[0].id ?? '');
    }
  }, [classesQuery.data, selectedClassId]);

  const bannerError = useMemo(
    () =>
      toBannerError(classesQuery.error ?? trendsQuery.error ?? alertsQuery.error, t('app.error')),
    [alertsQuery.error, classesQuery.error, t, trendsQuery.error],
  );

  const chartData = useMemo(
    () =>
      (trendsQuery.data ?? []).map((trend) => ({
        label: formatDate(trend.date, i18n.language, { day: '2-digit', month: '2-digit' }),
        rate: trend.total === 0 ? 0 : Math.round((trend.present / trend.total) * 100),
        present: trend.present,
        absent: trend.absent,
        late: trend.late,
      })),
    [i18n.language, trendsQuery.data],
  );

  const alertColumns: ColumnDef<AttendanceAlertTableRow>[] = useMemo(
    () => [
      {
        key: 'student_name',
        header: 'attendance.name',
        render: (value) => <strong>{String(value)}</strong>,
      },
      {
        key: 'absent_count',
        header: 'attendance.absentDays',
      },
      {
        key: 'consecutive_absences',
        header: 'attendance.consecutiveAbsences',
      },
      {
        key: 'alert_level',
        header: 'attendance.alertLevel',
        sortable: false,
        render: (value) => (
          <Badge variant={value === 'critical' ? 'error' : 'warning'}>{String(value)}</Badge>
        ),
      },
    ],
    [],
  );

  async function handleExport(format: 'csv' | 'pdf') {
    if (!selectedClassId) {
      return;
    }

    setExportMessage(null);
    setExportError(null);
    setIsExporting(true);

    try {
      const response = await attendanceService.exportAttendance(selectedClassId, format);
      if (response.data.download_url) {
        window.open(response.data.download_url, '_blank', 'noopener,noreferrer');
      }
      setExportMessage(t('attendance.exportReady', { format: format.toUpperCase() }));
    } catch (error) {
      setExportError(error instanceof Error ? error.message : t('attendance.exportFailed'));
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className="page attendance-analytics-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('attendance.analytics')}</h1>
          <p className="page-subtitle">{t('attendance.export')}</p>
        </div>
        <div className="attendance-toolbar">
          <label className="attendance-filter">
            <span className="attendance-filter__label">{t('attendance.selectClass')}</span>
            <select
              className="filter-select"
              value={selectedClassId}
              onChange={(event) => setSelectedClassId(event.target.value)}
            >
              {(classesQuery.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.code} · {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="attendance-filter">
            <span className="attendance-filter__label">
              {t('analytics.programFilterLabel', { defaultValue: 'Program' })}
            </span>
            <select
              className="filter-select"
              aria-label={t('analytics.programFilterLabel', {
                defaultValue: 'Program',
              })}
              value={selectedProgramId}
              onChange={(event) => setSelectedProgramId(event.target.value)}
            >
              <option value="">
                {t('analytics.allPrograms', { defaultValue: 'All programs' })}
              </option>
              {(programsQuery.data ?? []).map((program) => (
                <option key={program.id} value={program.id}>
                  {program.code} — {program.name}
                </option>
              ))}
            </select>
          </label>
          <label className="attendance-filter">
            <span className="attendance-filter__label">{t('analytics.from')}</span>
            <input
              type="date"
              className="filter-input"
              value={from}
              lang="fr-MA"
              onChange={(event) => setFrom(event.target.value)}
            />
          </label>
          <label className="attendance-filter">
            <span className="attendance-filter__label">{t('analytics.to')}</span>
            <input
              type="date"
              className="filter-input"
              value={to}
              lang="fr-MA"
              onChange={(event) => setTo(event.target.value)}
            />
          </label>
          <div className="attendance-analytics-page__export">
            <button
              type="button"
              className="btn btn-secondary"
              disabled={isExporting}
              onClick={() => void handleExport('csv')}
            >
              {t('attendance.exportCsv')}
            </button>
            <button
              type="button"
              className="btn btn-primary"
              disabled={isExporting}
              onClick={() => void handleExport('pdf')}
            >
              {isExporting ? t('app.loading') : t('attendance.exportPdf')}
            </button>
          </div>
        </div>
      </div>

      <ErrorBanner error={bannerError ?? exportError} />

      {exportMessage && (
        <div className="attendance-banner attendance-banner--success">{exportMessage}</div>
      )}

      <Tabs
        defaultTab="trends"
        tabs={[
          {
            id: 'trends',
            label: 'attendance.trends',
            content: trendsQuery.isLoading ? (
              <div className="attendance-history__skeleton">
                <Skeleton variant="card" count={2} />
              </div>
            ) : (
              <div className="attendance-analytics-page__chart">
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="label" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="rate"
                      stroke="var(--color-primary)"
                      strokeWidth={3}
                      name={t('attendance.rate')}
                    />
                    <Line
                      type="monotone"
                      dataKey="absent"
                      stroke="var(--color-error)"
                      strokeWidth={2}
                      name={t('attendance.absent')}
                    />
                    <Line
                      type="monotone"
                      dataKey="late"
                      stroke="var(--color-warning)"
                      strokeWidth={2}
                      name={t('attendance.late')}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ),
          },
          {
            id: 'alerts',
            label: 'attendance.alerts',
            content: (
              <DataTable
                columns={alertColumns}
                data={(alertsQuery.data ?? []) as AttendanceAlertTableRow[]}
                loading={alertsQuery.isLoading}
                emptyMessage="attendance.noRecords"
                ariaLabel={t('attendance.alerts')}
              />
            ),
          },
        ]}
      />
    </div>
  );
}
