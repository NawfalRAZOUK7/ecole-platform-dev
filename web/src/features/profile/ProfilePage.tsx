/**
 * Profile page — user info, language selection, logout.
 *
 * Reference: S-081 — Profile / /me page
 * Displays user profile from AuthContext. No API call needed.
 */

import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';

export function ProfilePage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  if (!user) return null;

  return (
    <div className="page">
      <h1 className="page-title">{t('profile.title')}</h1>

      <div className="card profile-card">
        <div className="profile-avatar">
          <span style={{ fontSize: '48px' }}>👤</span>
        </div>

        <div className="profile-fields">
          <div className="profile-field">
            <label>{t('profile.email')}</label>
            <span>{user.email}</span>
          </div>

          <div className="profile-field">
            <label>{t('profile.role')}</label>
            <span className="role-badge">{t(`roles.${user.role}`, user.role)}</span>
          </div>

          <div className="profile-field">
            <label>{t('profile.school')}</label>
            <span>{user.school_id}</span>
          </div>

          {user.permissions && user.permissions.length > 0 && (
            <div className="profile-field">
              <label>{t('profile.permissions')}</label>
              <div className="permissions-list">
                {user.permissions.map((perm) => (
                  <span key={perm} className="permission-badge">{perm}</span>
                ))}
              </div>
            </div>
          )}

          <div className="profile-field">
            <label>{t('profile.language')}</label>
            <LanguageSwitcher />
          </div>
        </div>

        <button className="btn btn-danger logout-button" onClick={handleLogout}>
          {t('profile.logout')}
        </button>
      </div>
    </div>
  );
}
