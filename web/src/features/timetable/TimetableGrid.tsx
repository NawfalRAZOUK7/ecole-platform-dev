import { useTranslation } from 'react-i18next';
import type { TimetableSlot } from './timetable.service';
import { getSubjectColor, type TimetableGridProps } from './timetable.types';

export function TimetableGrid({
  days,
  isAdmin,
  role,
  slotsByDay,
  onDelete,
  onEdit,
  onException,
}: TimetableGridProps) {
  const { t } = useTranslation();

  return (
    <div className="timetable-grid">
      {days.map((day) => {
        const daySlots = slotsByDay.get(day) || [];

        return (
          <div key={day} className="timetable-day">
            <div className="timetable-day-header">{t(`timetable.days.${day}`)}</div>
            <div className="timetable-day-slots">
              {daySlots.length === 0 ? (
                <div className="timetable-empty-day">—</div>
              ) : (
                daySlots.map((slot) => (
                  <TimetableSlotCard
                    key={slot.id}
                    isAdmin={isAdmin}
                    role={role}
                    slot={slot}
                    onDelete={onDelete}
                    onEdit={onEdit}
                    onException={onException}
                  />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface TimetableSlotCardProps {
  isAdmin: boolean;
  role: string;
  slot: TimetableSlot;
  onDelete: (slotId: string) => void;
  onEdit: (slot: TimetableSlot) => void;
  onException: (slot: TimetableSlot) => void;
}

function TimetableSlotCard({
  isAdmin,
  role,
  slot,
  onDelete,
  onEdit,
  onException,
}: TimetableSlotCardProps) {
  const { t } = useTranslation();
  const isCanceled = slot.exception?.exception_type === 'CANCELED';
  const isSubstituted = slot.exception?.exception_type === 'SUBSTITUTED';

  return (
    <div
      className={`timetable-slot-card ${isCanceled ? 'timetable-slot--canceled' : ''}`}
      style={{ background: isCanceled ? 'var(--color-surface-error)' : getSubjectColor(slot.subject) }}
    >
      <div className="timetable-slot-time">
        {slot.start_time.slice(0, 5)} – {slot.end_time.slice(0, 5)}
      </div>
      <div className="timetable-slot-subject">
        {t(`cms.subjects.${slot.subject.toLowerCase().replace(/\s+/g, '_')}`, slot.subject)}
      </div>
      {slot.room && <div className="timetable-slot-room">🏫 {slot.room}</div>}
      {slot.class_name && role === 'TCH' && <div className="timetable-slot-class">{slot.class_name}</div>}
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
        <span className="timetable-exception-badge timetable-exception--room">→ {slot.exception.new_room}</span>
      )}
      {isAdmin && (
        <div className="timetable-slot-actions">
          <button className="btn btn-sm btn-secondary" onClick={() => onEdit(slot)}>
            ✏️
          </button>
          <button className="btn btn-sm btn-secondary" onClick={() => onException(slot)}>
            ⚠️
          </button>
          <button className="btn btn-sm btn-danger" onClick={() => onDelete(slot.id)}>
            🗑️
          </button>
        </div>
      )}
    </div>
  );
}
