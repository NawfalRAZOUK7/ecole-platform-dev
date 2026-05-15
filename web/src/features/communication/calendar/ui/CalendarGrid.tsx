import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import type { CalendarGridProps } from '../model/calendar.types';
import {
  addDays,
  dayKey,
  eventTitle,
  eventTypeColor,
  occursOnDay,
  startOfWeek,
} from '../calendar.utils';

export function CalendarGrid({
  anchorDate,
  filteredItems,
  selectedDate,
  view,
  onChangeAnchorDate,
  onOpenDetails,
  onSelectDate,
}: CalendarGridProps) {
  const { t, i18n } = useTranslation();
  const monthDays = useMemo(() => {
    const first = startOfWeek(new Date(anchorDate.getFullYear(), anchorDate.getMonth(), 1));
    const last = addDays(
      startOfWeek(new Date(anchorDate.getFullYear(), anchorDate.getMonth() + 1, 0)),
      6,
    );
    const days: Date[] = [];
    let cursor = new Date(first);
    while (cursor <= last) {
      days.push(new Date(cursor));
      cursor = addDays(cursor, 1);
    }
    return days;
  }, [anchorDate]);
  const weekDays = useMemo(
    () => Array.from({ length: 7 }, (_, index) => addDays(startOfWeek(anchorDate), index)),
    [anchorDate],
  );

  return (
    <section className="calendar-board card">
      <div className="calendar-board__toolbar">
        <button type="button" className="btn btn-secondary" onClick={() => onChangeAnchorDate(-1)}>
          {t('calendar.previous')}
        </button>
        <h2>{anchorDate.toLocaleDateString(i18n.language, { month: 'long', year: 'numeric' })}</h2>
        <button type="button" className="btn btn-secondary" onClick={() => onChangeAnchorDate(1)}>
          {t('calendar.next')}
        </button>
      </div>

      {view === 'month' && (
        <div className="calendar-month-grid">
          {monthDays.map((day) => {
            const dayItems = filteredItems.filter((item) => occursOnDay(item, day));
            return (
              <button
                key={dayKey(day)}
                type="button"
                className={`calendar-day-cell ${day.getMonth() !== anchorDate.getMonth() ? 'calendar-day-cell--muted' : ''} ${dayKey(day) === dayKey(selectedDate) ? 'calendar-day-cell--selected' : ''}`}
                onClick={() => onSelectDate(day)}
              >
                <span className="calendar-day-cell__number">{day.getDate()}</span>
                <div className="calendar-day-cell__dots">
                  {dayItems.slice(0, 3).map((item) => (
                    <span
                      key={item.instance_id}
                      className={`calendar-event-dot ${eventTypeColor(item.type)}`}
                      title={eventTitle(item, i18n.language)}
                      onClick={(event) => {
                        event.stopPropagation();
                        onOpenDetails(item);
                      }}
                    />
                  ))}
                </div>
                <span className="calendar-day-cell__count">
                  {dayItems.length > 0 ? t('calendar.eventCount', { count: dayItems.length }) : ''}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {view === 'week' && (
        <div className="calendar-week-grid">
          {weekDays.map((day) => {
            const dayItems = filteredItems.filter((item) => occursOnDay(item, day));
            return (
              <div key={dayKey(day)} className="calendar-week-column">
                <button
                  type="button"
                  className="calendar-week-column__header"
                  onClick={() => onSelectDate(day)}
                >
                  <strong>{day.toLocaleDateString(i18n.language, { weekday: 'short' })}</strong>
                  <span>
                    {day.toLocaleDateString(i18n.language, { day: 'numeric', month: 'short' })}
                  </span>
                </button>
                <div className="calendar-week-column__items">
                  {dayItems.length === 0 ? (
                    <span className="calendar-week-column__empty">{t('calendar.noEvents')}</span>
                  ) : (
                    dayItems.map((item) => (
                      <button
                        key={item.instance_id}
                        type="button"
                        className={`calendar-event-chip ${eventTypeColor(item.type)}`}
                        onClick={() => onOpenDetails(item)}
                      >
                        <strong>{eventTitle(item, i18n.language)}</strong>
                        <span>
                          {item.is_all_day
                            ? t('calendar.allDay')
                            : new Date(item.start_at).toLocaleTimeString(i18n.language, {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {view === 'agenda' && (
        <div className="calendar-agenda">
          {filteredItems.length === 0 ? (
            <EmptyState message={t('calendar.noEvents')} icon="🗓️" />
          ) : (
            filteredItems.map((item) => (
              <button
                key={item.instance_id}
                type="button"
                className="calendar-agenda__item"
                onClick={() => onOpenDetails(item)}
              >
                <span className={`calendar-type-pill ${eventTypeColor(item.type)}`}>
                  {t(`calendar.types.${item.type}`)}
                </span>
                <strong>{eventTitle(item, i18n.language)}</strong>
                <span>
                  {new Date(item.start_at).toLocaleDateString(i18n.language, {
                    weekday: 'long',
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </section>
  );
}
