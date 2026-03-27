/**
 * Main application layout — sidebar navigation + topbar bell/dropdown.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import { formatDate } from '@/shared/i18n';
import { wsClient, type WsEvent } from '@/services/ws/WebSocketClient';

interface NavItem {
  to: string;
  labelKey: string;
  icon: string;
  roles: string[];
}

interface NotificationPreview {
  id: string;
  title: string;
  body: string | null;
  category: string;
  created_at: string;
  action_url: string | null;
  is_read: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/admin', labelKey: 'nav.adminDashboard', icon: '⚙️', roles: ['ADM', 'DIR'] },
  { to: '/admin/users', labelKey: 'nav.adminUsers', icon: '👥', roles: ['ADM', 'DIR'] },
  { to: '/admin/invitations', labelKey: 'nav.adminInvitations', icon: '🎟️', roles: ['ADM'] },
  { to: '/admin/audit', labelKey: 'nav.adminAudit', icon: '📋', roles: ['ADM', 'DIR'] },
  { to: '/admin/justifications', labelKey: 'nav.adminJustifications', icon: '📝', roles: ['ADM'] },
  { to: '/analytics', labelKey: 'nav.adminAnalytics', icon: '📈', roles: ['ADM', 'DIR'] },
  { to: '/admin/batch-register', labelKey: 'nav.adminBatchRegister', icon: '📋', roles: ['ADM'] },
  { to: '/admin/family-links', labelKey: 'nav.adminFamilyLinks', icon: '👨‍👩‍👧', roles: ['ADM'] },
  { to: '/admin/settings', labelKey: 'nav.adminSettings', icon: '🏫', roles: ['ADM'] },
  { to: '/admin/fee-structures', labelKey: 'nav.adminFeeStructures', icon: '💰', roles: ['ADM'] },
  { to: '/admin/fee-assignments', labelKey: 'nav.adminFeeAssignments', icon: '📋', roles: ['ADM'] },
  { to: '/admin/generate-invoices', labelKey: 'nav.adminGenerateInvoices', icon: '🧾', roles: ['ADM'] },
  { to: '/teacher', labelKey: 'nav.teacherClasses', icon: '🏫', roles: ['TCH'] },
  { to: '/teacher/courses', labelKey: 'nav.teacherCourses', icon: '📖', roles: ['TCH'] },
  { to: '/teacher/assignments', labelKey: 'nav.teacherAssignments', icon: '📝', roles: ['TCH'] },
  { to: '/teacher/submissions', labelKey: 'nav.teacherSubmissions', icon: '📄', roles: ['TCH'] },
  { to: '/teacher/attendance', labelKey: 'nav.teacherAttendance', icon: '✅', roles: ['TCH'] },
  { to: '/teacher/assessments', labelKey: 'nav.teacherAssessments', icon: '📊', roles: ['TCH'] },
  { to: '/teacher/content-library', labelKey: 'nav.teacherContentLibrary', icon: '📚', roles: ['TCH'] },
  { to: '/teacher/quizzes', labelKey: 'nav.teacherQuizzes', icon: '❓', roles: ['TCH'] },
  { to: '/teacher/class-progress', labelKey: 'nav.teacherClassProgress', icon: '📊', roles: ['TCH'] },
  { to: '/student/content', labelKey: 'nav.studentContent', icon: '📚', roles: ['STD'] },
  { to: '/student/quizzes', labelKey: 'nav.studentQuizzes', icon: '❓', roles: ['STD'] },
  { to: '/feed', labelKey: 'nav.feed', icon: '📰', roles: ['PAR'] },
  { to: '/timetable', labelKey: 'nav.timetable', icon: '📅', roles: ['ADM', 'DIR', 'TCH', 'STD', 'PAR'] },
  { to: '/calendar', labelKey: 'nav.calendar', icon: '🗓️', roles: ['ADM', 'DIR', 'TCH', 'STD', 'PAR'] },
  { to: '/messages', labelKey: 'nav.messages', icon: '💬', roles: ['PAR', 'TCH', 'ADM', 'DIR'] },
  { to: '/announcements', labelKey: 'nav.announcements', icon: '📢', roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'] },
  { to: '/notifications', labelKey: 'nav.notifications', icon: '🔔', roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'] },
  { to: '/reports', labelKey: 'nav.reports', icon: '🧾', roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'] },
  { to: '/documents', labelKey: 'nav.documents', icon: '🗂️', roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'] },
  { to: '/settings/notifications', labelKey: 'nav.notificationSettings', icon: '⚡', roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'] },
  { to: '/content', labelKey: 'nav.content', icon: '📚', roles: ['STD', 'PAR', 'TCH', 'ADM'] },
  { to: '/submissions', labelKey: 'nav.submissions', icon: '📤', roles: ['STD'] },
  { to: '/results', labelKey: 'nav.results', icon: '📊', roles: ['STD', 'PAR'] },
  { to: '/progress', labelKey: 'nav.progress', icon: '📈', roles: ['STD'] },
  { to: '/parent/progress', labelKey: 'nav.parentProgress', icon: '📈', roles: ['PAR'] },
  { to: '/justification', labelKey: 'nav.justification', icon: '📋', roles: ['PAR'] },
  { to: '/invoices', labelKey: 'nav.invoices', icon: '💳', roles: ['PAR', 'ADM'] },
  { to: '/activities', labelKey: 'nav.activities', icon: '🎯', roles: ['STD', 'TCH', 'ADM'] },
  { to: '/profile', labelKey: 'nav.profile', icon: '👤', roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP'] },
  { to: '/profile/sessions', labelKey: 'nav.sessions', icon: '🔒', roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP'] },
  { to: '/profile/2fa', labelKey: 'nav.twoFactor', icon: '🛡️', roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP'] },
];

interface Toast {
  id: number;
  message: string;
}

let toastIdCounter = 0;

function normalizeWsEvent(eventName: string): string {
  return eventName.replace(/:/g, '_');
}

export function Layout() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [notifCount, setNotifCount] = useState(0);
  const [msgCount, setMsgCount] = useState(0);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [dropdownLoading, setDropdownLoading] = useState(false);
  const [recentNotifications, setRecentNotifications] = useState<NotificationPreview[]>([]);

  const userRole = user?.role || '';
  const visibleItems = useMemo(
    () => NAV_ITEMS.filter((item) => item.roles.includes(userRole)),
    [userRole]
  );

  const addToast = useCallback((message: string) => {
    const id = ++toastIdCounter;
    setToasts((prev) => [...prev, { id, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 5000);
  }, []);

  const fetchNotificationSummary = useCallback(async () => {
    if (!user) return;
    setDropdownLoading(true);
    try {
      const [countResp, listResp] = await Promise.all([
        api.get<{ unread_count: number }>('/notifications/unread-count'),
        api.list<NotificationPreview>('/notifications', { read: 'false', limit: 5 }),
      ]);
      setNotifCount(countResp.data.unread_count);
      setRecentNotifications(listResp.data);
    } catch {
      // Keep current UI state; page-level components handle full errors.
    } finally {
      setDropdownLoading(false);
    }
  }, [user]);

  useEffect(() => {
    void fetchNotificationSummary();
    const timer = window.setInterval(() => {
      void fetchNotificationSummary();
    }, 60000);
    return () => window.clearInterval(timer);
  }, [fetchNotificationSummary]);

  useEffect(() => {
    setDropdownOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    wsClient.connect();
    const unsubscribe = wsClient.subscribe((event: WsEvent) => {
      const eventName = normalizeWsEvent(event.event);
      if (eventName === 'notification_created') {
        void fetchNotificationSummary();
        const title = (event.data.title as string) || t('notifications.title');
        addToast(title);
      }
      if (eventName === 'grade_published') {
        addToast(t('ws.gradePublished'));
      }
      if (eventName === 'payment_updated') {
        addToast(t('ws.paymentUpdated'));
      }
      if (eventName === 'message_created') {
        setMsgCount((count) => count + 1);
        addToast(t('ws.newMessage'));
      }
      if (eventName === 'announcement_published') {
        addToast(t('ws.announcementPublished'));
      }
    });
    return () => {
      unsubscribe();
      wsClient.disconnect();
    };
  }, [addToast, fetchNotificationSummary, t]);

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  async function handleMarkAsRead(notification: NotificationPreview) {
    await api.patch(`/notifications/${notification.id}/read`, { read: true });
    await fetchNotificationSummary();
  }

  async function handleOpenNotification(notification: NotificationPreview) {
    if (!notification.is_read) {
      await handleMarkAsRead(notification);
    }
    navigate(notification.action_url || '/notifications');
  }

  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">{t('app.name')}</h2>
          <LanguageSwitcher />
        </div>

        <nav className="sidebar-nav">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}
              onClick={() => {
                if (item.to === '/messages') setMsgCount(0);
              }}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{t(item.labelKey)}</span>
              {item.to === '/notifications' && notifCount > 0 && (
                <span className="notif-badge">{notifCount > 99 ? '99+' : notifCount}</span>
              )}
              {item.to === '/messages' && msgCount > 0 && (
                <span className="notif-badge">{msgCount > 99 ? '99+' : msgCount}</span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-name">{user?.full_name}</span>
            <span className="user-role">{t(`roles.${userRole}`, userRole)}</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            {t('nav.logout')}
          </button>
        </div>
      </aside>

      <main className="app-main">
        <div className="app-topbar">
          <div />
          <div className="topbar-actions">
            <div className="notification-menu">
              <button
                type="button"
                className="bell-button"
                onClick={() => {
                  setDropdownOpen((open) => !open);
                  if (!dropdownOpen) {
                    void fetchNotificationSummary();
                  }
                }}
                aria-label={t('notifications.bellLabel')}
              >
                <span className="bell-button__icon">🔔</span>
                {notifCount > 0 && (
                  <span className="notif-badge bell-button__badge">
                    {notifCount > 99 ? '99+' : notifCount}
                  </span>
                )}
              </button>

              {dropdownOpen && (
                <div className="notification-dropdown">
                  <div className="notification-dropdown__header">
                    <strong>{t('notifications.quickViewTitle')}</strong>
                    <button
                      type="button"
                      className="dropdown-link"
                      onClick={() => navigate('/notifications')}
                    >
                      {t('notifications.viewAll')}
                    </button>
                  </div>

                  {dropdownLoading ? (
                    <div className="notification-dropdown__empty">
                      {t('app.loading')}
                    </div>
                  ) : recentNotifications.length === 0 ? (
                    <div className="notification-dropdown__empty">
                      {t('notifications.empty')}
                    </div>
                  ) : (
                    <div className="notification-dropdown__list">
                      {recentNotifications.map((notification) => (
                        <div
                          key={notification.id}
                          className="notification-dropdown__item"
                          role="button"
                          tabIndex={0}
                          onClick={() => void handleOpenNotification(notification)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault();
                              void handleOpenNotification(notification);
                            }
                          }}
                        >
                          <span className="notification-dropdown__meta">
                            <span className="notification-category-badge">
                              {t(`notifications.categories.${notification.category}`)}
                            </span>
                            <time>
                              {formatDate(notification.created_at, i18n.language, {
                                dateStyle: 'short',
                                timeStyle: 'short',
                              })}
                            </time>
                          </span>
                          <strong>{notification.title}</strong>
                          {notification.body && <span>{notification.body}</span>}
                          {!notification.is_read && (
                            <span className="notification-dropdown__actions">
                              <button
                                type="button"
                                className="dropdown-link"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  void handleMarkAsRead(notification);
                                }}
                              >
                                {t('notifications.markRead')}
                              </button>
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="notification-dropdown__footer">
                    <button
                      type="button"
                      className="dropdown-link"
                      onClick={() => navigate('/settings/notifications')}
                    >
                      {t('notifications.manageSettings')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <Outlet />
      </main>

      {toasts.length > 0 && (
        <div className="toast-container">
          {toasts.map((toast) => (
            <div key={toast.id} className="toast">
              <span>{toast.message}</span>
              <button
                className="toast-close"
                onClick={() => setToasts((prev) => prev.filter((item) => item.id !== toast.id))}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
