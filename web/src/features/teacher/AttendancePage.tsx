/**
 * Teacher Attendance — mark attendance per class session.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /teacher/classes, GET /teacher/classes/{id}/students,
 *        GET /teacher/periods, POST /attendance/sessions.
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';

interface ClassOption {
  id: string;
  code: string;
  name: string;
}

interface PeriodOption {
  id: string;
  label: string | null;
  date_start: string;
  date_end: string;
}

interface StudentItem {
  id: string;
  full_name: string;
  email: string;
}

interface StudentRecord {
  student_id: string;
  status: string;
  absence_reason: string;
}

const SLOTS = ['slot_1', 'slot_2', 'slot_3', 'slot_4', 'slot_5', 'slot_6'];
const STATUS_OPTIONS = ['present', 'absent', 'late', 'excused'];

export function AttendancePage() {
  const { t } = useTranslation();
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [periods, setPeriods] = useState<PeriodOption[]>([]);
  const [students, setStudents] = useState<StudentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedPeriodId, setSelectedPeriodId] = useState('');
  const [sessionDate, setSessionDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [slot, setSlot] = useState('slot_1');
  const [records, setRecords] = useState<StudentRecord[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const fetchInitial = useCallback(async () => {
    try {
      const [classesResp, periodsResp] = await Promise.all([
        api.get<ClassOption[]>('/teacher/classes'),
        api.get<PeriodOption[]>('/teacher/periods'),
      ]);
      setClasses(classesResp.data);
      setPeriods(periodsResp.data);
      if (periodsResp.data.length > 0) {
        setSelectedPeriodId(periodsResp.data[0].id);
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchInitial().finally(() => setLoading(false));
  }, [fetchInitial]);

  // When class changes, fetch students
  useEffect(() => {
    if (!selectedClassId) {
      setStudents([]);
      setRecords([]);
      return;
    }
    api.get<StudentItem[]>(`/teacher/classes/${selectedClassId}/students`)
      .then((resp) => {
        setStudents(resp.data);
        setRecords(resp.data.map((s) => ({
          student_id: s.id,
          status: 'present',
          absence_reason: '',
        })));
      })
      .catch(() => {
        setStudents([]);
        setRecords([]);
      });
  }, [selectedClassId]);

  function updateRecord(index: number, field: keyof StudentRecord, value: string) {
    setRecords((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedClassId || !selectedPeriodId || records.length === 0) return;
    setSubmitting(true);
    setSuccess(null);
    try {
      await api.post('/attendance/sessions', {
        class_id: selectedClassId,
        period_id: selectedPeriodId,
        session_date: sessionDate,
        slot,
        records: records.map((r) => ({
          student_id: r.student_id,
          status: r.status,
          absence_reason: r.status === 'absent' ? r.absence_reason || null : null,
        })),
      });
      setSuccess(t('teacher.attendance.saved'));
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
      setSuccess(null);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.attendance.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {success && (
        <div className="card" style={{ background: '#ecfdf5', borderColor: 'var(--color-success)', marginBottom: 16, padding: 12, fontSize: 14 }}>
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="filters-bar">
          <select
            className="filter-select"
            value={selectedClassId}
            onChange={(e) => setSelectedClassId(e.target.value)}
            required
          >
            <option value="">{t('teacher.attendance.selectClass')}</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
            ))}
          </select>
          <select
            className="filter-select"
            value={selectedPeriodId}
            onChange={(e) => setSelectedPeriodId(e.target.value)}
            required
          >
            {periods.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label || `${p.date_start} → ${p.date_end}`}
              </option>
            ))}
          </select>
          <input
            type="date"
            className="filter-input"
            value={sessionDate}
            onChange={(e) => setSessionDate(e.target.value)}
            required
          />
          <select
            className="filter-select"
            value={slot}
            onChange={(e) => setSlot(e.target.value)}
          >
            {SLOTS.map((s) => (
              <option key={s} value={s}>{t(`teacher.attendance.${s}`)}</option>
            ))}
          </select>
        </div>

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
                  {students.map((student, i) => (
                    <tr key={student.id}>
                      <td style={{ fontWeight: 600 }}>{student.full_name}</td>
                      <td>
                        <select
                          className="filter-select"
                          value={records[i]?.status || 'present'}
                          onChange={(e) => updateRecord(i, 'status', e.target.value)}
                          style={{ minWidth: 120 }}
                        >
                          {STATUS_OPTIONS.map((s) => (
                            <option key={s} value={s}>
                              {t(`teacher.attendance.status_${s}`)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        {records[i]?.status === 'absent' && (
                          <input
                            className="filter-input"
                            value={records[i]?.absence_reason || ''}
                            onChange={(e) => updateRecord(i, 'absence_reason', e.target.value)}
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
              <button className="btn btn-primary" type="submit" disabled={submitting}>
                {submitting ? t('app.loading') : t('teacher.attendance.submit')}
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
}
