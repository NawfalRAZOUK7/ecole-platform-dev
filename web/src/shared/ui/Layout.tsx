/**
 * Main application layout — sidebar navigation + content area.
 *
 * Reference: S-083 — Layout with role-based navigation
 * Shows navigation items based on user role (PAR, STD, TCH, ADM).
 */

import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';

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
  { to: '/admin/settings', labelKey: 'nav.adminSettings', icon: '🏫', roles: ['ADM'] },
  { to: '/teacher', labelKey: 'nav.teacherClasses', icon: '🏫', roles: ['TCH'] },
  { to: '/teacher/courses', labelKey: 'nav.teacherCourses', icon: '📖', roles: ['TCH'] },
  { to: '/teacher/assignments', labelKey: 'nav.teacherAssignments', icon: '📝', roles: ['TCH'] },
  { to: '/teacher/submissions', labelKey: 'nav.teacherSubmissions', icon: '📄', roles: ['TCH'] },
  { to: '/teacher/attendance', labelKey: 'nav.teacherAttendance', icon: '✅', roles: ['TCH'] },
  { to: '/teacher/assessments', labelKey: 'nav.teacherAssessments', icon: '📊', roles: ['TCH'] },
  { to: '/feed', labelKey: 'nav.feed', icon: '📰', roles: ['PAR'] },
  { to: '/notifications', labelKey: 'nav.notifications', icon: '🔔', roles: ['PAR', 'TCH', 'ADM', 'DIR'] },
  { to: '/content', labelKey: 'nav.content', icon: '📚', roles: ['STD', 'PAR', 'TCH', 'ADM'] },
  { to: '/results', labelKey: 'nav.results', icon: '📊', roles: ['STD', 'PAR'] },
  { to: '/invoices', labelKey: 'nav.invoices', icon: '💳', roles: ['PAR', 'ADM'] },
  { to: '/activities', labelKey: 'nav.activities', icon: '🎯', roles: ['STD', 'TCH', 'ADM'] },
  { to: '/profile', labelKey: 'nav.profile', icon: '👤', roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP'] },
];

export function Layout() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const userRole = user?.role || '';
  const visibleItems = NAV_ITEMS.filter((item) => item.roles.includes(userRole));

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
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{t(item.labelKey)}</span>
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
    </div>
  );
}
