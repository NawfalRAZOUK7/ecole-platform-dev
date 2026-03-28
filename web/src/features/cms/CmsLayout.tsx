import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import { useCmsPendingSubmissionBadge } from './useCms';

interface CmsNavItem {
  to: string;
  labelKey: string;
  icon: string;
  badge?: number;
}

export function CmsLayout() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const pendingSubmissionBadgeQuery = useCmsPendingSubmissionBadge();
  const pendingCount = pendingSubmissionBadgeQuery.data ?? 0;

  const navItems: CmsNavItem[] = [
    { to: '/cms', labelKey: 'cms.nav.content', icon: '\uD83D\uDCDA' },
    { to: '/cms/upload', labelKey: 'cms.nav.upload', icon: '\uD83D\uDCE4' },
    { to: '/cms/review', labelKey: 'cms.nav.review', icon: '\uD83D\uDCCB', badge: pendingCount },
    { to: '/cms/quizzes', labelKey: 'cms.nav.quizzes', icon: '\u2753' },
    { to: '/cms/analytics', labelKey: 'cms.nav.analytics', icon: '\uD83D\uDCC8' },
  ];

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">{t('cms.title')}</h2>
          <LanguageSwitcher />
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/cms'}
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{t(item.labelKey)}</span>
              {item.badge != null && item.badge > 0 ? (
                <span className="notif-badge">{item.badge > 99 ? '99+' : item.badge}</span>
              ) : null}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-name">{user?.full_name}</span>
            <span className="user-role">{t('roles.CONTENT_MGR')}</span>
          </div>
          <button className="logout-btn" onClick={() => void handleLogout()}>
            {t('nav.logout')}
          </button>
        </div>
      </aside>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
