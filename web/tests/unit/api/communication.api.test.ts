import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { calendarService } from '@/features/communication/calendar/api/calendar.api';
import { messagesService } from '@/features/communication/messages/api/messages.api';
import { announcementsService } from '@/features/communication/announcements/api/announcements.api';
import { notificationsService } from '@/features/communication/notifications/api/notifications.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

// ── calendarService ───────────────────────────────────────────────────────────

describe('calendarService', () => {
  const event = {
    id: 'event-1',
    title: 'Parent Meeting',
    start_date: '2025-01-10',
    end_date: '2025-01-10',
    type: 'meeting',
  };

  const holiday = {
    id: 'holiday-1',
    name: 'New Year',
    start_date: '2025-01-01',
    end_date: '2025-01-01',
    type: 'national' as const,
  };

  it('listEvents returns events', async () => {
    server.use(
      http.get('/api/v1/events', () => HttpResponse.json({ data: [event], meta: listMeta })),
    );
    const result = await calendarService.listEvents({ from: '2025-01-01', to: '2025-01-31' });
    expect(result.data).toHaveLength(1);
  });

  it('getOptions returns calendar options', async () => {
    server.use(
      http.get('/api/v1/calendar/options', () =>
        HttpResponse.json({ data: { classes: [], event_types: [] }, meta }),
      ),
    );
    const result = await calendarService.getOptions();
    expect(result.data).toBeDefined();
  });

  it('getEvent returns single event', async () => {
    server.use(http.get('/api/v1/events/event-1', () => HttpResponse.json({ data: event, meta })));
    const result = await calendarService.getEvent('event-1');
    expect(result.data.id).toBe('event-1');
  });

  it('createEvent posts new event', async () => {
    server.use(http.post('/api/v1/events', () => HttpResponse.json({ data: event, meta })));
    const result = await calendarService.createEvent({
      title: 'Parent Meeting',
      start_date: '2025-01-10',
      end_date: '2025-01-10',
    });
    expect(result.data.title).toBe('Parent Meeting');
  });

  it('updateEvent puts event', async () => {
    server.use(
      http.put('/api/v1/events/event-1', () =>
        HttpResponse.json({ data: { ...event, title: 'Updated Meeting' }, meta }),
      ),
    );
    const result = await calendarService.updateEvent('event-1', { title: 'Updated Meeting' });
    expect(result.data.title).toBe('Updated Meeting');
  });

  it('deleteEvent deletes event', async () => {
    server.use(
      http.delete('/api/v1/events/event-1', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await calendarService.deleteEvent('event-1');
    expect(result).toBeDefined();
  });

  it('respondToEvent posts RSVP', async () => {
    server.use(
      http.post('/api/v1/events/event-1/rsvp', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await calendarService.respondToEvent('event-1', 'attending');
    expect(result).toBeDefined();
  });

  it('getMyRSVP returns my rsvp status', async () => {
    server.use(
      http.get('/api/v1/events/event-1/rsvp', () =>
        HttpResponse.json({ data: { status: 'attending' }, meta }),
      ),
    );
    const result = await calendarService.getMyRSVP('event-1');
    expect(result.data.status).toBe('attending');
  });

  it('getEventRSVPs returns rsvp list', async () => {
    server.use(
      http.get('/api/v1/events/event-1/rsvps', () => HttpResponse.json({ data: [], meta })),
    );
    const result = await calendarService.getEventRSVPs('event-1');
    expect(result.data).toEqual([]);
  });

  it('getHolidays returns holidays', async () => {
    server.use(
      http.get('/api/v1/calendar/holidays', () => HttpResponse.json({ data: [holiday], meta })),
    );
    const result = await calendarService.getHolidays();
    expect(result.data).toHaveLength(1);
  });

  it('createHoliday posts holiday', async () => {
    server.use(
      http.post('/api/v1/calendar/holidays', () => HttpResponse.json({ data: holiday, meta })),
    );
    const result = await calendarService.createHoliday({
      name: 'New Year',
      start_date: '2025-01-01',
      end_date: '2025-01-01',
      type: 'national',
    });
    expect(result.data.name).toBe('New Year');
  });

  it('updateHoliday puts holiday', async () => {
    server.use(
      http.put('/api/v1/calendar/holidays/holiday-1', () =>
        HttpResponse.json({ data: { ...holiday, name: 'Updated Holiday' }, meta }),
      ),
    );
    const result = await calendarService.updateHoliday('holiday-1', {
      name: 'Updated Holiday',
      start_date: '2025-01-01',
      end_date: '2025-01-01',
      type: 'national',
    });
    expect(result.data.name).toBe('Updated Holiday');
  });

  it('deleteHoliday deletes holiday', async () => {
    server.use(
      http.delete('/api/v1/calendar/holidays/holiday-1', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await calendarService.deleteHoliday('holiday-1');
    expect(result).toBeDefined();
  });

  it('updateReminderPreferences posts preferences', async () => {
    server.use(
      http.post('/api/v1/events/reminder-preferences', () => HttpResponse.json({ data: [], meta })),
    );
    const result = await calendarService.updateReminderPreferences([]);
    expect(result.data).toEqual([]);
  });

  it('getICalFeed returns ical url', async () => {
    server.use(
      http.get('/api/v1/calendar/ical', () =>
        HttpResponse.json({ data: { url: 'https://example.com/cal.ics' }, meta }),
      ),
    );
    const result = await calendarService.getICalFeed();
    expect(result.data.url).toBeTruthy();
  });
});

// ── messagesService ───────────────────────────────────────────────────────────

describe('messagesService', () => {
  const conversation = {
    id: 'conv-1',
    school_id: 'school-1',
    type: 'direct',
    created_by: 'user-1',
    subject: null,
    participants: [],
    last_message_at: null,
    last_message_body: null,
    unread_count: 0,
    created_at: new Date().toISOString(),
  };

  const message = {
    id: 'msg-1',
    conversation_id: 'conv-1',
    sender_id: 'user-1',
    body: 'Hello',
    sent_at: new Date().toISOString(),
    edited_at: null,
    created_at: new Date().toISOString(),
  };

  it('listConversations returns conversations', async () => {
    server.use(
      http.get('/api/v1/messages/conversations', () =>
        HttpResponse.json({ data: [conversation], meta: listMeta }),
      ),
    );
    const result = await messagesService.listConversations({});
    expect(result.data).toHaveLength(1);
  });

  it('createConversation posts new conversation', async () => {
    server.use(
      http.post('/api/v1/messages/conversations', () =>
        HttpResponse.json({ data: conversation, meta }),
      ),
    );
    const result = await messagesService.createConversation({
      type: 'direct',
      participant_ids: ['user-2'],
      initial_message: 'Hi',
    });
    expect(result.data.id).toBe('conv-1');
  });

  it('listConversationMessages returns messages', async () => {
    server.use(
      http.get('/api/v1/messages/conversations/conv-1/messages', () =>
        HttpResponse.json({ data: [message], meta: listMeta }),
      ),
    );
    const result = await messagesService.listConversationMessages('conv-1', {});
    expect(result.data).toHaveLength(1);
  });

  it('markConversationRead posts read status', async () => {
    server.use(
      http.post('/api/v1/messages/conversations/conv-1/read', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await messagesService.markConversationRead('conv-1', 'msg-1');
    expect(result).toBeDefined();
  });

  it('listConversationReadStatus returns read status', async () => {
    server.use(
      http.get('/api/v1/messages/conversations/conv-1/read-status', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await messagesService.listConversationReadStatus('conv-1');
    expect(result.data).toEqual([]);
  });

  it('sendConversationMessage posts message', async () => {
    server.use(
      http.post('/api/v1/messages/conversations/conv-1/messages', () =>
        HttpResponse.json({ data: message, meta }),
      ),
    );
    const result = await messagesService.sendConversationMessage('conv-1', 'Hello');
    expect(result.data.body).toBe('Hello');
  });

  it('searchMessages returns search results', async () => {
    server.use(
      http.get('/api/v1/messages/search', () =>
        HttpResponse.json({ data: [message], meta: listMeta }),
      ),
    );
    const result = await messagesService.searchMessages('Hello');
    expect(result.data).toHaveLength(1);
  });
});

// ── announcementsService ──────────────────────────────────────────────────────

describe('announcementsService', () => {
  const announcement = {
    id: 'ann-1',
    school_id: 'school-1',
    author_id: 'user-1',
    title: 'Holiday Notice',
    body: 'School is closed.',
    target_roles: ['parent', 'student'],
    target_class_ids: [],
    published_at: null,
    status: 'draft',
    created_at: new Date().toISOString(),
    updated_at: null,
  };

  it('list returns announcements', async () => {
    server.use(
      http.get('/api/v1/announcements', () =>
        HttpResponse.json({ data: [announcement], meta: listMeta }),
      ),
    );
    const result = await announcementsService.list({ status: 'draft' });
    expect(result.data).toHaveLength(1);
  });

  it('create posts announcement', async () => {
    server.use(
      http.post('/api/v1/announcements', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await announcementsService.create({
      title: 'Holiday',
      body: 'Closed',
      target_roles: ['parent'],
    });
    expect(result).toBeDefined();
  });

  it('update puts announcement', async () => {
    server.use(
      http.put('/api/v1/announcements/ann-1', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await announcementsService.update('ann-1', {
      title: 'Updated',
      body: 'Updated body',
      target_roles: ['parent'],
    });
    expect(result).toBeDefined();
  });

  it('publish posts publish action', async () => {
    server.use(
      http.post('/api/v1/announcements/ann-1/publish', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await announcementsService.publish('ann-1');
    expect(result).toBeDefined();
  });
});

// ── notificationsService ──────────────────────────────────────────────────────

describe('notificationsService', () => {
  const notification = {
    id: 'notif-1',
    title: 'Assignment Due',
    body: 'You have an assignment due tomorrow.',
    category: 'academic',
    read: false,
    created_at: new Date().toISOString(),
  };

  it('list returns notifications', async () => {
    server.use(
      http.get('/api/v1/notifications', () =>
        HttpResponse.json({ data: [notification], meta: listMeta }),
      ),
    );
    const result = await notificationsService.list({});
    expect(result.data).toHaveLength(1);
  });

  it('markRead patches notification', async () => {
    server.use(
      http.patch('/api/v1/notifications/notif-1/read', () =>
        HttpResponse.json({ data: { ...notification, read: true }, meta }),
      ),
    );
    const result = await notificationsService.markRead('notif-1', true);
    expect(result.data.read).toBe(true);
  });

  it('markAllRead patches all', async () => {
    server.use(
      http.patch('/api/v1/notifications/mark-all-read', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await notificationsService.markAllRead();
    expect(result).toBeDefined();
  });

  it('getPreferences returns preferences', async () => {
    server.use(
      http.get('/api/v1/notifications/preferences', () =>
        HttpResponse.json({ data: { preferences: [] }, meta }),
      ),
    );
    const result = await notificationsService.getPreferences();
    expect(result.data).toBeDefined();
  });

  it('updatePreferences posts preferences', async () => {
    server.use(
      http.post('/api/v1/notifications/preferences', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await notificationsService.updatePreferences([]);
    expect(result).toBeDefined();
  });

  it('updateNotificationPreferences puts preferences', async () => {
    server.use(
      http.put('/api/v1/notifications/preferences', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await notificationsService.updateNotificationPreferences({ preferences: [] });
    expect(result).toBeDefined();
  });

  it('getDigestPreferences returns digest prefs', async () => {
    server.use(
      http.get('/api/v1/notifications/digest/preferences', () =>
        HttpResponse.json({ data: { digest_frequency: 'daily' }, meta }),
      ),
    );
    const result = await notificationsService.getDigestPreferences();
    expect(result.data).toBeDefined();
  });

  it('updateDigestPreferences posts digest preferences', async () => {
    server.use(
      http.post('/api/v1/notifications/digest/preferences', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await notificationsService.updateDigestPreferences('weekly');
    expect(result).toBeDefined();
  });

  it('listConsents returns consents', async () => {
    server.use(http.get('/api/v1/consents', () => HttpResponse.json({ data: [], meta })));
    const result = await notificationsService.listConsents();
    expect(result.data).toEqual([]);
  });

  it('listDevices returns devices', async () => {
    server.use(http.get('/api/v1/devices', () => HttpResponse.json({ data: [], meta: listMeta })));
    const result = await notificationsService.listDevices();
    expect(result.data).toEqual([]);
  });

  it('removeDevice deletes device', async () => {
    server.use(
      http.delete('/api/v1/devices/device-1', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await notificationsService.removeDevice('device-1');
    expect(result).toBeDefined();
  });

  it('registerDevice posts device registration', async () => {
    server.use(
      http.post('/api/v1/devices/register', () =>
        HttpResponse.json({ data: { id: 'device-2', token: 'tok', platform: 'web' }, meta }),
      ),
    );
    const result = await notificationsService.registerDevice({ token: 'tok', platform: 'web' });
    expect(result.data).toBeDefined();
  });

  it('getUnreadCount returns count', async () => {
    server.use(
      http.get('/api/v1/notifications/unread-count', () =>
        HttpResponse.json({ data: { count: 3 }, meta }),
      ),
    );
    const result = await notificationsService.getUnreadCount();
    expect(result.data.count).toBe(3);
  });

  it('batchNotify posts batch notification', async () => {
    server.use(
      http.post('/api/v1/notifications/batch', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await notificationsService.batchNotify({
      user_ids: ['user-1'],
      title: 'Alert',
      body: 'Message',
    });
    expect(result).toBeDefined();
  });

  it('deleteNotification deletes a notification', async () => {
    server.use(
      http.delete('/api/v1/notifications/notif-1', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await notificationsService.deleteNotification('notif-1');
    expect(result).toBeDefined();
  });
});
