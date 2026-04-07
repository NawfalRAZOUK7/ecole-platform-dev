import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiClientError, type ApiError } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { CalendarFilters } from './CalendarFilters';
import { CalendarGrid } from './CalendarGrid';
import { EventForm } from './EventForm';
import { EventDetail } from './EventDetail';
import { dayKey, EVENT_TYPES, occursOnDay, rangeForView, shiftAnchorDate } from './calendar.utils';
import { useCalendarEvent, useCalendarEventRsvp, useCalendarEvents, useCalendarOptions, useCreateCalendarEvent, useDeleteCalendarEvent, useUpdateCalendarEvent } from './useCalendar';
import type { CalendarEventItem, CalendarOptionsPayload, CalendarView, EventRsvpStatus, EventType } from './types';

function toBannerError(error: unknown, fallback: string): ApiError | string | null {
  if (!error) return null;
  if (error instanceof ApiClientError) return error.apiError;
  if (error instanceof Error) return error.message;
  return fallback;
}

export function CalendarPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [view, setView] = useState<CalendarView>('month');
  const [anchorDate, setAnchorDate] = useState(() => new Date());
  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const [selectedTypes, setSelectedTypes] = useState<EventType[]>([...EVENT_TYPES]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [detailSeedEvent, setDetailSeedEvent] = useState<CalendarEventItem | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorEvent, setEditorEvent] = useState<CalendarEventItem | null>(null);
  const [copyState, setCopyState] = useState<string | null>(null);
  const [dismissedError, setDismissedError] = useState(false);

  const range = useMemo(() => rangeForView(view, anchorDate), [anchorDate, view]);
  const canCreate = ['ADM', 'DIR', 'TCH'].includes(user?.role || '');
  const eventsQuery = useCalendarEvents({ from: dayKey(range.from), to: dayKey(range.to), class_id: selectedClassId || undefined });
  const optionsQuery = useCalendarOptions();
  const createEventMutation = useCreateCalendarEvent();
  const updateEventMutation = useUpdateCalendarEvent();
  const deleteEventMutation = useDeleteCalendarEvent();
  const rsvpMutation = useCalendarEventRsvp();
  const items = useMemo(() => eventsQuery.data?.pages.flatMap((page) => page.data) ?? [], [eventsQuery.data]);
  const options: CalendarOptionsPayload = optionsQuery.data ?? { classes: [], ical_url: '', reminder_preferences: [] };
  const detailEventId = detailSeedEvent?.source === 'event' ? detailSeedEvent.id : null;
  const detailQuery = useCalendarEvent(detailEventId, { enabled: Boolean(detailEventId) });
  const detailEvent = useMemo<CalendarEventItem | null>(() => (!detailSeedEvent ? null : detailSeedEvent.source !== 'event' ? detailSeedEvent : detailQuery.data ?? detailSeedEvent), [detailQuery.data, detailSeedEvent]);
  const filteredItems = useMemo(() => items.filter((item) => selectedTypes.includes(item.type)), [items, selectedTypes]);
  const selectedDayItems = useMemo(() => filteredItems.filter((item) => occursOnDay(item, selectedDate)), [filteredItems, selectedDate]);
  const bannerError = useMemo(() => toBannerError(eventsQuery.error ?? optionsQuery.error ?? detailQuery.error ?? createEventMutation.error ?? updateEventMutation.error ?? deleteEventMutation.error ?? rsvpMutation.error, t('app.error')), [createEventMutation.error, deleteEventMutation.error, detailQuery.error, eventsQuery.error, optionsQuery.error, rsvpMutation.error, t, updateEventMutation.error]);

  useEffect(() => { setDismissedError(false); }, [bannerError]);

  async function handleSaveEvent(payload: Record<string, unknown>) {
    if (editorEvent) {
      const updatedEvent = await updateEventMutation.mutateAsync({ id: editorEvent.id, payload });
      if (detailSeedEvent?.id === updatedEvent.id) setDetailSeedEvent(updatedEvent);
    } else {
      await createEventMutation.mutateAsync(payload);
    }
    setEditorOpen(false);
    setEditorEvent(null);
  }

  async function handleDeleteEvent() {
    if (!detailEvent || detailEvent.source !== 'event') return;
    if (!window.confirm(t('calendar.confirmDelete'))) return;
    await deleteEventMutation.mutateAsync(detailEvent.id);
    setDetailSeedEvent(null);
  }

  async function handleRsvp(status: EventRsvpStatus) {
    if (!detailEvent || detailEvent.source !== 'event') return;
    await rsvpMutation.mutateAsync({ id: detailEvent.id, status });
  }

  async function handleCopyIcal() {
    if (!options.ical_url) return;
    await navigator.clipboard.writeText(options.ical_url);
    setCopyState(t('calendar.copied'));
    window.setTimeout(() => setCopyState(null), 2000);
  }

  if ((eventsQuery.isLoading && items.length === 0) || (optionsQuery.isLoading && !optionsQuery.data)) return <LoadingState />;

  return (
    <div className="page calendar-page">
      <div className="page-header page-header--split">
        <div><h1 className="page-title">{t('calendar.title')}</h1><p className="page-subtitle">{t('calendar.subtitle')}</p></div>
        <div className="page-actions">
          <div className="calendar-view-toggle">
            {(['month', 'week', 'agenda'] as CalendarView[]).map((item) => <button key={item} type="button" className={`btn ${view === item ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setView(item)}>{t(`calendar.views.${item}`)}</button>)}
          </div>
          {options.ical_url && (
            <a
              href={options.ical_url}
              download="calendar.ics"
              className="btn btn-secondary"
            >
              {t('calendar.exportIcal')}
            </a>
          )}
          {canCreate && <button className="btn btn-primary" type="button" onClick={() => { setEditorEvent(null); setEditorOpen(true); }}>{t('calendar.createEvent')}</button>}
        </div>
      </div>

      <ErrorBanner error={dismissedError ? null : bannerError} onDismiss={() => setDismissedError(true)} onRetry={() => void Promise.all([eventsQuery.refetch(), optionsQuery.refetch(), detailEventId ? detailQuery.refetch() : Promise.resolve(null)])} />

      <div className="calendar-layout">
        <CalendarFilters
          availableClasses={options.classes}
          copyState={copyState}
          icalUrl={options.ical_url}
          selectedClassId={selectedClassId}
          selectedDate={selectedDate}
          selectedDayItems={selectedDayItems}
          selectedTypes={selectedTypes}
          onChangeClassId={setSelectedClassId}
          onCopyIcal={() => void handleCopyIcal()}
          onOpenDetails={setDetailSeedEvent}
          onToggleType={(type) => setSelectedTypes((current) => current.includes(type) ? current.filter((item) => item !== type) : [...current, type])}
        />
        <CalendarGrid
          anchorDate={anchorDate}
          filteredItems={filteredItems}
          selectedDate={selectedDate}
          view={view}
          onChangeAnchorDate={(direction) => setAnchorDate((current) => shiftAnchorDate(view, current, direction))}
          onOpenDetails={setDetailSeedEvent}
          onSelectDate={setSelectedDate}
        />
      </div>

      {detailEvent && (
        <div className="modal-overlay" onClick={() => setDetailSeedEvent(null)}>
          <div className="modal-card calendar-modal-card" onClick={(event) => event.stopPropagation()}>
            {detailSeedEvent?.source === 'event' && detailQuery.isLoading && !detailQuery.data ? <LoadingState /> : <EventDetail event={detailEvent} onClose={() => setDetailSeedEvent(null)} onRsvp={(status) => void handleRsvp(status)} onEdit={() => { setEditorEvent(detailEvent); setEditorOpen(true); }} onDelete={() => void handleDeleteEvent()} showOpenPageLink={detailEvent.source === 'event'} />}
          </div>
        </div>
      )}

      <EventForm isOpen={editorOpen} initialEvent={editorEvent} userRole={user?.role || 'STD'} availableClasses={options.classes} onClose={() => { setEditorOpen(false); setEditorEvent(null); }} onSubmit={handleSaveEvent} />
    </div>
  );
}
