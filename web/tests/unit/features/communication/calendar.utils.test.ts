import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  EVENT_TYPES,
  eventTitle,
  formatEventRange,
  toEventFormState,
  toEventPayload,
  buildGoogleCalendarUrl,
  buildOutlookCalendarUrl,
  eventTypeColor,
  cloneDate,
  dayKey,
  addDays,
  startOfWeek,
  rangeForView,
  occursOnDay,
  shiftAnchorDate,
} from '@/features/communication/calendar/calendar.utils';
import type { CalendarEventItem } from '@/features/communication/calendar/model/types';

const mockEvent: CalendarEventItem = {
  id: 'evt-1',
  instance_id: 'inst-1',
  school_id: 'sch-1',
  title_fr: 'Réunion des parents',
  title_ar: 'اجتماع الآباء',
  title_en: 'Parent meeting',
  description: 'Annual meeting',
  type: 'meeting',
  visibility: 'school',
  start_at: '2026-09-10T09:00:00Z',
  end_at: '2026-09-10T11:00:00Z',
  is_all_day: false,
  location: 'Salle principale',
  capacity: null,
  class_id: null,
  role_codes: [],
  recurrence_rule: null,
  created_by: 'user-1',
  created_at: '2026-01-01T00:00:00Z',
};

describe('EVENT_TYPES', () => {
  it('contains all expected event types', () => {
    expect(EVENT_TYPES).toContain('holiday');
    expect(EVENT_TYPES).toContain('exam');
    expect(EVENT_TYPES).toContain('meeting');
    expect(EVENT_TYPES).toContain('excursion');
    expect(EVENT_TYPES).toContain('ceremony');
    expect(EVENT_TYPES).toContain('custom');
  });
});

describe('eventTitle', () => {
  it('returns Arabic title for ar lang', () => {
    expect(eventTitle(mockEvent, 'ar')).toBe('اجتماع الآباء');
  });

  it('returns English title for en lang', () => {
    expect(eventTitle(mockEvent, 'en')).toBe('Parent meeting');
  });

  it('returns French title as fallback', () => {
    expect(eventTitle(mockEvent, 'fr')).toBe('Réunion des parents');
  });

  it('falls back to French if ar title is not set', () => {
    const event = { ...mockEvent, title_ar: undefined };
    expect(eventTitle(event, 'ar')).toBe('Réunion des parents');
  });

  it('falls back to French if en title is not set', () => {
    const event = { ...mockEvent, title_en: undefined };
    expect(eventTitle(event, 'en')).toBe('Réunion des parents');
  });
});

describe('formatEventRange', () => {
  it('formats all-day events as a date string', () => {
    const event = { ...mockEvent, is_all_day: true };
    const result = formatEventRange(event, 'fr');
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });

  it('formats same-day events with start and end time', () => {
    const result = formatEventRange(mockEvent, 'fr');
    expect(result).toContain('•');
  });

  it('formats multi-day events with arrow separator', () => {
    const multiDayEvent = {
      ...mockEvent,
      start_at: '2026-09-10T09:00:00Z',
      end_at: '2026-09-12T11:00:00Z',
    };
    const result = formatEventRange(multiDayEvent, 'fr');
    expect(result).toContain('→');
  });
});

describe('toEventFormState', () => {
  it('returns default form when event is null', () => {
    const form = toEventFormState(null, 'ADM', []);
    expect(form.title_fr).toBe('');
    expect(form.type).toBe('meeting');
    expect(form.visibility).toBe('school');
    expect(form.is_all_day).toBe(false);
  });

  it('returns default form with visibility=class for TCH role', () => {
    const form = toEventFormState(null, 'TCH', []);
    expect(form.visibility).toBe('class');
  });

  it('uses first available class when creating for TCH', () => {
    const classes = [{ id: 'cls-1', name: 'Class 6A', code: '6A' }];
    const form = toEventFormState(null, 'TCH', classes);
    expect(form.class_id).toBe('cls-1');
  });

  it('maps event data to form state', () => {
    const form = toEventFormState(mockEvent, 'ADM', []);
    expect(form.title_fr).toBe('Réunion des parents');
    expect(form.title_ar).toBe('اجتماع الآباء');
    expect(form.title_en).toBe('Parent meeting');
    expect(form.description).toBe('Annual meeting');
    expect(form.type).toBe('meeting');
    expect(form.location).toBe('Salle principale');
    expect(form.is_all_day).toBe(false);
  });

  it('maps recurrence rule data', () => {
    const recurringEvent = {
      ...mockEvent,
      recurrence_rule: {
        frequency: 'weekly',
        interval: 2,
        until: '2026-12-31T00:00:00Z',
      },
    };
    const form = toEventFormState(recurringEvent, 'ADM', []);
    expect(form.recurrence_frequency).toBe('weekly');
    expect(form.recurrence_interval).toBe('2');
    expect(form.recurrence_until).toBeTruthy();
  });
});

