import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiClientError, type ApiError } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import {
  useCalendarEvent,
  useCalendarEventRsvp,
  useCalendarEvents,
  useCalendarOptions,
  useCreateCalendarEvent,
  useDeleteCalendarEvent,
  useUpdateCalendarEvent,
} from './useCalendar';
import { EventDetailView, EventEditorModal, eventTitle, eventTypeColor } from './shared';
import type {
  CalendarEventItem,
  CalendarOptionsPayload,
  CalendarView,
  EventRsvpStatus,
  EventType,
} from './types';

const EVENT_TYPES: EventType[] = ['holiday', 'exam', 'meeting', 'excursion', 'ceremony', 'custom'];

function toBannerError(error: unknown, fallback: string): ApiError | string | null {
  if (!error) {
    return null;
  }
  if (error instanceof ApiClientError) {
    return error.apiError;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

function cloneDate(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate());
}

function dayKey(value: Date) {
  return value.toISOString().slice(0, 10);
}

function addDays(value: Date, days: number) {
  const next = new Date(value);
  next.setDate(next.getDate() + days);
  return next;
}

function startOfWeek(value: Date) {
  const next = cloneDate(value);
  const delta = (next.getDay() + 6) % 7;
  next.setDate(next.getDate() - delta);
  return next;
}

function monthRange(value: Date) {
  const first = new Date(value.getFullYear(), value.getMonth(), 1);
  const last = new Date(value.getFullYear(), value.getMonth() + 1, 0);
  return {
    from: startOfWeek(first),
    to: addDays(startOfWeek(last), 6),
  };
}

function rangeForView(view: CalendarView, anchor: Date) {
  if (view === 'week') {
    const from = startOfWeek(anchor);
    return { from, to: addDays(from, 6) };
  }
  return monthRange(anchor);
}

function occursOnDay(event: CalendarEventItem, day: Date) {
  const dayStart = new Date(day);
  dayStart.setHours(0, 0, 0, 0);
  const dayEnd = new Date(day);
  dayEnd.setHours(23, 59, 59, 999);
  const start = new Date(event.start_at);
  const end = new Date(event.end_at);
  return start <= dayEnd && end >= dayStart;
}

function shiftAnchorDate(view: CalendarView, current: Date, direction: -1 | 1) {
  const next = new Date(current);
  if (view === 'week') {
    next.setDate(next.getDate() + direction * 7);
  } else {
    next.setMonth(next.getMonth() + direction);
  }
  return next;
}

export function CalendarPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [view, setView] = useState<CalendarView>('month');
  const [anchorDate, setAnchorDate] = useState(() => new Date());
  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const [selectedTypes, setSelectedTypes] = useState<EventType[]>(EVENT_TYPES);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [detailSeedEvent, setDetailSeedEvent] = useState<CalendarEventItem | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorEvent, setEditorEvent] = useState<CalendarEventItem | null>(null);
  const [copyState, setCopyState] = useState<string | null>(null);
  const [dismissedError, setDismissedError] = useState(false);

  const range = useMemo(() => rangeForView(view, anchorDate), [anchorDate, view]);
  const canCreate = ['ADM', 'DIR', 'TCH'].includes(user?.role || '');
  const calendarFilters = useMemo(
    () => ({
      from: dayKey(range.from),
      to: dayKey(range.to),
      class_id: selectedClassId || undefined,
    }),
    [range.from, range.to, selectedClassId]
  );

  const eventsQuery = useCalendarEvents(calendarFilters);
  const optionsQuery = useCalendarOptions();
  const createEventMutation = useCreateCalendarEvent();
  const updateEventMutation = useUpdateCalendarEvent();
  const deleteEventMutation = useDeleteCalendarEvent();
  const rsvpMutation = useCalendarEventRsvp();

  const items = useMemo(
    () => eventsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [eventsQuery.data]
  );
  const options: CalendarOptionsPayload = optionsQuery.data ?? {
    classes: [],
    ical_url: '',
    reminder_preferences: [],
  };
  const detailEventId = detailSeedEvent?.source === 'event' ? detailSeedEvent.id : null;
  const detailQuery = useCalendarEvent(detailEventId, { enabled: Boolean(detailEventId) });
  const detailEvent = useMemo<CalendarEventItem | null>(() => {
    if (!detailSeedEvent) {
      return null;
    }
    if (detailSeedEvent.source !== 'event') {
      return detailSeedEvent;
    }
    return detailQuery.data ?? detailSeedEvent;
  }, [detailQuery.data, detailSeedEvent]);
  const detailLoading = Boolean(detailSeedEvent?.source === 'event' && detailQuery.isLoading && !detailQuery.data);

  const filteredItems = useMemo(
    () => items.filter((item) => selectedTypes.includes(item.type)),
    [items, selectedTypes]
  );
  const selectedDayItems = useMemo(
    () => filteredItems.filter((item) => occursOnDay(item, selectedDate)),
    [filteredItems, selectedDate]
  );
  const monthDays = useMemo(() => {
    const days: Date[] = [];
    let cursor = cloneDate(range.from);
    while (cursor <= range.to) {
      days.push(cursor);
      cursor = addDays(cursor, 1);
    }
    return days;
  }, [range.from, range.to]);
  const weekDays = useMemo(() => {
    const from = startOfWeek(anchorDate);
    return Array.from({ length: 7 }, (_, index) => addDays(from, index));
  }, [anchorDate]);
  const bannerError = useMemo(
    () =>
      toBannerError(
        eventsQuery.error ??
          optionsQuery.error ??
          detailQuery.error ??
          createEventMutation.error ??
          updateEventMutation.error ??
          deleteEventMutation.error ??
          rsvpMutation.error,
        t('app.error')
      ),
    [
      createEventMutation.error,
      deleteEventMutation.error,
      detailQuery.error,
      eventsQuery.error,
      optionsQuery.error,
      rsvpMutation.error,
      t,
      updateEventMutation.error,
    ]
  );

  useEffect(() => {
    setDismissedError(false);
  }, [bannerError]);

  async function openDetails(item: CalendarEventItem) {
    setDetailSeedEvent(item);
  }

  async function handleSaveEvent(payload: Record<string, unknown>) {
    if (editorEvent) {
      const updatedEvent = await updateEventMutation.mutateAsync({ id: editorEvent.id, payload });
      if (detailSeedEvent?.id === updatedEvent.id) {
        setDetailSeedEvent(updatedEvent);
      }
    } else {
      await createEventMutation.mutateAsync(payload);
    }
    setEditorOpen(false);
    setEditorEvent(null);
  }

  async function handleDeleteEvent() {
    if (!detailEvent || detailEvent.source !== 'event') {
      return;
    }
    if (!window.confirm(t('calendar.confirmDelete'))) {
      return;
    }
    await deleteEventMutation.mutateAsync(detailEvent.id);
    setDetailSeedEvent(null);
  }

  async function handleRsvp(status: EventRsvpStatus) {
    if (!detailEvent || detailEvent.source !== 'event') {
      return;
    }
    await rsvpMutation.mutateAsync({ id: detailEvent.id, status });
  }

  async function handleCopyIcal() {
    if (!options.ical_url) {
      return;
    }
    await navigator.clipboard.writeText(options.ical_url);
    setCopyState(t('calendar.copied'));
    window.setTimeout(() => setCopyState(null), 2000);
  }

  function toggleType(type: EventType) {
    setSelectedTypes((current) =>
      current.includes(type) ? current.filter((item) => item !== type) : [...current, type]
    );
  }

  if ((eventsQuery.isLoading && items.length === 0) || (optionsQuery.isLoading && !optionsQuery.data)) {
    return <LoadingState />;
  }

  return (
    <div className="page calendar-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('calendar.title')}</h1>
          <p className="page-subtitle">{t('calendar.subtitle')}</p>
        </div>
        <div className="page-actions">
          <div className="calendar-view-toggle">
            {(['month', 'week', 'agenda'] as CalendarView[]).map((item) => (
              <button
                key={item}
                type="button"
                className={`btn ${view === item ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setView(item)}
              >
                {t(`calendar.views.${item}`)}
              </button>
            ))}
          </div>
          {canCreate && (
            <button
              className="btn btn-primary"
              type="button"
              onClick={() => {
                setEditorEvent(null);
                setEditorOpen(true);
              }}
            >
              {t('calendar.createEvent')}
            </button>
          )}
        </div>
      </div>

      <ErrorBanner
        error={dismissedError ? null : bannerError}
        onDismiss={() => setDismissedError(true)}
        onRetry={() => void Promise.all([
          eventsQuery.refetch(),
          optionsQuery.refetch(),
          detailEventId ? detailQuery.refetch() : Promise.resolve(null),
        ])}
      />

      <div className="calendar-layout">
        <aside className="calendar-sidebar card">
          <h2>{t('calendar.filters.title')}</h2>
          <label className="form-field">
            <span>{t('calendar.form.class')}</span>
            <select value={selectedClassId} onChange={(event) => setSelectedClassId(event.target.value)}>
              <option value="">{t('calendar.filters.allClasses')}</option>
              {options.classes.map((item) => (
                <option key={item.id} value={item.id}>
                  {[item.code, item.name].filter(Boolean).join(' · ')}
                </option>
              ))}
            </select>
          </label>

          <div className="calendar-filter-list">
            {EVENT_TYPES.map((type) => (
              <label key={type} className="form-checkbox">
                <input
                  type="checkbox"
                  checked={selectedTypes.includes(type)}
                  onChange={() => toggleType(type)}
                />
                <span>{t(`calendar.types.${type}`)}</span>
              </label>
            ))}
          </div>

          <div className="calendar-sidebar__section">
            <h3>{t('calendar.subscribeTitle')}</h3>
            <p>{t('calendar.subscribeHint')}</p>
            <div className="calendar-subscribe-box">
              <input readOnly value={options.ical_url} />
              <button className="btn btn-secondary" type="button" onClick={() => void handleCopyIcal()}>
                {t('calendar.copyIcal')}
              </button>
            </div>
            {copyState && <span className="calendar-copy-state">{copyState}</span>}
          </div>

          <div className="calendar-sidebar__section">
            <h3>{t('calendar.selectedDay')}</h3>
            <p>{selectedDate.toLocaleDateString(i18n.language, { dateStyle: 'full' })}</p>
            {selectedDayItems.length === 0 ? (
              <EmptyState message={t('calendar.noEvents')} icon="📅" />
            ) : (
              <div className="calendar-day-list">
                {selectedDayItems.map((item) => (
                  <button
                    key={item.instance_id}
                    type="button"
                    className={`calendar-day-list__item ${eventTypeColor(item.type)}`}
                    onClick={() => void openDetails(item)}
                  >
                    <strong>{eventTitle(item, i18n.language)}</strong>
                    <span>
                      {new Date(item.start_at).toLocaleTimeString(i18n.language, {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </aside>

        <section className="calendar-board card">
          <div className="calendar-board__toolbar">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setAnchorDate((current) => shiftAnchorDate(view, current, -1))}
            >
              {t('calendar.previous')}
            </button>
            <h2>
              {anchorDate.toLocaleDateString(i18n.language, {
                month: 'long',
                year: 'numeric',
              })}
            </h2>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setAnchorDate((current) => shiftAnchorDate(view, current, 1))}
            >
              {t('calendar.next')}
            </button>
          </div>

          {view === 'month' && (
            <div className="calendar-month-grid">
              {monthDays.map((day) => {
                const dayItems = filteredItems.filter((item) => occursOnDay(item, day));
                const isCurrentMonth = day.getMonth() === anchorDate.getMonth();
                const isSelected = dayKey(day) === dayKey(selectedDate);
                return (
                  <button
                    key={dayKey(day)}
                    type="button"
                    className={`calendar-day-cell ${!isCurrentMonth ? 'calendar-day-cell--muted' : ''} ${isSelected ? 'calendar-day-cell--selected' : ''}`}
                    onClick={() => setSelectedDate(day)}
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
                            void openDetails(item);
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
                      onClick={() => setSelectedDate(day)}
                    >
                      <strong>{day.toLocaleDateString(i18n.language, { weekday: 'short' })}</strong>
                      <span>{day.toLocaleDateString(i18n.language, { day: 'numeric', month: 'short' })}</span>
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
                            onClick={() => void openDetails(item)}
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
                    onClick={() => void openDetails(item)}
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
      </div>

      {detailEvent && (
        <div className="modal-overlay" onClick={() => setDetailSeedEvent(null)}>
          <div className="modal-card calendar-modal-card" onClick={(event) => event.stopPropagation()}>
            {detailLoading ? (
              <LoadingState />
            ) : (
              <EventDetailView
                event={detailEvent}
                onClose={() => setDetailSeedEvent(null)}
                onRsvp={(status) => void handleRsvp(status)}
                onEdit={() => {
                  setEditorEvent(detailEvent);
                  setEditorOpen(true);
                }}
                onDelete={() => void handleDeleteEvent()}
                showOpenPageLink={detailEvent.source === 'event'}
              />
            )}
          </div>
        </div>
      )}

      <EventEditorModal
        isOpen={editorOpen}
        initialEvent={editorEvent}
        userRole={user?.role || 'STD'}
        availableClasses={options.classes}
        onClose={() => {
          setEditorOpen(false);
          setEditorEvent(null);
        }}
        onSubmit={handleSaveEvent}
      />
    </div>
  );
}
