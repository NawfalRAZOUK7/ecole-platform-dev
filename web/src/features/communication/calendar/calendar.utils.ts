import { formatDate } from '@/shared/i18n';
import type {
  CalendarClassOption,
  CalendarEventItem,
  CalendarView,
  EventFormState,
} from './model/types';

export const EVENT_TYPES = [
  'holiday',
  'exam',
  'meeting',
  'excursion',
  'ceremony',
  'custom',
] as const;

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
  lang: string,
) {
  if (event.is_all_day) {
    return formatDate(event.start_at, lang, { dateStyle: 'full' });
  }
  const sameDay = new Date(event.start_at).toDateString() === new Date(event.end_at).toDateString();
  if (sameDay) {
    return `${formatDate(event.start_at, lang, { dateStyle: 'full', timeStyle: 'short' })} • ${formatDate(event.end_at, lang, { timeStyle: 'short' })}`;
  }
  return `${formatDate(event.start_at, lang, { dateStyle: 'medium', timeStyle: 'short' })} → ${formatDate(event.end_at, lang, { dateStyle: 'medium', timeStyle: 'short' })}`;
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
  availableClasses: CalendarClassOption[],
): EventFormState {
  if (!event) return defaultForm(userRole, availableClasses);
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
          until: form.recurrence_until ? new Date(form.recurrence_until).toISOString() : undefined,
        }
      : undefined,
    reminder_offsets_minutes: [1440, 60],
  };
}

function escapeIcs(value: string) {
  return value
    .replace(/\\/g, '\\\\')
    .replace(/\n/g, '\\n')
    .replace(/,/g, '\\,')
    .replace(/;/g, '\\;');
}

function toUtcStamp(value: string) {
  return new Date(value)
    .toISOString()
    .replace(/[-:]/g, '')
    .replace(/\.\d{3}Z$/, 'Z');
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
    `SUMMARY:${escapeIcs(eventTitle(event, lang))}`,
    `DESCRIPTION:${escapeIcs(event.description || '')}`,
    `LOCATION:${escapeIcs(event.location || '')}`,
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

export function cloneDate(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate());
}

export function dayKey(value: Date) {
  return value.toISOString().slice(0, 10);
}

export function addDays(value: Date, days: number) {
  const next = new Date(value);
  next.setDate(next.getDate() + days);
  return next;
}

export function startOfWeek(value: Date) {
  const next = cloneDate(value);
  const delta = (next.getDay() + 6) % 7;
  next.setDate(next.getDate() - delta);
  return next;
}

function monthRange(value: Date) {
  const first = new Date(value.getFullYear(), value.getMonth(), 1);
  const last = new Date(value.getFullYear(), value.getMonth() + 1, 0);
  return { from: startOfWeek(first), to: addDays(startOfWeek(last), 6) };
}

export function rangeForView(view: CalendarView, anchor: Date) {
  if (view === 'week') {
    const from = startOfWeek(anchor);
    return { from, to: addDays(from, 6) };
  }
  return monthRange(anchor);
}

export function occursOnDay(event: CalendarEventItem, day: Date) {
  const dayStart = new Date(day);
  dayStart.setHours(0, 0, 0, 0);
  const dayEnd = new Date(day);
  dayEnd.setHours(23, 59, 59, 999);
  const start = new Date(event.start_at);
  const end = new Date(event.end_at);
  return start <= dayEnd && end >= dayStart;
}

export function shiftAnchorDate(view: CalendarView, current: Date, direction: -1 | 1) {
  const next = new Date(current);
  if (view === 'week') next.setDate(next.getDate() + direction * 7);
  else next.setMonth(next.getMonth() + direction);
  return next;
}
