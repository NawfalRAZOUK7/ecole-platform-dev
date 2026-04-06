import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { buildGoogleCalendarUrl, buildOutlookCalendarUrl, downloadEventIcs, eventTitle, eventTypeColor, formatEventRange } from './calendar.utils';
import type { EventDetailProps } from './calendar.types';
import type { EventRsvpStatus } from './types';

export function EventDetail({ event, onClose, onDelete, onEdit, onRsvp, showOpenPageLink = false }: EventDetailProps) {
  const { t, i18n } = useTranslation();
  const googleUrl = useMemo(() => buildGoogleCalendarUrl(event, i18n.language), [event, i18n.language]);
  const outlookUrl = useMemo(() => buildOutlookCalendarUrl(event, i18n.language), [event, i18n.language]);
  const mapUrl = event.latitude != null && event.longitude != null ? `https://maps.google.com/?q=${event.latitude},${event.longitude}` : event.location ? `https://maps.google.com/?q=${encodeURIComponent(event.location)}` : null;

  return (
    <div className="calendar-detail-card">
      <div className="calendar-detail-card__header">
        <div>
          <span className={`calendar-type-pill ${eventTypeColor(event.type)}`}>{t(`calendar.types.${event.type}`)}</span>
          <h2>{eventTitle(event, i18n.language)}</h2>
        </div>
        {onClose && <button className="dropdown-link" type="button" onClick={onClose}>{t('app.cancel')}</button>}
      </div>
      <div className="calendar-detail-card__meta">
        <p>{formatEventRange(event, i18n.language)}</p>
        {event.location && <p>{event.location}</p>}
        {event.capacity != null && <p>{t('calendar.capacityValue', { count: event.capacity })}</p>}
        {event.recurrence_rule && <p>{t(`calendar.recurrence.${event.recurrence_rule.frequency}`)}</p>}
      </div>
      {event.description && <p className="calendar-detail-card__description">{event.description}</p>}
      <div className="calendar-rsvp-summary">
        <span>{t('calendar.rsvpSummary.attending', { count: event.attendee_count })}</span>
        <span>{t('calendar.rsvpSummary.maybe', { count: event.maybe_count })}</span>
        <span>{t('calendar.rsvpSummary.declined', { count: event.declined_count })}</span>
      </div>
      {event.can_rsvp && onRsvp && <div className="calendar-detail-card__actions">{(['attending', 'maybe', 'declined'] as EventRsvpStatus[]).map((status) => <button key={status} className={`btn ${event.my_rsvp === status ? 'btn-primary' : 'btn-secondary'}`} type="button" onClick={() => onRsvp(status)}>{t(`calendar.rsvp.${status}`)}</button>)}</div>}
      <div className="calendar-detail-card__links">
        <a href={googleUrl} target="_blank" rel="noreferrer">{t('calendar.external.google')}</a>
        <a href={outlookUrl} target="_blank" rel="noreferrer">{t('calendar.external.outlook')}</a>
        <button type="button" className="dropdown-link" onClick={() => downloadEventIcs(event, i18n.language)}>{t('calendar.external.ical')}</button>
        {mapUrl && <a href={mapUrl} target="_blank" rel="noreferrer">{t('calendar.external.map')}</a>}
        {showOpenPageLink && <Link to={`/events/${event.id}`}>{t('calendar.openPage')}</Link>}
      </div>
      {(event.can_edit || event.can_delete) && <div className="calendar-detail-card__actions">{event.can_edit && onEdit && <button className="btn btn-secondary" type="button" onClick={onEdit}>{t('calendar.editEvent')}</button>}{event.can_delete && onDelete && <button className="btn btn-secondary" type="button" onClick={onDelete}>{t('calendar.deleteEvent')}</button>}</div>}
      {event.rsvps && <div className="calendar-attendee-list"><h3>{t('calendar.attendees')}</h3>{event.rsvps.length === 0 ? <p>{t('calendar.noAttendees')}</p> : event.rsvps.map((item) => <div key={item.user_id} className="calendar-attendee-row"><strong>{item.full_name}</strong><span>{item.role || '—'}</span><span>{t(`calendar.rsvp.${item.status}`)}</span></div>)}</div>}
    </div>
  );
}
