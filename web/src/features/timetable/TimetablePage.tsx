/**
 * Timetable page — weekly grid view (Mon-Sat), color-coded by subject.
 *
 * Reference: Phase 12A — Timetable UI
 * ADM: add/edit/delete slots + create exceptions (inline modals)
 * TCH: own schedule across classes (read-only)
 * STD/PAR: class schedule (read-only)
 */

import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useCreateTimetableException,
  useCreateTimetableSlot,
  useDeleteTimetableSlot,
  useTimetableClasses,
  useUpdateTimetableSlot,
  useWeeklyTimetable,
} from './useTimetable';
import type { ClassOption, ExceptionForm, SlotForm, TimetableSlot } from './timetable.service';

const DAYS = [1, 2, 3, 4, 5, 6]; // Mon-Sat
const SUBJECT_COLORS: Record<string, string> = {
  math: '#eff6ff',
  french: '#fef3c7',
  arabic: '#ecfdf5',
  science: '#f0fdf4',
  history: '#faf5ff',
  geography: '#fff7ed',
  english: '#fdf2f8',
  islamic_studies: '#f0f9ff',
  art: '#fefce8',
  sport: '#f0fdfa',
};

function getSubjectColor(subject: string): string {
  const key = subject.toLowerCase().replace(/\s+/g, '_');
  return SUBJECT_COLORS[key] || '#f3f4f6';
}

const EMPTY_SLOT_FORM: SlotForm = {
  class_id: '',
  academic_year_id: '',
  day_of_week: 1,
  start_time: '08:00',
  end_time: '09:00',
  subject: '',
  teacher_id: '',
  room: '',
};

const EMPTY_EXCEPTION_FORM: ExceptionForm = {
  timetable_slot_id: '',
  exception_date: new Date().toISOString().slice(0, 10),
  exception_type: 'CANCELED',
  substitute_teacher_id: '',
  new_room: '',
  reason: '',
};

