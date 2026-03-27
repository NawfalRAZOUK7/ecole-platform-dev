import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EventDetailView, EventEditorModal } from './shared';
import type { CalendarEventItem, CalendarOptionsPayload, EventRsvpStatus } from './types';

export function EventDetailPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const [event, setEvent] = useState<CalendarEventItem | null>(null);
  const [options, setOptions] = useState<CalendarOptionsPayload>({
    classes: [],
    ical_url: '',
    reminder_preferences: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);

  const loadEvent = useCallback(async () => {
    if (!id) {
      return;
    }
    try {
      const [eventResponse, optionsResponse] = await Promise.all([
        api.get<CalendarEventItem>(`/events/${id}`),
        api.get<CalendarOptionsPayload>('/calendar/options'),
      ]);
      setEvent(eventResponse.data);
      setOptions(optionsResponse.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => {
    void loadEvent();
  }, [loadEvent]);

  useEffect(() => {
    if (!event?.source || event.source !== 'event') {
      return undefined;
    }
    const timer = window.setInterval(() => {
      void loadEvent();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [event?.source, loadEvent]);

  async function handleRsvp(status: EventRsvpStatus) {
    if (!id) {
      return;
    }
    try {
      await api.post(`/events/${id}/rsvp`, { status });
      await loadEvent();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  async function handleSaveEvent(payload: Record<string, unknown>) {
    if (!id) {
      return;
    }
    try {
      await api.put(`/events/${id}`, payload);
      setEditorOpen(false);
      await loadEvent();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
      throw err;
    }
  }

  async function handleDeleteEvent() {
    if (!id || !window.confirm(t('calendar.confirmDelete'))) {
      return;
    }
    try {
      await api.delete(`/events/${id}`);
      navigate('/calendar');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  if (loading) {
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

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => void loadEvent()} />

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
