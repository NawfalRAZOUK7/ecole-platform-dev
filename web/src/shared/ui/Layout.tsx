/**
 * Main application layout — sidebar navigation + topbar bell/dropdown.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { adminQueryKeys } from '@/features/admin/useAdmin';
import { adminService } from '@/features/admin/admin.service';
import { invoicesQueryKeys } from '@/features/invoices/useInvoices';
import { invoicesService } from '@/features/invoices/invoices.service';
import { notificationQueryKeys } from '@/features/notifications/useNotifications';
import { notificationsService } from '@/features/notifications/notifications.service';
import { useFeedUnreadSummary } from '@/features/feed/useFeed';
import { useSyncDevices, useSyncHealth, useSyncStatus } from '@/features/sync/useSync';
import { useFocusManagement } from '@/shared/hooks/useFocusManagement';
import { useTheme } from '@/shared/hooks/useTheme';
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
  {
    to: '/admin/generate-invoices',
    labelKey: 'nav.adminGenerateInvoices',
    icon: '🧾',
    roles: ['ADM'],
  },
  {
    to: '/billing/sibling-policy',
    labelKey: 'nav.billingSiblingPolicy',
    icon: '👨‍👩‍👧',
    roles: ['ADM'],
  },
  { to: '/billing/late-fees', labelKey: 'nav.billingLateFees', icon: '⏰', roles: ['ADM'] },
  {
    to: '/billing/payment-plans',
    labelKey: 'nav.billingPaymentPlans',
    icon: '📅',
    roles: ['ADM', 'DIR', 'PAR'],
  },
  { to: '/budgets', labelKey: 'nav.budgets', icon: '💼', roles: ['ADM', 'DIR'] },
  { to: '/financial-health', labelKey: 'nav.financialHealth', icon: '💹', roles: ['ADM', 'SYS'] },
  { to: '/micro-schools', labelKey: 'nav.microSchools', icon: '🏠', roles: ['ADM', 'DIR', 'PAR'] },
  { to: '/teacher', labelKey: 'nav.teacherClasses', icon: '🏫', roles: ['TCH'] },
  { to: '/teacher/courses', labelKey: 'nav.teacherCourses', icon: '📖', roles: ['TCH'] },
  { to: '/teacher/assignments', labelKey: 'nav.teacherAssignments', icon: '📝', roles: ['TCH'] },
  { to: '/teacher/submissions', labelKey: 'nav.teacherSubmissions', icon: '📄', roles: ['TCH'] },
  { to: '/teacher/attendance', labelKey: 'nav.teacherAttendance', icon: '✅', roles: ['TCH'] },
  { to: '/teacher/assessments', labelKey: 'nav.teacherAssessments', icon: '📊', roles: ['TCH'] },
  {
    to: '/teacher/content-library',
    labelKey: 'nav.teacherContentLibrary',
    icon: '📚',
    roles: ['TCH'],
  },
  { to: '/teacher/games', labelKey: 'nav.games', icon: '🎮', roles: ['TCH', 'ADM'] },
  { to: '/teacher/quizzes', labelKey: 'nav.teacherQuizzes', icon: '❓', roles: ['TCH'] },
  { to: '/rubrics', labelKey: 'nav.rubrics', icon: '📊', roles: ['TCH'] },
  { to: '/question-bank', labelKey: 'nav.questionBank', icon: '🗃️', roles: ['TCH', 'CONTENT_MGR'] },
  {
    to: '/teacher/class-progress',
    labelKey: 'nav.teacherClassProgress',
    icon: '📊',
    roles: ['TCH'],
  },
  { to: '/student/content', labelKey: 'nav.studentContent', icon: '📚', roles: ['STD'] },
  { to: '/student/quizzes', labelKey: 'nav.studentQuizzes', icon: '❓', roles: ['STD'] },
  { to: '/rewards', labelKey: 'nav.myRewards', icon: '⭐', roles: ['STD'] },
  { to: '/feed', labelKey: 'nav.feed', icon: '📰', roles: ['PAR'] },
  {
    to: '/rewards',
    labelKey: 'nav.rewards',
    icon: '⭐',
    roles: ['PAR', 'TCH', 'ADM', 'DIR', 'SUP', 'SYS'],
  },
  {
    to: '/timetable',
    labelKey: 'nav.timetable',
    icon: '📅',
    roles: ['ADM', 'DIR', 'TCH', 'STD', 'PAR'],
  },
  {
    to: '/timetable/constraints',
    labelKey: 'nav.timetableConstraints',
    icon: '⚙️',
    roles: ['ADM', 'DIR'],
  },
  {
    to: '/timetable/generate',
    labelKey: 'nav.timetableGenerate',
    icon: '✨',
    roles: ['ADM', 'DIR'],
  },
  {
    to: '/calendar',
    labelKey: 'nav.calendar',
    icon: '🗓️',
    roles: ['ADM', 'DIR', 'TCH', 'STD', 'PAR'],
  },
  { to: '/calendar/holidays', labelKey: 'nav.calendarHolidays', icon: '🏖️', roles: ['ADM', 'DIR'] },
  { to: '/messages', labelKey: 'nav.messages', icon: '💬', roles: ['PAR', 'TCH', 'ADM', 'DIR'] },
  {
    to: '/announcements',
    labelKey: 'nav.announcements',
    icon: '📢',
    roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'],
  },
  {
    to: '/notifications',
    labelKey: 'nav.notifications',
    icon: '🔔',
    roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'],
  },
  {
    to: '/reports',
    labelKey: 'nav.reports',
    icon: '🧾',
    roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'],
  },
  {
    to: '/documents',
    labelKey: 'nav.documents',
    icon: '🗂️',
    roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'],
  },
  {
    to: '/settings/notifications',
    labelKey: 'nav.notificationSettings',
    icon: '⚡',
    roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'],
  },
  { to: '/content', labelKey: 'nav.content', icon: '📚', roles: ['STD', 'PAR', 'TCH', 'ADM'] },
  { to: '/submissions', labelKey: 'nav.submissions', icon: '📤', roles: ['STD'] },
  { to: '/results', labelKey: 'nav.results', icon: '📊', roles: ['STD', 'PAR'] },
  { to: '/progress', labelKey: 'nav.progress', icon: '📈', roles: ['STD'] },
  { to: '/parent/progress', labelKey: 'nav.parentProgress', icon: '📈', roles: ['PAR'] },
  { to: '/justification', labelKey: 'nav.justification', icon: '📋', roles: ['PAR'] },
  { to: '/invoices', labelKey: 'nav.invoices', icon: '💳', roles: ['PAR', 'ADM'] },
  { to: '/activities', labelKey: 'nav.activities', icon: '🎯', roles: ['STD', 'TCH', 'ADM'] },
  { to: '/skills', labelKey: 'nav.skills', icon: '🧠', roles: ['TCH', 'DIR', 'PAR', 'STD'] },
  { to: '/compliance', labelKey: 'nav.compliance', icon: '📐', roles: ['ADM', 'DIR'] },
  {
    to: '/profile',
    labelKey: 'nav.profile',
    icon: '👤',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP'],
  },
  {
    to: '/profile/sessions',
    labelKey: 'nav.sessions',
    icon: '🔒',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP'],
  },
  {
    to: '/profile/2fa',
    labelKey: 'nav.twoFactor',
    icon: '🛡️',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP'],
  },
  {
    to: '/profile/login-history',
    labelKey: 'nav.loginHistory',
    icon: '🕐',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP'],
  },
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
  const navRef = useRef<HTMLElement>(null);
  const { theme, toggleTheme } = useTheme();
  const userRole = user?.role || '';
  const feedUnreadSummary = useFeedUnreadSummary(userRole === 'PAR');
  const { unreadCount: feedUnreadCount, refetch: refetchFeedUnread } = feedUnreadSummary;
  const syncEnabled = userRole === 'ADM' || userRole === 'DIR';
  const syncDevicesQuery = useSyncDevices(syncEnabled);
  const primarySyncDeviceId = syncDevicesQuery.data?.[0]?.id ?? '';
  const syncStatusQuery = useSyncStatus(primarySyncDeviceId, syncEnabled);
  const syncHealthQuery = useSyncHealth(primarySyncDeviceId, syncEnabled);

  const queryClient = useQueryClient();

  const handleNavPrefetch = useCallback(
    (to: string) => {
      if (to === '/admin') {
        void queryClient.prefetchQuery({
          queryKey: adminQueryKeys.dashboard(),
          queryFn: () => adminService.getDashboard().then((r) => r.data),
          staleTime: 5 * 60 * 1000,
        });
      } else if (to === '/invoices') {
        void queryClient.prefetchQuery({
          queryKey: invoicesQueryKeys.list({}),
          queryFn: () => invoicesService.listInvoices({}).then((r) => r.data),
          staleTime: 5 * 60 * 1000,
        });
      } else if (to === '/notifications') {
        void queryClient.prefetchQuery({
          queryKey: notificationQueryKeys.list({}),
          queryFn: () => notificationsService.list({}).then((r) => r.data),
          staleTime: 5 * 60 * 1000,
        });
      } else if (to === '/attendance' || to === '/gradebook') {
        // These pages depend on dynamic classId; prefetch is skipped as params unknown
      }
    },
    [queryClient],
  );

  useFocusManagement();
  const visibleItems = useMemo(
    () => NAV_ITEMS.filter((item) => item.roles.includes(userRole)),
    [userRole],
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
      if (eventName === 'feed_new') {
        if (userRole === 'PAR') {
          void refetchFeedUnread();
        }
        addToast(t('feed.realtimeNewItem'));
      }
    });
    return () => {
      unsubscribe();
      wsClient.disconnect();
    };
  }, [addToast, fetchNotificationSummary, refetchFeedUnread, t, userRole]);

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

  function handleSidebarKeyDown(event: React.KeyboardEvent<HTMLElement>) {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') {
      return;
    }

    const links = Array.from(
      navRef.current?.querySelectorAll<HTMLAnchorElement>('a.nav-link') ?? [],
    );
    if (links.length === 0) {
      return;
    }

    const currentIndex = links.findIndex((link) => link === document.activeElement);
    const fallbackIndex = currentIndex === -1 ? 0 : currentIndex;
    const nextIndex =
      event.key === 'ArrowDown'
        ? (fallbackIndex + 1) % links.length
        : (fallbackIndex - 1 + links.length) % links.length;

    event.preventDefault();
    links[nextIndex]?.focus();
  }

  return (
    <div className="app-layout">
      <a href="#main-content" className="skip-link">
        {t('a11y.skipToContent', { defaultValue: 'Skip to content' })}
      </a>
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">{t('app.name')}</h2>
          <div className="sidebar-header__controls">
            <LanguageSwitcher />
            <button
              type="button"
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label={t('theme.toggle', { defaultValue: 'Toggle dark mode' })}
            >
              {theme === 'dark' ? (
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 4a1 1 0 0 1 1 1v1.2a1 1 0 0 1-2 0V5a1 1 0 0 1 1-1Zm0 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7-5a1 1 0 0 1 0 2h-1.2a1 1 0 0 1 0-2H19ZM7.2 12a1 1 0 0 1-1 1H5a1 1 0 1 1 0-2h1.2a1 1 0 0 1 1 1Zm8.94 5.54a1 1 0 0 1 1.41 0l.85.85a1 1 0 0 1-1.41 1.41l-.85-.85a1 1 0 0 1 0-1.41ZM6.46 7.86a1 1 0 0 1 1.41 0l.85.85a1 1 0 1 1-1.41 1.41l-.85-.85a1 1 0 0 1 0-1.41Zm10.68 0a1 1 0 0 1 0 1.41l-.85.85a1 1 0 0 1-1.41-1.41l.85-.85a1 1 0 0 1 1.41 0ZM7.87 16.13a1 1 0 0 1 0 1.41l-.85.85a1 1 0 0 1-1.41-1.41l.85-.85a1 1 0 0 1 1.41 0ZM12 17.8a1 1 0 0 1 1 1V20a1 1 0 0 1-2 0v-1.2a1 1 0 0 1 1-1Z" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M14.94 3.78a1 1 0 0 1 .65 1.57 8 8 0 1 0 3.06 11.4 1 1 0 0 1 1.77.92A10 10 0 1 1 14.3 3.9a1 1 0 0 1 .64-.12Z" />
                </svg>
              )}
            </button>
          </div>
        </div>

        <nav
          ref={navRef}
          className="sidebar-nav"
          role="navigation"
          aria-label={t('a11y.mainNavigation', { defaultValue: 'Main navigation' })}
          onKeyDown={handleSidebarKeyDown}
        >
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}
              aria-label={t(item.labelKey)}
              onMouseEnter={() => handleNavPrefetch(item.to)}
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
              {item.to === '/feed' && feedUnreadCount > 0 && (
                <span className="notif-badge">
                  {feedUnreadCount > 99 ? '99+' : feedUnreadCount}
                </span>
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

      <main id="main-content" className="app-main">
        <div className="app-topbar">
          <div />
          <div className="topbar-actions">
            {syncEnabled && primarySyncDeviceId ? (
              <button
                type="button"
                className="bell-button"
                onClick={() => navigate('/sync')}
                aria-label={t('sync.title')}
              >
                <span
                  className="bell-button__icon"
                  style={{
                    color:
                      (syncStatusQuery.data?.conflict_count ??
                        syncHealthQuery.data?.conflict_count ??
                        0) > 0
                        ? 'var(--color-error)'
                        : (syncStatusQuery.data?.pending_count ?? 0) > 0
                          ? 'var(--color-warning)'
                          : 'var(--color-success)',
                  }}
                >
                  ⟳
                </span>
              </button>
            ) : null}
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
                    <div className="notification-dropdown__empty">{t('app.loading')}</div>
                  ) : recentNotifications.length === 0 ? (
                    <div className="notification-dropdown__empty">{t('notifications.empty')}</div>
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
