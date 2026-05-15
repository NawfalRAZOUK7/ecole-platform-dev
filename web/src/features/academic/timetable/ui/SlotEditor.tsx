import { useTranslation } from 'react-i18next';
import { type SlotEditorProps } from '../model/timetable.types';

export function SlotEditor({
  days,
  exceptionForm,
  isExceptionOpen,
  isSlotOpen,
  isSaving,
  editingSlotId,
  slotForm,
  onChangeExceptionForm,
  onChangeSlotForm,
  onCloseException,
  onCloseSlot,
  onSaveException,
  onSaveSlot,
}: SlotEditorProps) {
  const { t } = useTranslation();

  return (
    <>
      {isSlotOpen && (
        <div className="modal-overlay" onClick={onCloseSlot}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>
              {editingSlotId ? t('timetable.editSlot') : t('timetable.addSlot')}
            </h2>
            <div className="form-field">
              <label>{t('timetable.day')}</label>
              <select
                className="filter-select"
                aria-label={t('timetable.day')}
                value={slotForm.day_of_week}
                onChange={(event) =>
                  onChangeSlotForm({ ...slotForm, day_of_week: Number(event.target.value) })
                }
              >
                {days.map((day) => (
                  <option key={day} value={day}>
                    {t(`timetable.days.${day}`)}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <label className="form-field" style={{ flex: 1 }}>
                <span>{t('timetable.startTime')}</span>
                <input
                  aria-label={t('timetable.startTime')}
                  type="time"
                  value={slotForm.start_time}
                  onChange={(event) =>
                    onChangeSlotForm({ ...slotForm, start_time: event.target.value })
                  }
                />
              </label>
              <label className="form-field" style={{ flex: 1 }}>
                <span>{t('timetable.endTime')}</span>
                <input
                  aria-label={t('timetable.endTime')}
                  type="time"
                  value={slotForm.end_time}
                  onChange={(event) =>
                    onChangeSlotForm({ ...slotForm, end_time: event.target.value })
                  }
                />
              </label>
            </div>
            <label className="form-field">
              <span>{t('timetable.subject')}</span>
              <input
                aria-label={t('timetable.subject')}
                type="text"
                value={slotForm.subject}
                onChange={(event) => onChangeSlotForm({ ...slotForm, subject: event.target.value })}
                placeholder={t('timetable.subjectPlaceholder')}
              />
            </label>
            <label className="form-field">
              <span>{t('timetable.room')}</span>
              <input
                aria-label={t('timetable.room')}
                type="text"
                value={slotForm.room}
                onChange={(event) => onChangeSlotForm({ ...slotForm, room: event.target.value })}
                placeholder={t('timetable.roomPlaceholder')}
              />
            </label>
            <label className="form-field">
              <span>{t('timetable.teacherId')}</span>
              <input
                aria-label={t('timetable.teacherId')}
                type="text"
                value={slotForm.teacher_id}
                onChange={(event) =>
                  onChangeSlotForm({ ...slotForm, teacher_id: event.target.value })
                }
                placeholder="UUID"
              />
            </label>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                className="btn btn-primary"
                onClick={onSaveSlot}
                disabled={isSaving || !slotForm.subject}
              >
                {isSaving ? t('app.loading') : t('app.save')}
              </button>
              <button className="btn btn-secondary" onClick={onCloseSlot}>
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {isExceptionOpen && (
        <div className="modal-overlay" onClick={onCloseException}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>{t('timetable.createException')}</h2>
            <label className="form-field">
              <span>{t('timetable.exceptionDate')}</span>
              <input
                aria-label={t('timetable.exceptionDate')}
                type="date"
                value={exceptionForm.exception_date}
                onChange={(event) =>
                  onChangeExceptionForm({ ...exceptionForm, exception_date: event.target.value })
                }
              />
            </label>
            <label className="form-field">
              <span>{t('timetable.exceptionType')}</span>
              <select
                className="filter-select"
                aria-label={t('timetable.exceptionType')}
                value={exceptionForm.exception_type}
                onChange={(event) =>
                  onChangeExceptionForm({ ...exceptionForm, exception_type: event.target.value })
                }
              >
                <option value="CANCELED">{t('timetable.canceled')}</option>
                <option value="SUBSTITUTED">{t('timetable.substituted')}</option>
                <option value="ROOM_CHANGED">{t('timetable.roomChanged')}</option>
              </select>
            </label>
            {exceptionForm.exception_type === 'SUBSTITUTED' && (
              <label className="form-field">
                <span>{t('timetable.substituteTeacher')}</span>
                <input
                  aria-label={t('timetable.substituteTeacher')}
                  type="text"
                  value={exceptionForm.substitute_teacher_id}
                  onChange={(event) =>
                    onChangeExceptionForm({
                      ...exceptionForm,
                      substitute_teacher_id: event.target.value,
                    })
                  }
                  placeholder="UUID"
                />
              </label>
            )}
            {exceptionForm.exception_type === 'ROOM_CHANGED' && (
              <label className="form-field">
                <span>{t('timetable.newRoom')}</span>
                <input
                  aria-label={t('timetable.newRoom')}
                  type="text"
                  value={exceptionForm.new_room}
                  onChange={(event) =>
                    onChangeExceptionForm({ ...exceptionForm, new_room: event.target.value })
                  }
                />
              </label>
            )}
            <label className="form-field">
              <span>{t('timetable.reason')}</span>
              <input
                aria-label={t('timetable.reason')}
                type="text"
                value={exceptionForm.reason}
                onChange={(event) =>
                  onChangeExceptionForm({ ...exceptionForm, reason: event.target.value })
                }
                placeholder={t('timetable.reasonPlaceholder')}
              />
            </label>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button className="btn btn-primary" onClick={onSaveException} disabled={isSaving}>
                {isSaving ? t('app.loading') : t('app.save')}
              </button>
              <button className="btn btn-secondary" onClick={onCloseException}>
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
