/**
 * Teacher Attendance — mark attendance per class session.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /teacher/classes, GET /teacher/classes/{id}/students,
 *        GET /teacher/periods, POST /attendance/sessions.
 */

import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useCreateAttendanceSession,
  useTeacherClasses,
  useTeacherClassStudents,
  useTeacherPeriods,
} from './useTeacher';
import type { StudentItem } from './teacher.service';

interface StudentRecord {
  student_id: string;
  status: string;
  absence_reason: string;
}

const SLOTS = ['slot_1', 'slot_2', 'slot_3', 'slot_4', 'slot_5', 'slot_6'];
const STATUS_OPTIONS = ['present', 'absent', 'late', 'excused'];

export function AttendancePage() {
  const { t } = useTranslation();
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedPeriodId, setSelectedPeriodId] = useState('');
  const [sessionDate, setSessionDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [slot, setSlot] = useState('slot_1');
  const [records, setRecords] = useState<StudentRecord[]>([]);

  const classesQuery = useTeacherClasses();
  const periodsQuery = useTeacherPeriods();
  const studentsQuery = useTeacherClassStudents(selectedClassId || null);
  const createSessionMutation = useCreateAttendanceSession();

  const classes = classesQuery.data ?? [];
  const periods = periodsQuery.data ?? [];
  const students: StudentItem[] = studentsQuery.data ?? [];
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          classesQuery.error ?? periodsQuery.error ?? studentsQuery.error ?? createSessionMutation.error,
          t('app.error')
        ),
      [classesQuery.error, createSessionMutation.error, periodsQuery.error, studentsQuery.error, t]
    )
  );

  useEffect(() => {
    if (periods.length > 0 && !selectedPeriodId) {
      setSelectedPeriodId(periods[0].id);
    }
  }, [periods, selectedPeriodId]);

  useEffect(() => {
    if (!students.length) {
      setRecords([]);
      return;
    }
    setRecords(students.map((student) => ({
      student_id: student.id,
      status: 'present',
      absence_reason: '',
    })));
  }, [students]);

  function updateRecord(index: number, field: keyof StudentRecord, value: string) {
    setRecords((current) => {
      const next = [...current];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedClassId || !selectedPeriodId || records.length === 0) return;
    await createSessionMutation.mutateAsync({
      class_id: selectedClassId,
      period_id: selectedPeriodId,
      session_date: sessionDate,
      slot,
      records: records.map((record) => ({
        student_id: record.student_id,
        status: record.status,
        absence_reason: record.status === 'absent' ? record.absence_reason || null : null,
      })),
    });
    setSuccess(t('teacher.attendance.saved'));
  }

  if (classesQuery.isLoading || periodsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.attendance.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void Promise.all([
          classesQuery.refetch(),
          periodsQuery.refetch(),
          selectedClassId ? studentsQuery.refetch() : Promise.resolve(null),
        ])}
      />

      {success && (
        <div className="card" role="status" aria-live="polite" style={{ background: 'var(--color-surface-success)', borderColor: 'var(--color-success)', marginBottom: 16, padding: 12, fontSize: 14 }}>
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="filters-bar">
          <select className="filter-select" aria-label={t('teacher.attendance.selectClass')} value={selectedClassId} onChange={(e) => setSelectedClassId(e.target.value)} required>
            <option value="">{t('teacher.attendance.selectClass')}</option>
            {classes.map((item) => (
              <option key={item.id} value={item.id}>{item.code} — {item.name}</option>
            ))}
          </select>
          <select className="filter-select" aria-label={t('teacher.attendance.selectPeriod', { defaultValue: 'Select period' })} value={selectedPeriodId} onChange={(e) => setSelectedPeriodId(e.target.value)} required>
            {periods.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label || `${item.date_start} → ${item.date_end}`}
              </option>
            ))}
          </select>
          <input type="date" className="filter-input" aria-label={t('teacher.attendance.date', { defaultValue: 'Session date' })} value={sessionDate} onChange={(e) => setSessionDate(e.target.value)} required />
          <select className="filter-select" aria-label={t('teacher.attendance.slot', { defaultValue: 'Attendance slot' })} value={slot} onChange={(e) => setSlot(e.target.value)}>
            {SLOTS.map((item) => (
              <option key={item} value={item}>{t(`teacher.attendance.${item}`)}</option>
            ))}
          </select>
        </div>

        {studentsQuery.isLoading && <LoadingState />}

        {students.length > 0 && (
          <>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('teacher.attendance.student')}</th>
                    <th>{t('teacher.attendance.status')}</th>
                    <th>{t('teacher.attendance.reason')}</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((student, index) => (
                    <tr key={student.id}>
                      <td style={{ fontWeight: 600 }}>{student.full_name}</td>
                      <td>
                        <select
                          className="filter-select"
                          aria-label={t('teacher.attendance.status')}
                          value={records[index]?.status || 'present'}
                          onChange={(e) => updateRecord(index, 'status', e.target.value)}
                          style={{ minWidth: 120 }}
                        >
                          {STATUS_OPTIONS.map((item) => (
                            <option key={item} value={item}>
                              {t(`teacher.attendance.status_${item}`)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        {records[index]?.status === 'absent' && (
                          <input
                            className="filter-input"
                            aria-label={t('teacher.attendance.reason')}
                            value={records[index]?.absence_reason || ''}
                            onChange={(e) => updateRecord(index, 'absence_reason', e.target.value)}
                            placeholder={t('teacher.attendance.reasonPlaceholder')}
                            style={{ minWidth: 200 }}
                          />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: 16 }}>
              <button className="btn btn-primary" type="submit" disabled={createSessionMutation.isPending}>
                {createSessionMutation.isPending ? t('app.loading') : t('teacher.attendance.submit')}
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
}
