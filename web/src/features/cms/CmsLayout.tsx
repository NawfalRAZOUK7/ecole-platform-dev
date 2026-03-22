/**
 * CMS Dashboard layout — separate sidebar for CONTENT_MGR role.
 *
 * Phase 10A — CMS route group /cms/* with own navigation.
 * Sidebar: Content, Upload, Review Queue (with pending badge), Quizzes, Analytics.
 */

import { useCallback, useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { api } from '@/services/api/client';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';

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
  const [pendingCount, setPendingCount] = useState(0);

  const fetchPendingCount = useCallback(async () => {
    try {
      const resp = await api.list<{ id: string }>('/cms/submissions', {
        status: 'PENDING',
        limit: 1,
      });
      // The meta may not have total_count, so we use has_more as a hint
      // If has_more is true, there's at least 2; otherwise count the data
      if (resp.meta.has_more) {
        setPendingCount(99); // placeholder; real count would need a dedicated endpoint
      } else {
        setPendingCount(resp.data.length);
      }
    } catch {
      // Silently fail — badge is non-critical
    }
  }, []);

  useEffect(() => {
    fetchPendingCount();
    const interval = setInterval(fetchPendingCount, 60000);
    return () => clearInterval(interval);
  }, [fetchPendingCount]);

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
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{t(item.labelKey)}</span>
              {item.badge != null && item.badge > 0 && (
                <span className="notif-badge">
                  {item.badge > 99 ? '99+' : item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-name">{user?.full_name}</span>
            <span className="user-role">{t('roles.CONTENT_MGR')}</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
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