describe('toEventPayload', () => {
  it('trims title_fr', () => {
    const form = {
      title_fr: '  Meeting  ',
      title_ar: '',
      title_en: '',
      description: '',
      type: 'meeting',
      visibility: 'school',
      start_at: '2026-09-10T09:00',
      end_at: '2026-09-10T11:00',
      location: '',
      capacity: '',
      class_id: '',
      role_codes: [],
      is_all_day: false,
      recurrence_frequency: '',
      recurrence_interval: '1',
      recurrence_until: '',
    };
    const payload = toEventPayload(form, 'ADM');
    expect(payload.title_fr).toBe('Meeting');
  });

  it('forces visibility=class for TCH role', () => {
    const form = {
      title_fr: 'Meeting',
      title_ar: '',
      title_en: '',
      description: '',
      type: 'meeting',
      visibility: 'school',
      start_at: '2026-09-10T09:00',
      end_at: '2026-09-10T11:00',
      location: '',
      capacity: '',
      class_id: 'cls-1',
      role_codes: [],
      is_all_day: false,
      recurrence_frequency: '',
      recurrence_interval: '1',
      recurrence_until: '',
    };
    const payload = toEventPayload(form, 'TCH');
    expect(payload.visibility).toBe('class');
    expect(payload.class_id).toBe('cls-1');
  });

  it('includes recurrence_rule when frequency is set', () => {
    const form = {
      title_fr: 'Weekly',
      title_ar: '',
      title_en: '',
      description: '',
      type: 'meeting',
      visibility: 'school',
      start_at: '2026-09-10T09:00',
      end_at: '2026-09-10T11:00',
      location: '',
      capacity: '',
      class_id: '',
      role_codes: [],
      is_all_day: false,
      recurrence_frequency: 'weekly',
      recurrence_interval: '2',
      recurrence_until: '',
    };
    const payload = toEventPayload(form, 'ADM');
    expect(payload.recurrence_rule).toBeDefined();
    expect((payload.recurrence_rule as { frequency: string }).frequency).toBe('weekly');
    expect((payload.recurrence_rule as { interval: number }).interval).toBe(2);
  });

  it('omits recurrence_rule when no frequency', () => {
    const form = {
      title_fr: 'Single',
      title_ar: '',
      title_en: '',
      description: '',
      type: 'meeting',
      visibility: 'school',
      start_at: '2026-09-10T09:00',
      end_at: '2026-09-10T11:00',
      location: '',
      capacity: '',
      class_id: '',
      role_codes: [],
      is_all_day: false,
      recurrence_frequency: '',
      recurrence_interval: '1',
      recurrence_until: '',
    };
    const payload = toEventPayload(form, 'ADM');
    expect(payload.recurrence_rule).toBeUndefined();
  });

  it('converts capacity to number when provided', () => {
    const form = {
      title_fr: 'Test',
      title_ar: '',
      title_en: '',
      description: '',
      type: 'meeting',
      visibility: 'school',
      start_at: '2026-09-10T09:00',
      end_at: '2026-09-10T11:00',
      location: '',
      capacity: '50',
      class_id: '',
      role_codes: [],
      is_all_day: false,
      recurrence_frequency: '',
      recurrence_interval: '1',
      recurrence_until: '',
    };
    const payload = toEventPayload(form, 'ADM');
    expect(payload.capacity).toBe(50);
  });

  it('includes role_codes for role visibility', () => {
    const form = {
      title_fr: 'Role event',
      title_ar: '',
      title_en: '',
      description: '',
      type: 'meeting',
      visibility: 'role',
      start_at: '2026-09-10T09:00',
      end_at: '2026-09-10T11:00',
      location: '',
      capacity: '',
      class_id: '',
      role_codes: ['TCH', 'ADM'],
      is_all_day: false,
      recurrence_frequency: '',
      recurrence_interval: '1',
      recurrence_until: '',
    };
    const payload = toEventPayload(form, 'ADM');
    expect(payload.role_codes).toEqual(['TCH', 'ADM']);
  });
});

describe('buildGoogleCalendarUrl', () => {
  it('returns a google calendar URL', () => {
    const url = buildGoogleCalendarUrl(mockEvent, 'fr');
    expect(url).toContain('calendar.google.com');
    expect(url).toContain('TEMPLATE');
    // URLSearchParams encodes spaces as + not %20
    expect(url).toContain('R%C3%A9union');
  });

  it('uses language-appropriate title', () => {
    const urlEn = buildGoogleCalendarUrl(mockEvent, 'en');
    expect(urlEn).toContain('Parent');
    expect(urlEn).toContain('meeting');
  });
});

describe('buildOutlookCalendarUrl', () => {
  it('returns an outlook URL', () => {
    const url = buildOutlookCalendarUrl(mockEvent, 'fr');
    expect(url).toContain('outlook.live.com');
    expect(url).toContain('addevent');
  });
});

