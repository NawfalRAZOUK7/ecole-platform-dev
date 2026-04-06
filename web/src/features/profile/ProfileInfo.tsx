import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import type { ProfileInfoProps } from './profile.types';

export function ProfileInfo({ children, childrenLoading, user }: ProfileInfoProps) {
  const { t } = useTranslation();

  return (
    <>
      <div className="profile-fields">
        <div className="profile-field">
          <label>{t('profile.name')}</label>
          <span>{user.full_name}</span>
        </div>
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
        {user.permissions.length > 0 && (
          <div className="profile-field">
            <label>{t('profile.permissions')}</label>
            <div className="permissions-list">
              {user.permissions.map((permission) => (
                <span key={permission} className="permission-badge">{permission}</span>
              ))}
            </div>
          </div>
        )}
        <div className="profile-field">
          <label>{t('profile.language')}</label>
          <LanguageSwitcher />
        </div>
      </div>

      {user.role === 'PAR' && (
        <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>{t('profile.myChildren.title')}</h3>
          {childrenLoading ? (
            <p style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>{t('app.loading')}</p>
          ) : children.length === 0 ? (
            <p style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>{t('profile.myChildren.empty')}</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {children.map((child) => (
                <Link
                  key={child.user_id}
                  to="/results"
                  style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', textDecoration: 'none', color: 'inherit', cursor: 'pointer' }}
                >
                  <span style={{ fontSize: 28 }}>👧</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{child.full_name}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{child.email}</div>
                    {child.student_profile?.class_level && (
                      <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                        {t('register.classLevel')}: {child.student_profile.class_level}
                      </div>
                    )}
                  </div>
                  <span style={{ fontSize: 18, color: 'var(--color-text-secondary)' }}>›</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