export function TimetablePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const role = user?.role || '';
  const isAdmin = role === 'ADM' || role === 'DIR';

  const [selectedClassId, setSelectedClassId] = useState('');
  const [showSlotModal, setShowSlotModal] = useState(false);
  const [slotForm, setSlotForm] = useState<SlotForm>(EMPTY_SLOT_FORM);
  const [editingSlotId, setEditingSlotId] = useState<string | null>(null);
  const [showExceptionModal, setShowExceptionModal] = useState(false);
  const [exceptionForm, setExceptionForm] = useState<ExceptionForm>(EMPTY_EXCEPTION_FORM);
  const classesQuery = useTimetableClasses(isAdmin);
  const weeklyQuery = useWeeklyTimetable(selectedClassId || null, isAdmin);
  const createSlotMutation = useCreateTimetableSlot();
  const updateSlotMutation = useUpdateTimetableSlot();
  const deleteSlotMutation = useDeleteTimetableSlot();
  const createExceptionMutation = useCreateTimetableException();
  const classes: ClassOption[] = classesQuery.data ?? [];
  const slots: TimetableSlot[] = weeklyQuery.data?.slots ?? [];
  const weekStart = weeklyQuery.data?.week_start ?? '';
  const weekEnd = weeklyQuery.data?.week_end ?? '';
  const saving =
    createSlotMutation.isPending ||
    updateSlotMutation.isPending ||
    deleteSlotMutation.isPending ||
    createExceptionMutation.isPending;
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          classesQuery.error ??
            weeklyQuery.error ??
            createSlotMutation.error ??
            updateSlotMutation.error ??
            deleteSlotMutation.error ??
            createExceptionMutation.error,
          t('app.error')
        ),
      [
        classesQuery.error,
        createExceptionMutation.error,
        createSlotMutation.error,
        deleteSlotMutation.error,
        t,
        updateSlotMutation.error,
        weeklyQuery.error,
      ]
    )
  );

  useEffect(() => {
    if (isAdmin && !selectedClassId && classes.length > 0) {
      setSelectedClassId(classes[0].id);
    }
  }, [classes, isAdmin, selectedClassId]);

  const slotsByDay = new Map<number, TimetableSlot[]>();
  DAYS.forEach((d) => slotsByDay.set(d, []));
  slots.forEach((s) => {
    const daySlots = slotsByDay.get(s.day_of_week) || [];
    daySlots.push(s);
    slotsByDay.set(s.day_of_week, daySlots);
  });
  // Sort by start_time
  slotsByDay.forEach((daySlots) => daySlots.sort((a, b) => a.start_time.localeCompare(b.start_time)));

  async function handleSaveSlot() {
    if (editingSlotId) {
      await updateSlotMutation.mutateAsync({
        slotId: editingSlotId,
        payload: {
          day_of_week: slotForm.day_of_week,
          start_time: slotForm.start_time,
          end_time: slotForm.end_time,
          subject: slotForm.subject,
          teacher_id: slotForm.teacher_id || undefined,
          room: slotForm.room || undefined,
        },
      });
    } else {
      await createSlotMutation.mutateAsync({
        class_id: slotForm.class_id || selectedClassId,
        academic_year_id: slotForm.academic_year_id || undefined,
        day_of_week: slotForm.day_of_week,
        start_time: slotForm.start_time,
        end_time: slotForm.end_time,
        subject: slotForm.subject,
        teacher_id: slotForm.teacher_id || undefined,
        room: slotForm.room || undefined,
        is_recurring: true,
      });
    }
    setShowSlotModal(false);
    setSlotForm(EMPTY_SLOT_FORM);
    setEditingSlotId(null);
    await weeklyQuery.refetch();
  }

  async function handleDeleteSlot(slotId: string) {
    if (!confirm(t('timetable.confirmDelete'))) return;
    await deleteSlotMutation.mutateAsync(slotId);
    await weeklyQuery.refetch();
  }

  function openEditSlot(slot: TimetableSlot) {
    setSlotForm({
      class_id: slot.class_id,
      academic_year_id: '',
      day_of_week: slot.day_of_week,
      start_time: slot.start_time,
      end_time: slot.end_time,
      subject: slot.subject,
      teacher_id: slot.teacher_id,
      room: slot.room || '',
    });
    setEditingSlotId(slot.id);
    setShowSlotModal(true);
  }

  function openException(slot: TimetableSlot) {
    setExceptionForm({
      ...EMPTY_EXCEPTION_FORM,
      timetable_slot_id: slot.id,
    });
    setShowExceptionModal(true);
  }

  async function handleSaveException() {
    await createExceptionMutation.mutateAsync({
      timetable_slot_id: exceptionForm.timetable_slot_id,
      exception_date: exceptionForm.exception_date,
      exception_type: exceptionForm.exception_type,
      substitute_teacher_id: exceptionForm.substitute_teacher_id || undefined,
      new_room: exceptionForm.new_room || undefined,
      reason: exceptionForm.reason || undefined,
    });
    setShowExceptionModal(false);
    setExceptionForm(EMPTY_EXCEPTION_FORM);
    await weeklyQuery.refetch();
  }

  if ((isAdmin && classesQuery.isLoading) || weeklyQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('timetable.title')}</h1>
        {isAdmin && (
          <button
            className="btn btn-primary"
            onClick={() => {
              setSlotForm({ ...EMPTY_SLOT_FORM, class_id: selectedClassId });
              setEditingSlotId(null);
              setShowSlotModal(true);
            }}
          >
            + {t('timetable.addSlot')}
          </button>
        )}
      </div>

      {weekStart && weekEnd && (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginBottom: 16 }}>
          {t('timetable.weekOf')} {weekStart} — {weekEnd}
        </p>
      )}

      {isAdmin && classes.length > 0 && (
        <div className="filters-bar">
          <select
            className="filter-select"
            value={selectedClassId}
            onChange={(e) => setSelectedClassId(e.target.value)}
          >
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
            ))}
          </select>
        </div>
      )}

      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} onRetry={() => void weeklyQuery.refetch()} />

      {slots.length === 0 ? (
        <EmptyState message={t('timetable.empty')} icon="📅" />
      ) : (
        <div className="timetable-grid">
          {DAYS.map((day) => {
            const daySlots = slotsByDay.get(day) || [];
            return (
              <div key={day} className="timetable-day">
                <div className="timetable-day-header">
                  {t(`timetable.days.${day}`)}
                </div>
                <div className="timetable-day-slots">
                  {daySlots.length === 0 ? (
                    <div className="timetable-empty-day">—</div>
                  ) : (
                    daySlots.map((slot) => {
                      const isCanceled = slot.exception?.exception_type === 'CANCELED';
                      const isSubstituted = slot.exception?.exception_type === 'SUBSTITUTED';
                      return (
                        <div
                          key={slot.id}
                          className={`timetable-slot-card ${isCanceled ? 'timetable-slot--canceled' : ''}`}
                          style={{ background: isCanceled ? '#fee2e2' : getSubjectColor(slot.subject) }}
                        >
                          <div className="timetable-slot-time">
                            {slot.start_time.slice(0, 5)} – {slot.end_time.slice(0, 5)}
                          </div>
                          <div className="timetable-slot-subject">
                            {t(`cms.subjects.${slot.subject.toLowerCase().replace(/\s+/g, '_')}`, slot.subject)}
                          </div>
                          {slot.room && (
                            <div className="timetable-slot-room">🏫 {slot.room}</div>
                          )}
                          {slot.class_name && role === 'TCH' && (
                            <div className="timetable-slot-class">{slot.class_name}</div>
                          )}
                          {isCanceled && (
                            <span className="timetable-exception-badge timetable-exception--canceled">
                              {t('timetable.canceled')}
                            </span>
                          )}
                          {isSubstituted && (
                            <span className="timetable-exception-badge timetable-exception--substituted">
                              {t('timetable.substituted')}
                            </span>
                          )}
                          {slot.exception?.exception_type === 'ROOM_CHANGED' && slot.exception.new_room && (
                            <span className="timetable-exception-badge timetable-exception--room">
                              → {slot.exception.new_room}
                            </span>
                          )}
                          {isAdmin && (
                            <div className="timetable-slot-actions">
                              <button className="btn btn-sm btn-secondary" onClick={() => openEditSlot(slot)}>
                                ✏️
                              </button>
                              <button className="btn btn-sm btn-secondary" onClick={() => openException(slot)}>
                                ⚠️
                              </button>
                              <button className="btn btn-sm btn-danger" onClick={() => handleDeleteSlot(slot.id)}>
                                🗑️
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Slot Create/Edit Modal */}
      {showSlotModal && (
        <div className="modal-overlay" onClick={() => setShowSlotModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>
              {editingSlotId ? t('timetable.editSlot') : t('timetable.addSlot')}
            </h2>
            <div className="form-field">
              <label>{t('timetable.day')}</label>
              <select
                className="filter-select"
                value={slotForm.day_of_week}
                onChange={(e) => setSlotForm({ ...slotForm, day_of_week: Number(e.target.value) })}
              >
                {DAYS.map((d) => (
                  <option key={d} value={d}>{t(`timetable.days.${d}`)}</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('timetable.startTime')}</label>
                <input
                  type="time"
                  value={slotForm.start_time}
                  onChange={(e) => setSlotForm({ ...slotForm, start_time: e.target.value })}
                />
              </div>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('timetable.endTime')}</label>
                <input
                  type="time"
                  value={slotForm.end_time}
                  onChange={(e) => setSlotForm({ ...slotForm, end_time: e.target.value })}
                />
              </div>
            </div>
            <div className="form-field">
              <label>{t('timetable.subject')}</label>
              <input
                type="text"
                value={slotForm.subject}
                onChange={(e) => setSlotForm({ ...slotForm, subject: e.target.value })}
                placeholder={t('timetable.subjectPlaceholder')}
              />
            </div>
            <div className="form-field">
              <label>{t('timetable.room')}</label>
              <input
                type="text"
                value={slotForm.room}
                onChange={(e) => setSlotForm({ ...slotForm, room: e.target.value })}
                placeholder={t('timetable.roomPlaceholder')}
              />
            </div>
            <div className="form-field">
              <label>{t('timetable.teacherId')}</label>
              <input
                type="text"
                value={slotForm.teacher_id}
                onChange={(e) => setSlotForm({ ...slotForm, teacher_id: e.target.value })}
                placeholder="UUID"
              />
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button className="btn btn-primary" onClick={handleSaveSlot} disabled={saving || !slotForm.subject}>
                {saving ? t('app.loading') : t('app.save')}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowSlotModal(false)}>
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Exception Modal */}
      {showExceptionModal && (
        <div className="modal-overlay" onClick={() => setShowExceptionModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>{t('timetable.createException')}</h2>
            <div className="form-field">
              <label>{t('timetable.exceptionDate')}</label>
              <input
                type="date"
                value={exceptionForm.exception_date}
                onChange={(e) => setExceptionForm({ ...exceptionForm, exception_date: e.target.value })}
              />
            </div>
            <div className="form-field">
              <label>{t('timetable.exceptionType')}</label>
              <select
                className="filter-select"
                value={exceptionForm.exception_type}
                onChange={(e) => setExceptionForm({ ...exceptionForm, exception_type: e.target.value })}
              >
                <option value="CANCELED">{t('timetable.canceled')}</option>
                <option value="SUBSTITUTED">{t('timetable.substituted')}</option>
                <option value="ROOM_CHANGED">{t('timetable.roomChanged')}</option>
              </select>
            </div>
            {exceptionForm.exception_type === 'SUBSTITUTED' && (
              <div className="form-field">
                <label>{t('timetable.substituteTeacher')}</label>
                <input
                  type="text"
                  value={exceptionForm.substitute_teacher_id}
                  onChange={(e) => setExceptionForm({ ...exceptionForm, substitute_teacher_id: e.target.value })}
                  placeholder="UUID"
                />
              </div>
            )}
            {exceptionForm.exception_type === 'ROOM_CHANGED' && (
              <div className="form-field">
                <label>{t('timetable.newRoom')}</label>
                <input
                  type="text"
                  value={exceptionForm.new_room}
                  onChange={(e) => setExceptionForm({ ...exceptionForm, new_room: e.target.value })}
                />
              </div>
            )}
            <div className="form-field">
              <label>{t('timetable.reason')}</label>
              <input
                type="text"
                value={exceptionForm.reason}
                onChange={(e) => setExceptionForm({ ...exceptionForm, reason: e.target.value })}
                placeholder={t('timetable.reasonPlaceholder')}
              />
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button className="btn btn-primary" onClick={handleSaveException} disabled={saving}>
                {saving ? t('app.loading') : t('app.save')}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowExceptionModal(false)}>
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
