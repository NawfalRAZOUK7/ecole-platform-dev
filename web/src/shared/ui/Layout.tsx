/**
 * Main application layout — sidebar navigation + content area.
 *
 * Reference: S-083 — Layout with role-based navigation
 * Shows navigation items based on user role (PAR, STD, TCH, ADM).
 */

import { useCallback, useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import { wsClient, type WsEvent } from '@/services/ws/WebSocketClient';

interface NavItem {
  to: string;
  labelKey: string;
  icon: string;
  roles: string[];
}

const NAV_ITEMS: NavItem[] = [
  { to: '/admin', labelKey: 'nav.adminDashboard', icon: '⚙️', roles: ['ADM', 'DIR'] },
  { to: '/admin/users', labelKey: 'nav.adminUsers', icon: '👥', roles: ['ADM', 'DIR'] },
  { to: '/admin/invitations', labelKey: 'nav.adminInvitations', icon: '🎟️', roles: ['ADM'] },
  { to: '/admin/audit', labelKey: 'nav.adminAudit', icon: '📋', roles: ['ADM', 'DIR'] },
  { to: '/admin/justifications', labelKey: 'nav.adminJustifications', icon: '📝', roles: ['ADM'] },
  { to: '/admin/analytics', labelKey: 'nav.adminAnalytics', icon: '📈', roles: ['ADM', 'DIR'] },
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
  { to: '/student/content', labelKey: 'nav.studentContent', icon: '📚', roles: ['STD'] },
  { to: '/student/quizzes', labelKey: 'nav.studentQuizzes', icon: '❓', roles: ['STD'] },
  { to: '/feed', labelKey: 'nav.feed', icon: '📰', roles: ['PAR'] },
  { to: '/timetable', labelKey: 'nav.timetable', icon: '📅', roles: ['ADM', 'DIR', 'TCH', 'STD', 'PAR'] },
  { to: '/messages', labelKey: 'nav.messages', icon: '💬', roles: ['PAR', 'TCH', 'ADM', 'DIR'] },
  { to: '/announcements', labelKey: 'nav.announcements', icon: '📢', roles: ['PAR', 'TCH', 'ADM', 'DIR', 'STD'] },
  { to: '/notifications', labelKey: 'nav.notifications', icon: '🔔', roles: ['PAR', 'TCH', 'ADM', 'DIR'] },
  { to: '/content', labelKey: 'nav.content', icon: '📚', roles: ['STD', 'PAR', 'TCH', 'ADM'] },
  { to: '/submissions', labelKey: 'nav.submissions', icon: '📤', roles: ['STD'] },
  { to: '/results', labelKey: 'nav.results', icon: '📊', roles: ['STD', 'PAR'] },
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

export function Layout() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [notifCount, setNotifCount] = useState(0);
  const [msgCount, setMsgCount] = useState(0);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const userRole = user?.role || '';
  const visibleItems = NAV_ITEMS.filter((item) => item.roles.includes(userRole));

  const addToast = useCallback((message: string) => {
    const id = ++toastIdCounter;
    setToasts((prev) => [...prev, { id, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  // WebSocket connect/disconnect on mount/unmount
  useEffect(() => {
    wsClient.connect();
    const unsub = wsClient.subscribe((event: WsEvent) => {
      if (event.event === 'notification_created') {
        setNotifCount((c) => c + 1);
        const subject = (event.data.subject as string) || t('notifications.title');
        addToast(subject);
      }
      if (event.event === 'grade_published') {
        addToast(t('ws.gradePublished'));
      }
      if (event.event === 'payment_updated') {
        addToast(t('ws.paymentUpdated'));
      }
      if (event.event === 'message_created' || (event.event === 'notification_created' && event.data.event_type === 'message_created')) {
        setMsgCount((c) => c + 1);
        addToast(t('ws.newMessage'));
      }
      if (event.event === 'announcement_published' || (event.event === 'notification_created' && event.data.event_type === 'announcement_published')) {
        addToast(t('ws.announcementPublished'));
      }
    });
    return () => {
      unsub();
      wsClient.disconnect();
    };
  }, [addToast, t]);

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
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
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
              onClick={() => {
                if (item.to === '/notifications') setNotifCount(0);
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

      {/* Main content */}
      <main className="app-main">
        <Outlet />
      </main>

      {/* Toast notifications */}
      {toasts.length > 0 && (
        <div className="toast-container">
          {toasts.map((toast) => (
            <div key={toast.id} className="toast">
              <span>{toast.message}</span>
              <button
                className="toast-close"
                onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
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
