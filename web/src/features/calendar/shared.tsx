import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { formatDate } from '@/shared/i18n';
import type {
  CalendarClassOption,
  CalendarEventItem,
  EventFormState,
  EventRsvpStatus,
} from './types';

const ROLE_OPTIONS = ['ADM', 'DIR', 'TCH', 'PAR', 'STD'] as const;

function nowPlus(hours: number) {
  const value = new Date();
  value.setMinutes(0, 0, 0);
  value.setHours(value.getHours() + hours);
  return value.toISOString().slice(0, 16);
}

export function eventTitle(event: CalendarEventItem, lang: string) {
  if (lang.startsWith('ar') && event.title_ar) return event.title_ar;
  if (lang.startsWith('en') && event.title_en) return event.title_en;
  return event.title_fr;
}

export function formatEventRange(
  event: Pick<CalendarEventItem, 'start_at' | 'end_at' | 'is_all_day'>,
  lang: string
) {
  if (event.is_all_day) {
    return formatDate(event.start_at, lang, { dateStyle: 'full' });
  }
  const sameDay =
    new Date(event.start_at).toDateString() === new Date(event.end_at).toDateString();
  if (sameDay) {
    return `${formatDate(event.start_at, lang, {
      dateStyle: 'full',
      timeStyle: 'short',
    })} • ${formatDate(event.end_at, lang, { timeStyle: 'short' })}`;
  }
  return `${formatDate(event.start_at, lang, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })} → ${formatDate(event.end_at, lang, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })}`;
}

function defaultForm(userRole: string, availableClasses: CalendarClassOption[]): EventFormState {
  return {
    title_fr: '',
    title_ar: '',
    title_en: '',
    description: '',
    type: 'meeting',
    visibility: userRole === 'TCH' ? 'class' : 'school',
    start_at: nowPlus(1),
    end_at: nowPlus(2),
    location: '',
    capacity: '',
    class_id: availableClasses[0]?.id || '',
    role_codes: [],
    is_all_day: false,
    recurrence_frequency: '',
    recurrence_interval: '1',
    recurrence_until: '',
  };
}

export function toEventFormState(
  event: CalendarEventItem | null | undefined,
  userRole: string,
  availableClasses: CalendarClassOption[]
): EventFormState {
  if (!event) {
    return defaultForm(userRole, availableClasses);
  }
  return {
    title_fr: event.title_fr,
    title_ar: event.title_ar || '',
    title_en: event.title_en || '',
    description: event.description || '',
    type: event.type,
    visibility: event.visibility,
    start_at: event.start_at.slice(0, 16),
    end_at: event.end_at.slice(0, 16),
    location: event.location || '',
    capacity: event.capacity ? String(event.capacity) : '',
    class_id: event.class_id || availableClasses[0]?.id || '',
    role_codes: event.role_codes || [],
    is_all_day: event.is_all_day,
    recurrence_frequency: event.recurrence_rule?.frequency || '',
    recurrence_interval: String(event.recurrence_rule?.interval || 1),
    recurrence_until: event.recurrence_rule?.until?.slice(0, 16) || '',
  };
}

export function toEventPayload(form: EventFormState, userRole: string) {
  return {
    title_fr: form.title_fr.trim(),
    title_ar: form.title_ar.trim() || undefined,
    title_en: form.title_en.trim() || undefined,
    description: form.description.trim() || undefined,
    type: form.type,
    visibility: userRole === 'TCH' ? 'class' : form.visibility,
    start_at: new Date(form.start_at).toISOString(),
    end_at: new Date(form.end_at).toISOString(),
    location: form.location.trim() || undefined,
    capacity: form.capacity ? Number(form.capacity) : undefined,
    class_id:
      (userRole === 'TCH' || form.visibility === 'class') && form.class_id
        ? form.class_id
        : undefined,
    role_codes: form.visibility === 'role' ? form.role_codes : undefined,
    is_all_day: form.is_all_day,
    recurrence_rule: form.recurrence_frequency
      ? {
          frequency: form.recurrence_frequency,
          interval: Number(form.recurrence_interval || 1),
          until: form.recurrence_until
            ? new Date(form.recurrence_until).toISOString()
            : undefined,
        }
      : undefined,
    reminder_offsets_minutes: [1440, 60],
  };
}

function escapeIcs(value: string) {
  return value.replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/,/g, '\\,').replace(/;/g, '\\;');
}

function toUtcStamp(value: string) {
  return new Date(value).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
}

