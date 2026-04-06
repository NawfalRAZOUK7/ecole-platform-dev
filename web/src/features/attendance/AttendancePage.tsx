import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { formatDate } from '@/shared/i18n';
import { Badge, DataTable, ErrorBanner, Skeleton } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useTeacherClasses } from '@/features/teacher/useTeacher';
import type { ClassOption } from '@/features/teacher/teacher.service';
import type { ColumnDef } from '@/shared/ui/DataTable';
import type { AttendanceRecord, AttendanceStatus } from './attendance.types';
import { useClassAttendance, useMarkAttendance } from './useAttendance';

interface AttendanceDraftRow extends AttendanceRecord {
  note: string;
}

type AttendanceDraftTableRow = AttendanceDraftRow & Record<string, unknown>;

const TODAY = new Date().toISOString().split('T')[0];
const STATUS_OPTIONS: AttendanceStatus[] = ['present', 'absent', 'late', 'excused'];

function getStatusBadgeVariant(status: AttendanceStatus) {
  if (status === 'present') return 'success';
  if (status === 'late') return 'warning';
  if (status === 'absent') return 'error';
  return 'neutral';
}

export function AttendancePage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedDate, setSelectedDate] = useState(TODAY);
  const [records, setRecords] = useState<AttendanceDraftRow[]>([]);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const classesQuery = useTeacherClasses();
  const attendanceQuery = useClassAttendance(selectedClassId, selectedDate);
  const markAttendanceMutation = useMarkAttendance();

  const classes = classesQuery.data ?? [];
  const bannerError = useMemo(
    () =>
      toBannerError(
        classesQuery.error ?? attendanceQuery.error ?? markAttendanceMutation.error,
        t('app.error')
      ),
    [attendanceQuery.error, classesQuery.error, markAttendanceMutation.error, t]
  );

  useEffect(() => {
    if (!selectedClassId && classes.length > 0) {
      setSelectedClassId(classes[0].id);
    }
  }, [classes, selectedClassId]);

  useEffect(() => {
    setRecords(
      (attendanceQuery.data ?? []).map((record) => ({
        ...record,
        note: record.justification ?? '',
      }))
    );
  }, [attendanceQuery.data]);

  function updateRecord(studentId: string, patch: Partial<AttendanceDraftRow>) {
    setSuccessMessage(null);
    setRecords((current) =>
      current.map((record) =>
        record.student_id === studentId ? { ...record, ...patch } : record
      )
    );
  }

  function handleMarkAllPresent() {
    setSuccessMessage(null);
    setRecords((current) =>
      current.map((record) => ({
        ...record,
        status: 'present',
      }))
    );
  }

  async function handleSubmit() {
    if (!selectedClassId || records.length === 0) {
      return;
    }

    await markAttendanceMutation.mutateAsync({
      class_id: selectedClassId,
      date: selectedDate,
      records: records.map((record) => ({
        student_id: record.student_id,
        status: record.status,
        note: record.note.trim() || undefined,
      })),
    });
    setSuccessMessage(t('attendance.saved'));
  }

  const selectedClass = classes.find((item) => item.id === selectedClassId);
  const columns: ColumnDef<AttendanceDraftTableRow>[] = useMemo(
    () => [
      {
        key: 'student_name',
        header: 'attendance.name',
        sortable: true,
        render: (value) => <strong>{String(value)}</strong>,
      },
      {
        key: 'status',
        header: 'attendance.status',
        sortable: false,
        render: (_value, row) => (
          <div className="attendance-status-group">
            {STATUS_OPTIONS.map((status) => {
              const isActive = row.status === status;
              return (
                <button
                  key={status}
                  type="button"
                  className={`attendance-status-pill attendance-status-pill--${status} ${
                    isActive ? 'attendance-status-pill--active' : ''
                  }`}
                  onClick={() => updateRecord(row.student_id, { status })}
                >
                  {t(`attendance.${status}`)}
                </button>
              );
            })}
          </div>
        ),
      },
      {
        key: 'justified',
        header: 'attendance.justified',
        sortable: false,
        render: (_value, row) => (
          <Badge variant={row.justified ? 'success' : 'neutral'}>
            {t(row.justified ? 'attendance.justifiedYes' : 'attendance.justifiedNo')}
          </Badge>
        ),
      },
      {
        key: 'note',
        header: 'attendance.note',
        sortable: false,
        render: (_value, row) => (
          <input
            type="text"
            className="filter-input attendance-page__note-input"
            value={row.note}
            placeholder={t('attendance.note')}
            onChange={(event) => updateRecord(row.student_id, { note: event.target.value })}
          />
        ),
      },
    ],
    [t]
  );

  return (
    <div className="page attendance-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('attendance.title')}</h1>
          <p className="page-subtitle">
            {selectedClass
              ? `${selectedClass.code} · ${selectedClass.name} · ${formatDate(selectedDate, i18n.language)}`
              : t('attendance.noRecords')}
          </p>
        </div>
        <div className="attendance-page__summary">
          <strong>{user?.role}</strong> · {formatDate(selectedDate, i18n.language)}
        </div>
      </div>

      <ErrorBanner error={bannerError} />

      {successMessage && <div className="attendance-banner attendance-banner--success">{successMessage}</div>}

      <div className="attendance-toolbar">
        <label className="attendance-filter">
          <span className="attendance-filter__label">{t('attendance.selectClass')}</span>
          <select
            className="filter-select"
            value={selectedClassId}
            onChange={(event) => setSelectedClassId(event.target.value)}
          >
            {classes.map((item: ClassOption) => (
              <option key={item.id} value={item.id}>
                {item.code} · {item.name}
              </option>
            ))}
          </select>
        </label>

        <label className="attendance-filter">
          <span className="attendance-filter__label">{t('attendance.date')}</span>
          <input
            type="date"
            className="filter-input"
            lang="fr-MA"
            value={selectedDate}
            onChange={(event) => setSelectedDate(event.target.value)}
          />
        </label>

        <div className="attendance-page__actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleMarkAllPresent}
            disabled={records.length === 0}
          >
            {t('attendance.markAll')}
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => void handleSubmit()}
            disabled={markAttendanceMutation.isPending || records.length === 0}
          >
            {markAttendanceMutation.isPending ? t('app.loading') : t('attendance.submit')}
          </button>
        </div>
      </div>

      {attendanceQuery.isLoading ? (
        <div className="attendance-page__skeleton">
          <Skeleton variant="card" count={2} />
          <Skeleton variant="table-row" count={6} />
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={records as AttendanceDraftTableRow[]}
          loading={attendanceQuery.isLoading}
          emptyMessage="attendance.noRecords"
          ariaLabel={t('attendance.title')}
          sortable
        />
      )}

      {records.length > 0 && (
        <div className="attendance-page__footer">
          {records.map((record) => (
            <Badge key={record.id} variant={getStatusBadgeVariant(record.status)}>
              {record.student_name}: {t(`attendance.${record.status}`)}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
