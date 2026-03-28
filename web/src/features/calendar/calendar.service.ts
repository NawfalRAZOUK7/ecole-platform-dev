import { api } from '@/services/api/client';
import type { CalendarEventItem, CalendarOptionsPayload, EventRsvpStatus } from './types';

export interface CalendarEventsFilters extends Record<string, string | number | undefined> {
  from: string;
  to: string;
  class_id?: string;
  type?: string;
  cursor?: string;
}

export type CalendarEventPayload = Record<string, unknown>;

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
};
