import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useSaveConstraints, useTimetableConstraints } from './useTimetable';
import type {
  RoomConstraint,
  TeacherAvailability,
  TimetableConstraints,
} from './timetable.service';

const DAYS = [
  { value: 1, label: 'Lundi' },
  { value: 2, label: 'Mardi' },
  { value: 3, label: 'Mercredi' },
  { value: 4, label: 'Jeudi' },
  { value: 5, label: 'Vendredi' },
  { value: 6, label: 'Samedi' },
];

const EMPTY_AVAIL: TeacherAvailability = {
  teacher_id: '',
  day_of_week: 1,
  available_from: '08:00',
  available_until: '17:00',
};

const EMPTY_ROOM: RoomConstraint = { room_name: '', capacity: 30 };
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function TimetableConstraintsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialAcademicYearId = searchParams.get('academicYearId') ?? '';
  const [academicYearId, setAcademicYearId] = useState(initialAcademicYearId);
  const selectedAcademicYearId = UUID_PATTERN.test(academicYearId.trim())
    ? academicYearId.trim()
    : '';
  const constraintsQuery = useTimetableConstraints(selectedAcademicYearId);
  const saveMutation = useSaveConstraints();

  const [maxConsecutive, setMaxConsecutive] = useState(3);
  const [availability, setAvailability] = useState<TeacherAvailability[]>([]);
  const [rooms, setRooms] = useState<RoomConstraint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (constraintsQuery.data) {
      const d = constraintsQuery.data;
      setAcademicYearId(d.academic_year_id);
      setMaxConsecutive(d.max_consecutive_classes);
      setAvailability(d.teacher_availability);
      setRooms(d.room_constraints);
    }
  }, [constraintsQuery.data]);

  function updateAvail(index: number, field: keyof TeacherAvailability, value: string | number) {
    setAvailability((prev) => prev.map((a, i) => (i === index ? { ...a, [field]: value } : a)));
  }

  function updateRoom(index: number, field: keyof RoomConstraint, value: string | number) {
    setRooms((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaved(false);
    const payload: TimetableConstraints = {
      academic_year_id: selectedAcademicYearId,
      max_consecutive_classes: maxConsecutive,
      teacher_availability: availability,
      room_constraints: rooms,
    };
    try {
      await saveMutation.mutateAsync(payload);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (constraintsQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('timetable.constraints.title')}</h1>
          <p className="page-subtitle">{t('timetable.constraints.subtitle')}</p>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() =>
              navigate(
                selectedAcademicYearId
                  ? `/timetable/generate?academicYearId=${encodeURIComponent(selectedAcademicYearId)}`
                  : '/timetable/generate',
              )
            }
          >
            {t('timetable.generate.title')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={
          error ?? (constraintsQuery.error instanceof Error ? constraintsQuery.error.message : null)
        }
        onDismiss={() => setError(null)}
        onRetry={() => void constraintsQuery.refetch()}
      />

      <form onSubmit={handleSave}>
        {/* Global */}
        <section style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 15, marginBottom: 12 }}>{t('timetable.constraints.global')}</h2>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <div className="form-field" style={{ flex: 1, minWidth: 200 }}>
              <label>{t('timetable.constraints.academicYear')}</label>
              <input
                className="input"
                required
                value={academicYearId}
                onChange={(e) => setAcademicYearId(e.target.value)}
                placeholder={t('timetable.constraints.academicYearPlaceholder')}
              />
            </div>
            <div className="form-field" style={{ minWidth: 160 }}>
              <label>{t('timetable.constraints.maxConsecutive')}</label>
              <input
                type="number"
                className="input"
                min={1}
                max={8}
                value={maxConsecutive}
                onChange={(e) => setMaxConsecutive(Number(e.target.value))}
              />
            </div>
          </div>
        </section>

        {/* Teacher availability */}
        <section style={{ marginBottom: 28 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
            }}
          >
            <h2 style={{ fontSize: 15 }}>{t('timetable.constraints.teacherAvailability')}</h2>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '4px 10px' }}
              onClick={() => setAvailability((p) => [...p, { ...EMPTY_AVAIL }])}
            >
              + {t('timetable.constraints.addAvailability')}
            </button>
          </div>
          {availability.length === 0 && (
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {t('timetable.constraints.noAvailability')}
            </p>
          )}
          {availability.map((a, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                gap: 10,
                alignItems: 'flex-end',
                marginBottom: 8,
                flexWrap: 'wrap',
              }}
            >
              <div className="form-field" style={{ flex: 2, minWidth: 160 }}>
                {i === 0 && <label>{t('timetable.constraints.teacherId')}</label>}
                <input
                  className="input"
                  required
                  placeholder={t('timetable.constraints.teacherIdPlaceholder')}
                  value={a.teacher_id}
                  onChange={(e) => updateAvail(i, 'teacher_id', e.target.value)}
                />
              </div>
              <div className="form-field" style={{ minWidth: 130 }}>
                {i === 0 && <label>{t('timetable.constraints.day')}</label>}
                <select
                  className="input"
                  value={a.day_of_week}
                  onChange={(e) => updateAvail(i, 'day_of_week', Number(e.target.value))}
                >
                  {DAYS.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-field" style={{ minWidth: 110 }}>
                {i === 0 && <label>{t('timetable.constraints.from')}</label>}
                <input
                  type="time"
                  className="input"
                  value={a.available_from}
                  onChange={(e) => updateAvail(i, 'available_from', e.target.value)}
                />
              </div>
              <div className="form-field" style={{ minWidth: 110 }}>
                {i === 0 && <label>{t('timetable.constraints.until')}</label>}
                <input
                  type="time"
                  className="input"
                  required
                  value={a.available_until}
                  onChange={(e) => updateAvail(i, 'available_until', e.target.value)}
                />
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: '6px 10px', marginBottom: 0 }}
                onClick={() => setAvailability((p) => p.filter((_, j) => j !== i))}
              >
                ✕
              </button>
            </div>
          ))}
        </section>

        {/* Room constraints */}
        <section style={{ marginBottom: 28 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
            }}
          >
            <h2 style={{ fontSize: 15 }}>{t('timetable.constraints.rooms')}</h2>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '4px 10px' }}
              onClick={() => setRooms((p) => [...p, { ...EMPTY_ROOM }])}
            >
              + {t('timetable.constraints.addRoom')}
            </button>
          </div>
          {rooms.length === 0 && (
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {t('timetable.constraints.noRooms')}
            </p>
          )}
          {rooms.map((r, i) => (
            <div
              key={i}
              style={{ display: 'flex', gap: 10, alignItems: 'flex-end', marginBottom: 8 }}
            >
              <div className="form-field" style={{ flex: 2 }}>
                {i === 0 && <label>{t('timetable.constraints.roomName')}</label>}
                <input
                  className="input"
                  required
                  placeholder={t('timetable.constraints.roomNamePlaceholder')}
                  value={r.room_name}
                  onChange={(e) => updateRoom(i, 'room_name', e.target.value)}
                />
              </div>
              <div className="form-field" style={{ minWidth: 110 }}>
                {i === 0 && <label>{t('timetable.constraints.capacity')}</label>}
                <input
                  type="number"
                  className="input"
                  required
                  min={1}
                  value={r.capacity}
                  onChange={(e) => updateRoom(i, 'capacity', Number(e.target.value))}
                />
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: '6px 10px', marginBottom: 0 }}
                onClick={() => setRooms((p) => p.filter((_, j) => j !== i))}
              >
                ✕
              </button>
            </div>
          ))}
        </section>

        <div style={{ display: 'flex', gap: 8 }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={saveMutation.isPending || !selectedAcademicYearId}
          >
            {saveMutation.isPending ? t('app.loading') : saved ? t('app.saved') : t('app.save')}
          </button>
        </div>
      </form>
    </div>
  );
}