describe('eventTypeColor', () => {
  it('maps holiday to correct class', () => {
    expect(eventTypeColor('holiday')).toBe('calendar-type--holiday');
  });

  it('maps exam to correct class', () => {
    expect(eventTypeColor('exam')).toBe('calendar-type--exam');
  });

  it('maps meeting to correct class', () => {
    expect(eventTypeColor('meeting')).toBe('calendar-type--meeting');
  });

  it('maps excursion to correct class', () => {
    expect(eventTypeColor('excursion')).toBe('calendar-type--excursion');
  });

  it('maps ceremony to correct class', () => {
    expect(eventTypeColor('ceremony')).toBe('calendar-type--ceremony');
  });

  it('maps unknown type to custom', () => {
    expect(eventTypeColor('other')).toBe('calendar-type--custom');
    expect(eventTypeColor('custom')).toBe('calendar-type--custom');
  });
});

describe('cloneDate', () => {
  it('returns a new Date with same year/month/day', () => {
    const original = new Date(2026, 8, 10, 15, 30);
    const cloned = cloneDate(original);
    expect(cloned.getFullYear()).toBe(2026);
    expect(cloned.getMonth()).toBe(8);
    expect(cloned.getDate()).toBe(10);
    expect(cloned).not.toBe(original);
  });

  it('resets time to midnight', () => {
    const d = new Date(2026, 5, 15, 14, 30, 45);
    const cloned = cloneDate(d);
    expect(cloned.getHours()).toBe(0);
    expect(cloned.getMinutes()).toBe(0);
    expect(cloned.getSeconds()).toBe(0);
  });
});

describe('dayKey', () => {
  it('returns YYYY-MM-DD format', () => {
    const d = new Date('2026-09-10T09:00:00Z');
    const key = dayKey(d);
    expect(key).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

describe('addDays', () => {
  it('adds days correctly', () => {
    const base = new Date(2026, 8, 10);
    const result = addDays(base, 5);
    expect(result.getDate()).toBe(15);
    expect(result.getMonth()).toBe(8);
  });

  it('handles month overflow', () => {
    const base = new Date(2026, 8, 28);
    const result = addDays(base, 5);
    expect(result.getMonth()).toBe(9);
    expect(result.getDate()).toBe(3);
  });

  it('handles negative days', () => {
    const base = new Date(2026, 8, 10);
    const result = addDays(base, -3);
    expect(result.getDate()).toBe(7);
  });
});

describe('startOfWeek', () => {
  it('returns Monday for a Wednesday', () => {
    // 2026-09-09 is a Wednesday
    const wednesday = new Date(2026, 8, 9);
    const monday = startOfWeek(wednesday);
    expect(monday.getDay()).toBe(1); // Monday
    expect(monday.getDate()).toBe(7);
  });

  it('returns same day for Monday', () => {
    // 2026-09-07 is a Monday
    const monday = new Date(2026, 8, 7);
    const result = startOfWeek(monday);
    expect(result.getDay()).toBe(1);
    expect(result.getDate()).toBe(7);
  });

  it('returns Monday for Sunday', () => {
    // 2026-09-13 is a Sunday
    const sunday = new Date(2026, 8, 13);
    const result = startOfWeek(sunday);
    expect(result.getDay()).toBe(1);
  });
});

describe('rangeForView', () => {
  it('returns week range for week view', () => {
    const anchor = new Date(2026, 8, 9); // Wednesday Sep 9
    const range = rangeForView('week', anchor);
    expect(range.from.getDay()).toBe(1); // starts on Monday
    const diff = (range.to.getTime() - range.from.getTime()) / (1000 * 60 * 60 * 24);
    expect(diff).toBe(6);
  });

  it('returns month range for month view', () => {
    const anchor = new Date(2026, 8, 15); // September
    const range = rangeForView('month', anchor);
    expect(range.from <= new Date(2026, 8, 1)).toBe(true);
    expect(range.to >= new Date(2026, 8, 30)).toBe(true);
  });
});

describe('occursOnDay', () => {
  it('returns true when event is on the day', () => {
    const day = new Date(2026, 8, 10);
    expect(occursOnDay(mockEvent, day)).toBe(true);
  });

  it('returns false when event is not on the day', () => {
    const day = new Date(2026, 8, 11);
    expect(occursOnDay(mockEvent, day)).toBe(false);
  });

  it('returns true for multi-day events covering the day', () => {
    const multiDay = {
      ...mockEvent,
      start_at: '2026-09-08T09:00:00Z',
      end_at: '2026-09-12T11:00:00Z',
    };
    const day = new Date(2026, 8, 10);
    expect(occursOnDay(multiDay, day)).toBe(true);
  });
});

describe('shiftAnchorDate', () => {
  it('shifts by 7 days forward for week view', () => {
    const base = new Date(2026, 8, 7);
    const result = shiftAnchorDate('week', base, 1);
    expect(result.getDate()).toBe(14);
  });

  it('shifts by 7 days backward for week view', () => {
    const base = new Date(2026, 8, 14);
    const result = shiftAnchorDate('week', base, -1);
    expect(result.getDate()).toBe(7);
  });

  it('shifts by one month forward for month view', () => {
    const base = new Date(2026, 8, 1); // September
    const result = shiftAnchorDate('month', base, 1);
    expect(result.getMonth()).toBe(9); // October
  });

  it('shifts by one month backward for month view', () => {
    const base = new Date(2026, 8, 1); // September
    const result = shiftAnchorDate('month', base, -1);
    expect(result.getMonth()).toBe(7); // August
  });
});
