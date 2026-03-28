import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ApiClientError, type ApiError } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import {
  useCalendarEvent,
  useCalendarEventRsvp,
  useCalendarOptions,
  useDeleteCalendarEvent,
  useUpdateCalendarEvent,
} from './useCalendar';
import { EventDetailView, EventEditorModal } from './shared';
import type { CalendarEventItem, CalendarOptionsPayload, EventRsvpStatus } from './types';

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

export function EventDetailPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const [editorOpen, setEditorOpen] = useState(false);
  const [dismissedError, setDismissedError] = useState(false);

  const eventQuery = useCalendarEvent(id, { enabled: Boolean(id), refetchInterval: 5000 });
  const optionsQuery = useCalendarOptions();
  const updateEventMutation = useUpdateCalendarEvent();
  const deleteEventMutation = useDeleteCalendarEvent();
  const rsvpMutation = useCalendarEventRsvp();

  const event: CalendarEventItem | null = eventQuery.data ?? null;
  const options: CalendarOptionsPayload = optionsQuery.data ?? {
    classes: [],
    ical_url: '',
    reminder_preferences: [],
  };
  const bannerError = useMemo(
    () =>
      toBannerError(
        eventQuery.error ??
          optionsQuery.error ??
          updateEventMutation.error ??
          deleteEventMutation.error ??
          rsvpMutation.error,
        t('app.error')
      ),
    [
      deleteEventMutation.error,
      eventQuery.error,
      optionsQuery.error,
      rsvpMutation.error,
      t,
      updateEventMutation.error,
    ]
  );

  useEffect(() => {
    setDismissedError(false);
  }, [bannerError]);

  async function handleRsvp(status: EventRsvpStatus) {
    if (!id) {
      return;
    }
    await rsvpMutation.mutateAsync({ id, status });
  }

  async function handleSaveEvent(payload: Record<string, unknown>) {
    if (!id) {
      return;
    }
    await updateEventMutation.mutateAsync({ id, payload });
    setEditorOpen(false);
  }

  async function handleDeleteEvent() {
    if (!id || !window.confirm(t('calendar.confirmDelete'))) {
      return;
    }
    await deleteEventMutation.mutateAsync(id);
    navigate('/calendar');
  }

  if ((eventQuery.isLoading && !event) || (optionsQuery.isLoading && !optionsQuery.data)) {
    return <LoadingState />;
  }

  if (!event) {
    return <EmptyState message={t('calendar.noEvents')} icon="📅" />;
  }

  return (
    <div className="page event-detail-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('calendar.eventDetailTitle')}</h1>
          <p className="page-subtitle">{t('calendar.subtitle')}</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-secondary" type="button" onClick={() => navigate('/calendar')}>
            {t('calendar.backToCalendar')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={dismissedError ? null : bannerError}
        onDismiss={() => setDismissedError(true)}
        onRetry={() => void Promise.all([eventQuery.refetch(), optionsQuery.refetch()])}
      />

      <div className="card">
        <EventDetailView
          event={event}
          onRsvp={(status) => void handleRsvp(status)}
          onEdit={() => setEditorOpen(true)}
          onDelete={() => void handleDeleteEvent()}
        />
      </div>

      <EventEditorModal
        isOpen={editorOpen}
        initialEvent={event}
        userRole={user?.role || 'STD'}
        availableClasses={options.classes}
        onClose={() => setEditorOpen(false)}
        onSubmit={handleSaveEvent}
      />
    </div>
  );
}
