import { api } from '@/core/api/client';
import type {
  CalendarEventItem,
  CalendarOptionsPayload,
  EventRsvpItem,
  EventRsvpStatus,
  ReminderPreference,
} from '@/entities/communication/calendar/model/types';

export interface CalendarEventsFilters extends Record<string, string | number | undefined> {
  from: string;
  to: string;
  class_id?: string;
  type?: string;
  cursor?: string;
}

export type CalendarEventPayload = Record<string, unknown>;

export type HolidayType = 'national' | 'school';

export interface Holiday {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  type: HolidayType;
  description?: string | null;
}

export interface HolidayPayload {
  name: string;
  start_date: string;
  end_date: string;
  type: HolidayType;
  description?: string;
}

export const calendarService = {
  listEvents(params: CalendarEventsFilters) {
    return api.list<CalendarEventItem>('/events', params);
  },

  getOptions() {
    return api.get<CalendarOptionsPayload>('/calendar/options');
  },

  getEvent(id: string) {
    return api.get<CalendarEventItem>(`/events/${id}`);
  },

  createEvent(payload: CalendarEventPayload) {
    return api.post<CalendarEventItem>('/events', payload);
  },

  updateEvent(id: string, payload: CalendarEventPayload) {
    return api.put<CalendarEventItem>(`/events/${id}`, payload);
  },

  deleteEvent(id: string) {
    return api.delete<void>(`/events/${id}`);
  },

  respondToEvent(id: string, status: EventRsvpStatus) {
    return api.post<void>(`/events/${id}/rsvp`, { status });
  },

  getMyRSVP(eventId: string) {
    return api.get<{ status: EventRsvpStatus | null }>(`/events/${eventId}/rsvp`);
  },

  getEventRSVPs(eventId: string) {
    return api.get<EventRsvpItem[]>(`/events/${eventId}/rsvps`);
  },

  getHolidays() {
    return api.get<Holiday[]>('/calendar/holidays');
  },

  createHoliday(payload: HolidayPayload) {
    return api.post<Holiday>('/calendar/holidays', payload);
  },

  updateHoliday(id: string, payload: HolidayPayload) {
    return api.put<Holiday>(`/calendar/holidays/${id}`, payload);
  },

  deleteHoliday(id: string) {
    return api.delete<void>(`/calendar/holidays/${id}`);
  },

  updateReminderPreferences(preferences: ReminderPreference[]) {
    return api.post<ReminderPreference[]>('/events/reminder-preferences', { preferences });
  },

  getICalFeed() {
    return api.get<{ url: string }>('/calendar/ical');
  },
};
