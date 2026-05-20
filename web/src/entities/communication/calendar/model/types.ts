export type CalendarView = 'month' | 'week' | 'agenda';

export type EventType = 'holiday' | 'exam' | 'meeting' | 'excursion' | 'ceremony' | 'custom';
export type EventVisibility = 'school' | 'class' | 'role';
export type EventRsvpStatus = 'attending' | 'maybe' | 'declined';

export interface CalendarClassOption {
  id: string;
  code: string;
  name: string;
}

export interface ReminderPreference {
  event_type: EventType;
  enabled: boolean;
}

export interface CalendarOptionsPayload {
  classes: CalendarClassOption[];
  ical_url: string;
  reminder_preferences: ReminderPreference[];
}

export interface EventRsvpItem {
  user_id: string;
  full_name: string;
  role: string;
  status: EventRsvpStatus;
  responded_at: string;
}

export interface CalendarEventItem {
  id: string;
  instance_id: string;
  source: string;
  title_fr: string;
  title_ar: string | null;
  title_en: string | null;
  description: string | null;
  type: EventType;
  visibility: EventVisibility;
  start_at: string;
  end_at: string;
  location: string | null;
  latitude: number | null;
  longitude: number | null;
  class_id: string | null;
  role_codes: string[] | null;
  capacity: number | null;
  rsvp_deadline: string | null;
  attendee_count: number;
  maybe_count: number;
  declined_count: number;
  my_rsvp: EventRsvpStatus | null;
  is_all_day: boolean;
  is_recurring: boolean;
  recurrence_rule: {
    frequency: 'weekly' | 'annual';
    interval: number;
    until?: string | null;
  } | null;
  can_edit: boolean;
  can_delete: boolean;
  can_rsvp: boolean;
  is_holiday: boolean;
  rsvps?: EventRsvpItem[] | null;
}

export interface EventFormState {
  title_fr: string;
  title_ar: string;
  title_en: string;
  description: string;
  type: EventType;
  visibility: EventVisibility;
  start_at: string;
  end_at: string;
  location: string;
  capacity: string;
  class_id: string;
  role_codes: string[];
  is_all_day: boolean;
  recurrence_frequency: '' | 'weekly' | 'annual';
  recurrence_interval: string;
  recurrence_until: string;
}
