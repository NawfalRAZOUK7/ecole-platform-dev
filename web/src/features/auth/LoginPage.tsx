/**
 * Login page — email, password, school selector + 2FA TOTP step.
 *
 * Reference: S-079 — Login page with role-based redirect
 * Phase 4C (from 2B) — 2FA login flow integration
 * Calls POST /auth/login with school_id. If 2FA required, shows TOTP input.
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';

/** Default school ID from seed data */
const DEFAULT_SCHOOL_ID = 'bd9a703c-aca8-5fb2-81d7-58e902aa2472';

export function LoginPage() {
  const { t } = useTranslation();
  const { login, verify2fa, cancel2fa, isLoading, error, clearError, twoFactorPending } = useAuth();
  const navigate = useNavigate();
  const translatedError = error ? t(error) : null;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [schoolId, setSchoolId] = useState(DEFAULT_SCHOOL_ID);
  const [totpCode, setTotpCode] = useState('');
  const [useBackupCode, setUseBackupCode] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    clearError();

    try {
      await login(email, password, schoolId);
      // If 2FA is not required, login resolves with user set → navigate.
      // If 2FA is required, twoFactorPending is set → component re-renders to 2FA step.
      // We navigate to / which triggers RoleRedirect. If not authenticated yet (2FA pending),
      // the component will show the 2FA form instead.
      navigate('/');
    } catch {
      // Error is handled by AuthContext state
    }
  }

  async function handleVerify2fa(e: FormEvent) {
    e.preventDefault();
    clearError();
    const code = totpCode.trim();
    if (!code) return;

    try {
      await verify2fa(code);
      navigate('/');
    } catch {
      // Error handled by AuthContext
    }
  }

  function handleCancel2fa() {
    cancel2fa();
    setTotpCode('');
    setUseBackupCode(false);
  }

  // After successful login (no 2FA), navigate
  // We use the isAuthenticated check in App.tsx redirect logic
  // The login function resolves after setting user state
  // So if twoFactorPending is null and login resolved, we navigate in handleSubmit

  // 2FA step
  if (twoFactorPending) {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="login-header">
            <h1 className="login-title">{t('app.name')}</h1>
            <LanguageSwitcher />
          </div>

          <h2 className="login-subtitle">{t('login.twoFactor.title')}</h2>
          <p
            style={{
              fontSize: 13,
              color: 'var(--color-text-secondary)',
              marginBottom: 16,
              textAlign: 'center',
            }}
          >
            {useBackupCode
              ? t('login.twoFactor.backupInstructions')
              : t('login.twoFactor.instructions')}
          </p>

          <ErrorBanner error={translatedError} onDismiss={clearError} />

          <form onSubmit={handleVerify2fa} className="login-form">
            <div className="form-field">
              <label htmlFor="totpCode">
                {useBackupCode ? t('login.twoFactor.backupCode') : t('login.twoFactor.code')}
              </label>
              <input
                id="totpCode"
                type="text"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                placeholder={useBackupCode ? t('login.twoFactor.backupPlaceholder') : '000000'}
                maxLength={useBackupCode ? 20 : 6}
                pattern={useBackupCode ? undefined : '[0-9]{6}'}
                required
                autoFocus
                autoComplete="one-time-code"
                disabled={isLoading}
                style={
                  useBackupCode
                    ? undefined
                    : { textAlign: 'center', fontSize: 18, letterSpacing: 4 }
                }
              />
            </div>

            <button type="submit" className="login-submit" disabled={isLoading || !totpCode.trim()}>
              {isLoading ? t('app.loading') : t('login.twoFactor.verify')}
            </button>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
              <button
                type="button"
                className="btn-link"
                onClick={() => {
                  setUseBackupCode(!useBackupCode);
                  setTotpCode('');
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-primary)',
                  cursor: 'pointer',
                  fontSize: 13,
                }}
              >
                {useBackupCode ? t('login.twoFactor.useApp') : t('login.twoFactor.useBackup')}
              </button>
              <button
                type="button"
                className="btn-link"
                onClick={handleCancel2fa}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-text-secondary)',
                  cursor: 'pointer',
                  fontSize: 13,
                }}
              >
                {t('app.cancel')}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // Normal login form
  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">{t('app.name')}</h1>
          <LanguageSwitcher />
        </div>

        <h2 className="login-subtitle">{t('login.title')}</h2>

        <ErrorBanner error={translatedError} onDismiss={clearError} />

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-field">
            <label htmlFor="email">{t('login.email')}</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              disabled={isLoading}
            />
          </div>

          <div className="form-field">
            <label htmlFor="password">{t('login.password')}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              disabled={isLoading}
            />
          </div>

          <div className="form-field">
            <label htmlFor="schoolId">{t('login.school')}</label>
            <input
              id="schoolId"
              type="text"
              value={schoolId}
              onChange={(e) => setSchoolId(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            className="login-submit"
            disabled={isLoading || !email || !password || !schoolId}
          >
            {isLoading ? t('login.loading') : t('login.submit')}
          </button>

          <div style={{ textAlign: 'center', marginTop: 12 }}>
            <Link to="/register" style={{ color: 'var(--color-primary)', fontSize: 14 }}>
              {t('register.hasCode')}
            </Link>
          </div>
          <div style={{ textAlign: 'center', marginTop: 8 }}>
            <Link
              to="/forgot-password"
              style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}
            >
              {t('login.forgotPassword')}
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
