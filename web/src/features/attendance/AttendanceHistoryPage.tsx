import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { formatDate } from '@/shared/i18n';
import { ErrorBanner, Skeleton, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { AttendanceRecord, AttendanceStatus } from './attendance.types';
import { useStudentHistory } from './useAttendance';

const TODAY = new Date().toISOString().split('T')[0];

function getDateOffset(offset: number) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return date.toISOString().split('T')[0];
}

function isInRange(recordDate: string, from: string, to: string) {
  return recordDate >= from && recordDate <= to;
}

function getHeatmapColor(status: AttendanceStatus | undefined) {
  if (status === 'present') return 'var(--color-success)';
  if (status === 'absent') return 'var(--color-error)';
  if (status === 'late') return 'var(--color-warning)';
  if (status === 'excused') return 'var(--color-text-secondary)';
  return 'color-mix(in srgb, var(--color-border) 80%, var(--color-surface))';
}

function buildHeatmapDays(endDate: string) {
  const end = new Date(endDate);
  return Array.from({ length: 30 }, (_, index) => {
    const current = new Date(end);
    current.setDate(end.getDate() - 29 + index);
    return current.toISOString().split('T')[0];
  });
}

export function AttendanceHistoryPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [from, setFrom] = useState(getDateOffset(-29));
  const [to, setTo] = useState(TODAY);

  const historyQuery = useStudentHistory(user?.id ?? '');
  const records = historyQuery.data ?? [];
  const bannerError = useMemo(
    () => toBannerError(historyQuery.error, t('app.error')),
    [historyQuery.error, t]
  );

  const filteredRecords = useMemo(
    () => records.filter((record) => isInRange(record.date.slice(0, 10), from, to)),
    [from, records, to]
  );

  const heatmapDays = useMemo(() => buildHeatmapDays(to), [to]);
  const historyMap = useMemo(() => {
    const map = new Map<string, AttendanceRecord>();
    filteredRecords.forEach((record) => {
      map.set(record.date.slice(0, 10), record);
    });
    return map;
  }, [filteredRecords]);

  const stats = useMemo(() => {
    const presentCount = filteredRecords.filter((record) => record.status === 'present').length;
    const absentCount = filteredRecords.filter((record) => record.status === 'absent').length;
    const lateCount = filteredRecords.filter((record) => record.status === 'late').length;
    const totalDays = filteredRecords.length;
    const presentRate = totalDays === 0 ? 0 : Math.round((presentCount / totalDays) * 100);

    return {
      totalDays,
      presentRate,
      absentCount,
      lateCount,
    };
  }, [filteredRecords]);

  return (
    <div className="page attendance-history-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('attendance.history')}</h1>
          <p className="page-subtitle">{t('attendance.lastThirtyDays')}</p>
        </div>
        <div className="attendance-toolbar">
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
        </div>
      </div>

      <ErrorBanner error={bannerError} />

      {historyQuery.isLoading ? (
        <div className="attendance-history__skeleton">
          <Skeleton variant="card" count={4} />
          <Skeleton variant="card" count={1} />
        </div>
      ) : (
        <>
          <div className="attendance-history__stats">
            <StatCard label="attendance.totalDays" value={stats.totalDays} />
            <StatCard label="attendance.presentRate" value={`${stats.presentRate}%`} />
            <StatCard label="attendance.absentCount" value={stats.absentCount} />
            <StatCard label="attendance.lateCount" value={stats.lateCount} />
          </div>

          <div className="card attendance-history__card">
            <div className="attendance-history__header">
              <h2 className="attendance-page__section-title">{t('attendance.history')}</h2>
              <span className="attendance-page__summary">
                {formatDate(from, i18n.language)} → {formatDate(to, i18n.language)}
              </span>
            </div>

            <div className="attendance-heatmap" role="grid" aria-label={t('attendance.history')}>
              {heatmapDays.map((day) => {
                const record = historyMap.get(day);
                return (
                  <div
                    key={day}
                    role="gridcell"
                    className="attendance-heatmap__cell"
                    style={{
                      backgroundColor: getHeatmapColor(record?.status),
                      color: record ? 'var(--color-surface)' : 'var(--color-text)',
                    }}
                    title={`${formatDate(day, i18n.language)} · ${
                      record ? t(`attendance.${record.status}`) : t('attendance.noRecords')
                    }`}
                  >
                    <span className="attendance-heatmap__day">
                      {new Date(day).getDate()}
                    </span>
                    <span className="attendance-heatmap__label">
                      {record ? t(`attendance.${record.status}`) : '—'}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="attendance-heatmap__legend">
              {(['present', 'absent', 'late', 'excused'] as AttendanceStatus[]).map((status) => (
                <div key={status} className="attendance-heatmap__legend-item">
                  <span
                    className="attendance-heatmap__legend-swatch"
                    style={{ backgroundColor: getHeatmapColor(status) }}
                  />
                  <span>{t(`attendance.${status}`)}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