export function buildGoogleCalendarUrl(event: CalendarEventItem, lang: string) {
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: eventTitle(event, lang),
    dates: `${toUtcStamp(event.start_at)}/${toUtcStamp(event.end_at)}`,
    details: event.description || '',
    location: event.location || '',
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export function buildOutlookCalendarUrl(event: CalendarEventItem, lang: string) {
  const params = new URLSearchParams({
    path: '/calendar/action/compose',
    rru: 'addevent',
    subject: eventTitle(event, lang),
    startdt: event.start_at,
    enddt: event.end_at,
    body: event.description || '',
    location: event.location || '',
  });
  return `https://outlook.live.com/calendar/0/deeplink/compose?${params.toString()}`;
}

export function downloadEventIcs(event: CalendarEventItem, lang: string) {
  const summary = escapeIcs(eventTitle(event, lang));
  const description = escapeIcs(event.description || '');
  const location = escapeIcs(event.location || '');
  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Ecole Platform//Calendar//EN',
    'BEGIN:VEVENT',
    `UID:${event.instance_id}@ecole-platform.ma`,
    `DTSTAMP:${toUtcStamp(new Date().toISOString())}`,
    event.is_all_day
      ? `DTSTART;VALUE=DATE:${toUtcStamp(event.start_at).slice(0, 8)}`
      : `DTSTART:${toUtcStamp(event.start_at)}`,
    event.is_all_day
      ? `DTEND;VALUE=DATE:${toUtcStamp(event.end_at).slice(0, 8)}`
      : `DTEND:${toUtcStamp(event.end_at)}`,
    `SUMMARY:${summary}`,
    `DESCRIPTION:${description}`,
    `LOCATION:${location}`,
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n');

  const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `event-${event.id}.ics`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function eventTypeColor(type: string) {
  switch (type) {
    case 'holiday':
      return 'calendar-type--holiday';
    case 'exam':
      return 'calendar-type--exam';
    case 'meeting':
      return 'calendar-type--meeting';
    case 'excursion':
      return 'calendar-type--excursion';
    case 'ceremony':
      return 'calendar-type--ceremony';
    default:
      return 'calendar-type--custom';
  }
}

interface EventEditorModalProps {
  isOpen: boolean;
  initialEvent?: CalendarEventItem | null;
  userRole: string;
  availableClasses: CalendarClassOption[];
  onClose: () => void;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
}

export function EventEditorModal({
  isOpen,
  initialEvent,
  userRole,
  availableClasses,
  onClose,
  onSubmit,
}: EventEditorModalProps) {
  const { t } = useTranslation();
  const [form, setForm] = useState<EventFormState>(
    toEventFormState(initialEvent, userRole, availableClasses)
  );
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(toEventFormState(initialEvent, userRole, availableClasses));
  }, [availableClasses, initialEvent, isOpen, userRole]);

  const canSetVisibility = userRole !== 'TCH';

  if (!isOpen) {
    return null;
  }

  async function handleSubmit() {
    setSaving(true);
    try {
      await onSubmit(toEventPayload(form, userRole));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card calendar-modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="calendar-modal-card__header">
          <h2>{t(initialEvent ? 'calendar.editEvent' : 'calendar.createEvent')}</h2>
          <button className="dropdown-link" type="button" onClick={onClose}>
            {t('app.cancel')}
          </button>
        </div>

        <label className="form-field">
          <span>{t('calendar.form.titleFr')}</span>
          <input
            value={form.title_fr}
            onChange={(event) => setForm((current) => ({ ...current, title_fr: event.target.value }))}
          />
        </label>

        <div className="calendar-form-grid">
          <label className="form-field">
            <span>{t('calendar.form.titleAr')}</span>
            <input
              value={form.title_ar}
              onChange={(event) => setForm((current) => ({ ...current, title_ar: event.target.value }))}
            />
          </label>
          <label className="form-field">
            <span>{t('calendar.form.titleEn')}</span>
            <input
              value={form.title_en}
              onChange={(event) => setForm((current) => ({ ...current, title_en: event.target.value }))}
            />
          </label>
        </div>

        <div className="calendar-form-grid">
          <label className="form-field">
            <span>{t('calendar.form.type')}</span>
            <select
              value={form.type}
              onChange={(event) =>
                setForm((current) => ({ ...current, type: event.target.value as EventFormState['type'] }))
              }
            >
              {['holiday', 'exam', 'meeting', 'excursion', 'ceremony', 'custom'].map((value) => (
                <option key={value} value={value}>
                  {t(`calendar.types.${value}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>{t('calendar.form.visibility')}</span>
            <select
              disabled={!canSetVisibility}
              value={canSetVisibility ? form.visibility : 'class'}
              onChange={(event) =>
                setForm((current) => ({ ...current, visibility: event.target.value as EventFormState['visibility'] }))
              }
            >
              {['school', 'class', 'role'].map((value) => (
                <option key={value} value={value}>
                  {t(`calendar.visibility.${value}`)}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="calendar-form-grid">
          <label className="form-field">
            <span>{t('calendar.form.start')}</span>
            <input
              type="datetime-local"
              value={form.start_at}
              onChange={(event) => setForm((current) => ({ ...current, start_at: event.target.value }))}
            />
          </label>
          <label className="form-field">
            <span>{t('calendar.form.end')}</span>
            <input
              type="datetime-local"
              value={form.end_at}
              onChange={(event) => setForm((current) => ({ ...current, end_at: event.target.value }))}
            />
          </label>
        </div>

        <div className="calendar-form-grid">
          <label className="form-field">
            <span>{t('calendar.form.location')}</span>
            <input
              value={form.location}
              onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))}
            />
          </label>
          <label className="form-field">
            <span>{t('calendar.form.capacity')}</span>
            <input
              type="number"
              min="1"
              value={form.capacity}
              onChange={(event) => setForm((current) => ({ ...current, capacity: event.target.value }))}
            />
          </label>
        </div>

        {(userRole === 'TCH' || form.visibility === 'class') && (
          <label className="form-field">
            <span>{t('calendar.form.class')}</span>
            <select
              value={form.class_id}
              onChange={(event) => setForm((current) => ({ ...current, class_id: event.target.value }))}
            >
              {availableClasses.map((item) => (
                <option key={item.id} value={item.id}>
                  {[item.code, item.name].filter(Boolean).join(' · ')}
                </option>
              ))}
            </select>
          </label>
        )}

        {form.visibility === 'role' && (
          <div className="calendar-role-picker">
            <span>{t('calendar.form.roles')}</span>
            <div className="calendar-role-picker__list">
              {ROLE_OPTIONS.map((role) => (
                <label key={role} className="form-checkbox">
                  <input
                    type="checkbox"
                    checked={form.role_codes.includes(role)}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        role_codes: event.target.checked
                          ? [...current.role_codes, role]
                          : current.role_codes.filter((item) => item !== role),
                      }))
                    }
                  />
                  <span>{role}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        <label className="form-field">
          <span>{t('calendar.form.description')}</span>
          <textarea
            className="filter-input"
            rows={4}
            value={form.description}
            onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
          />
        </label>

        <div className="calendar-form-grid">
          <label className="form-checkbox">
            <input
              type="checkbox"
              checked={form.is_all_day}
              onChange={(event) => setForm((current) => ({ ...current, is_all_day: event.target.checked }))}
            />
            <span>{t('calendar.form.allDay')}</span>
          </label>
          <label className="form-field">
            <span>{t('calendar.form.recurrence')}</span>
            <select
              value={form.recurrence_frequency}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  recurrence_frequency: event.target.value as EventFormState['recurrence_frequency'],
                }))
              }
            >
              <option value="">{t('calendar.recurrence.none')}</option>
              <option value="weekly">{t('calendar.recurrence.weekly')}</option>
              <option value="annual">{t('calendar.recurrence.annual')}</option>
            </select>
          </label>
        </div>

        {form.recurrence_frequency && (
          <div className="calendar-form-grid">
            <label className="form-field">
              <span>{t('calendar.form.interval')}</span>
              <input
                type="number"
                min="1"
                value={form.recurrence_interval}
                onChange={(event) =>
                  setForm((current) => ({ ...current, recurrence_interval: event.target.value }))
                }
              />
            </label>
            <label className="form-field">
              <span>{t('calendar.form.until')}</span>
              <input
                type="datetime-local"
                value={form.recurrence_until}
                onChange={(event) => setForm((current) => ({ ...current, recurrence_until: event.target.value }))}
              />
            </label>
          </div>
        )}

        <div className="calendar-modal-card__actions">
          <button className="btn btn-secondary" type="button" onClick={onClose}>
            {t('app.cancel')}
          </button>
          <button
            className="btn btn-primary"
            type="button"
            disabled={saving || !form.title_fr.trim()}
            onClick={() => void handleSubmit()}
          >
            {saving ? t('calendar.saving') : t('app.save')}
          </button>
        </div>
      </div>
    </div>
  );
}

interface EventDetailViewProps {
  event: CalendarEventItem;
  onRsvp?: (status: EventRsvpStatus) => void;
  onEdit?: () => void;
  onDelete?: () => void;
  onClose?: () => void;
  showOpenPageLink?: boolean;
}

export function EventDetailView({
  event,
  onRsvp,
  onEdit,
  onDelete,
  onClose,
  showOpenPageLink = false,
}: EventDetailViewProps) {
  const { t, i18n } = useTranslation();
  const googleUrl = useMemo(() => buildGoogleCalendarUrl(event, i18n.language), [event, i18n.language]);
  const outlookUrl = useMemo(() => buildOutlookCalendarUrl(event, i18n.language), [event, i18n.language]);
  const mapUrl =
    event.latitude != null && event.longitude != null
      ? `https://maps.google.com/?q=${event.latitude},${event.longitude}`
      : event.location
        ? `https://maps.google.com/?q=${encodeURIComponent(event.location)}`
        : null;

  return (
    <div className="calendar-detail-card">
      <div className="calendar-detail-card__header">
        <div>
          <span className={`calendar-type-pill ${eventTypeColor(event.type)}`}>
            {t(`calendar.types.${event.type}`)}
          </span>
          <h2>{eventTitle(event, i18n.language)}</h2>
        </div>
        {onClose && (
          <button className="dropdown-link" type="button" onClick={onClose}>
            {t('app.cancel')}
          </button>
        )}
      </div>

      <div className="calendar-detail-card__meta">
        <p>{formatEventRange(event, i18n.language)}</p>
        {event.location && <p>{event.location}</p>}
        {event.capacity != null && (
          <p>{t('calendar.capacityValue', { count: event.capacity })}</p>
        )}
        {event.recurrence_rule && (
          <p>{t(`calendar.recurrence.${event.recurrence_rule.frequency}`)}</p>
        )}
      </div>

      {event.description && <p className="calendar-detail-card__description">{event.description}</p>}

      <div className="calendar-rsvp-summary">
        <span>{t('calendar.rsvpSummary.attending', { count: event.attendee_count })}</span>
        <span>{t('calendar.rsvpSummary.maybe', { count: event.maybe_count })}</span>
        <span>{t('calendar.rsvpSummary.declined', { count: event.declined_count })}</span>
      </div>

      {event.can_rsvp && onRsvp && (
        <div className="calendar-detail-card__actions">
          {(['attending', 'maybe', 'declined'] as EventRsvpStatus[]).map((status) => (
            <button
              key={status}
              className={`btn ${event.my_rsvp === status ? 'btn-primary' : 'btn-secondary'}`}
              type="button"
              onClick={() => onRsvp(status)}
            >
              {t(`calendar.rsvp.${status}`)}
            </button>
          ))}
        </div>
      )}

      <div className="calendar-detail-card__links">
        <a href={googleUrl} target="_blank" rel="noreferrer">
          {t('calendar.external.google')}
        </a>
        <a href={outlookUrl} target="_blank" rel="noreferrer">
          {t('calendar.external.outlook')}
        </a>
        <button type="button" className="dropdown-link" onClick={() => downloadEventIcs(event, i18n.language)}>
          {t('calendar.external.ical')}
        </button>
        {mapUrl && (
          <a href={mapUrl} target="_blank" rel="noreferrer">
            {t('calendar.external.map')}
          </a>
        )}
        {showOpenPageLink && <Link to={`/events/${event.id}`}>{t('calendar.openPage')}</Link>}
      </div>

      {(event.can_edit || event.can_delete) && (
        <div className="calendar-detail-card__actions">
          {event.can_edit && onEdit && (
            <button className="btn btn-secondary" type="button" onClick={onEdit}>
              {t('calendar.editEvent')}
            </button>
          )}
          {event.can_delete && onDelete && (
            <button className="btn btn-secondary" type="button" onClick={onDelete}>
              {t('calendar.deleteEvent')}
            </button>
          )}
        </div>
      )}

      {event.rsvps && (
        <div className="calendar-attendee-list">
          <h3>{t('calendar.attendees')}</h3>
          {event.rsvps.length === 0 ? (
            <p>{t('calendar.noAttendees')}</p>
          ) : (
            event.rsvps.map((item) => (
              <div key={item.user_id} className="calendar-attendee-row">
                <strong>{item.full_name}</strong>
                <span>{item.role || '—'}</span>
                <span>{t(`calendar.rsvp.${item.status}`)}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
