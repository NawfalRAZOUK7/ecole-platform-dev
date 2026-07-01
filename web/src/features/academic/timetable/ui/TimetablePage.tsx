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
import { useAuth } from '@/app/providers/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useCreateTimetableException,
  useCreateTimetableSlot,
  useDeleteTimetableSlot,
  useTimetableClasses,
  useUpdateTimetableSlot,
  useWeeklyTimetable,
} from '../model/useTimetable';
import type { ClassOption, ExceptionForm, SlotForm, TimetableSlot } from '../api/timetable.api';
import { TimetableFilters } from './TimetableFilters';
import { TimetableGrid } from './TimetableGrid';
import { SlotEditor } from './SlotEditor';
import { DAYS, EMPTY_EXCEPTION_FORM, EMPTY_SLOT_FORM } from '../model/timetable.types';
import { EmptyState } from '@/shared/ui/EmptyState';

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
          t('app.error'),
        ),
      [
        classesQuery.error,
        createExceptionMutation.error,
        createSlotMutation.error,
        deleteSlotMutation.error,
        t,
        updateSlotMutation.error,
        weeklyQuery.error,
      ],
    ),
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
  slotsByDay.forEach((daySlots) =>
    daySlots.sort((a, b) => a.start_time.localeCompare(b.start_time)),
  );

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
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <h1 className="page-title" style={{ marginBottom: 0 }}>
          {t('timetable.title')}
        </h1>
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

      <TimetableFilters
        classes={classes}
        isAdmin={isAdmin}
        selectedClassId={selectedClassId}
        weekStart={weekStart}
        weekEnd={weekEnd}
        onChangeClass={setSelectedClassId}
      />

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void weeklyQuery.refetch()}
      />

      {slots.length === 0 ? (
        <EmptyState message={t('timetable.empty')} icon="📅" />
      ) : (
        <TimetableGrid
          days={DAYS}
          isAdmin={isAdmin}
          role={role}
          slotsByDay={slotsByDay}
          onDelete={(slotId) => void handleDeleteSlot(slotId)}
          onEdit={openEditSlot}
          onException={openException}
        />
      )}

      <SlotEditor
        days={DAYS}
        exceptionForm={exceptionForm}
        isExceptionOpen={showExceptionModal}
        isSlotOpen={showSlotModal}
        isSaving={saving}
        editingSlotId={editingSlotId}
        slotForm={slotForm}
        onChangeExceptionForm={setExceptionForm}
        onChangeSlotForm={setSlotForm}
        onCloseException={() => setShowExceptionModal(false)}
        onCloseSlot={() => setShowSlotModal(false)}
        onSaveException={() => void handleSaveException()}
        onSaveSlot={() => void handleSaveSlot()}
      />
    </div>
  );
}
