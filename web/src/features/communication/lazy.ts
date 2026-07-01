import { lazy } from 'react';

export const NotificationsPage = lazy(() =>
  import('./notifications/ui/NotificationsPage').then((m) => ({ default: m.NotificationsPage })),
);
export const NotificationSettingsPage = lazy(() =>
  import('./notifications/ui/NotificationSettingsPage').then((m) => ({
    default: m.NotificationSettingsPage,
  })),
);

export const CalendarPage = lazy(() =>
  import('./calendar/ui/CalendarPage').then((m) => ({ default: m.CalendarPage })),
);
export const EventDetailPage = lazy(() =>
  import('./calendar/ui/EventDetailPage').then((m) => ({ default: m.EventDetailPage })),
);
export const HolidayManagerPage = lazy(() =>
  import('./calendar/ui/HolidayManagerPage').then((m) => ({ default: m.HolidayManagerPage })),
);

export const ConversationsPage = lazy(() =>
  import('./messages/ui/ConversationsPage').then((m) => ({ default: m.ConversationsPage })),
);
export const ChatPage = lazy(() =>
  import('./messages/ui/ChatPage').then((m) => ({ default: m.ChatPage })),
);

export const AnnouncementsPage = lazy(() =>
  import('./announcements/ui/AnnouncementsPage').then((m) => ({ default: m.AnnouncementsPage })),
);
