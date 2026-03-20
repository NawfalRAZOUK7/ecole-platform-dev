/**
 * Profile page — user info, edit name/language, change password with policy feedback.
 *
 * Reference: S-081 — Profile / /me page
 * Phase 4C (from 2A) — Password change with policy feedback
 * Calls POST /auth/change-password with current + new password.
 */

import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { api, ApiClientError } from '@/services/api/client';

/** Password policy rules — mirrors backend app/core/password_policy.py */
const PASSWORD_RULES = [
  { key: 'minLength', test: (p: string) => p.length >= 12 },
  { key: 'uppercase', test: (p: string) => /[A-Z]/.test(p) },
  { key: 'lowercase', test: (p: string) => /[a-z]/.test(p) },
  { key: 'digit', test: (p: string) => /\d/.test(p) },
  { key: 'special', test: (p: string) => /[^A-Za-z0-9]/.test(p) },
];

export function ProfilePage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Password change state
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  async function handlePasswordChange(e: FormEvent) {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (newPassword !== confirmPassword) {
      setPasswordError(t('profile.passwordMismatch'));
      return;
    }

    // Client-side policy check
    const failedRules = PASSWORD_RULES.filter((r) => !r.test(newPassword));
    if (failedRules.length > 0) {
      setPasswordError(t('profile.passwordPolicyFail'));
      return;
    }

    setPasswordLoading(true);
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setPasswordLoading(false);
    }
  }

  if (!user) return null;

  const policyResults = PASSWORD_RULES.map((r) => ({
    key: r.key,
    passed: newPassword.length > 0 ? r.test(newPassword) : null,
  }));

  return (
    <div className="page">
      <h1 className="page-title">{t('profile.title')}</h1>

      <div className="card profile-card">
        <div className="profile-avatar">
          <span style={{ fontSize: '48px' }}>👤</span>
        </div>

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

        {/* Password Change Section */}
        <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 16 }}>
          {!showPasswordForm ? (
            <button
              className="btn btn-secondary"
              onClick={() => setShowPasswordForm(true)}
            >
              {t('profile.changePassword')}
            </button>
          ) : (
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
                {t('profile.changePassword')}
              </h3>

              <ErrorBanner error={passwordError} onDismiss={() => setPasswordError(null)} />

              {passwordSuccess && (
                <div style={{ padding: 12, background: '#ecfdf5', border: '1px solid var(--color-success)', borderRadius: 'var(--radius)', marginBottom: 12, fontSize: 14, color: 'var(--color-success)' }}>
                  {t('profile.passwordChanged')}
                </div>
              )}

              <form onSubmit={handlePasswordChange}>
                <div className="form-field" style={{ marginBottom: 12 }}>
                  <label>{t('profile.currentPassword')}</label>
                  <input
                    type="password"
                    className="filter-input"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    disabled={passwordLoading}
                    style={{ width: '100%' }}
                  />
                </div>

                <div className="form-field" style={{ marginBottom: 8 }}>
                  <label>{t('profile.newPassword')}</label>
                  <input
                    type="password"
                    className="filter-input"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={12}
                    autoComplete="new-password"
                    disabled={passwordLoading}
                    style={{ width: '100%' }}
                  />
                </div>

                {/* Password policy feedback */}
                {newPassword.length > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    {policyResults.map((r) => (
                      <div
                        key={r.key}
                        style={{
                          fontSize: 12,
                          color: r.passed ? 'var(--color-success)' : 'var(--color-danger)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '1px 0',
                        }}
                      >
                        <span>{r.passed ? '\u2713' : '\u2717'}</span>
                        <span>{t(`profile.policy.${r.key}`)}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="form-field" style={{ marginBottom: 12 }}>
                  <label>{t('profile.confirmPassword')}</label>
                  <input
                    type="password"
                    className="filter-input"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                    disabled={passwordLoading}
                    style={{ width: '100%' }}
                  />
                  {confirmPassword.length > 0 && newPassword !== confirmPassword && (
                    <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>
                      {t('profile.passwordMismatch')}
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={passwordLoading || !currentPassword || !newPassword || newPassword !== confirmPassword}
                  >
                    {passwordLoading ? t('app.loading') : t('profile.changePassword')}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowPasswordForm(false);
                      setPasswordError(null);
                      setPasswordSuccess(false);
                      setCurrentPassword('');
                      setNewPassword('');
                      setConfirmPassword('');
                    }}
                  >
                    {t('app.cancel')}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        <button className="btn btn-danger logout-button" onClick={handleLogout} style={{ marginTop: 16 }}>
          {t('profile.logout')}
        </button>
      </div>
    </div>
  );
}
