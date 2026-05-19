/**
 * Login page — email, password, school selector + 2FA TOTP step.
 *
 * Reference: S-079 — Login page with role-based redirect
 * Phase 4C (from 2B) — 2FA login flow integration
 * Calls POST /auth/login with school_id. If 2FA required, shows TOTP input.
 */

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Building2, LogIn } from 'lucide-react';
import { useAuth } from '@/app/providers/AuthContext';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';

/** Default school ID from seed data */
const DEFAULT_SCHOOL_ID = '00000000-0000-4000-8000-000000000001';
type OAuthProvider = 'google' | 'microsoft';

function isOAuthProvider(provider: string | null | undefined): provider is OAuthProvider {
  return provider === 'google' || provider === 'microsoft';
}

export function LoginPage() {
  const { t } = useTranslation();
  const {
    login,
    verify2fa,
    cancel2fa,
    isAuthenticated,
    isLoading,
    error,
    clearError,
    twoFactorPending,
    startOAuthLogin,
    completeOAuthLogin,
  } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const translatedError = error ? t(error) : null;
  const oauthCallbackHandledRef = useRef(false);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [schoolId, setSchoolId] = useState(DEFAULT_SCHOOL_ID);
  const [totpCode, setTotpCode] = useState('');
  const [useBackupCode, setUseBackupCode] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (oauthCallbackHandledRef.current) return;

    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const returnedState = params.get('state');
    if (!code || !returnedState) return;

    let pending: { provider?: string; schoolId?: string } | null = null;
    const pendingRaw = sessionStorage.getItem('oauth_pending');
    if (pendingRaw) {
      try {
        pending = JSON.parse(pendingRaw) as { provider?: string; schoolId?: string };
      } catch {
        pending = null;
      }
    }

    const providerFromUrl = params.get('provider');
    const provider = isOAuthProvider(providerFromUrl)
      ? providerFromUrl
      : isOAuthProvider(pending?.provider)
        ? pending.provider
        : null;
    const callbackSchoolId = pending?.schoolId ?? schoolId;

    if (!provider || !callbackSchoolId) return;

    oauthCallbackHandledRef.current = true;
    clearError();
    void completeOAuthLogin(provider, code, returnedState, callbackSchoolId);
  }, [clearError, completeOAuthLogin, location.search, schoolId]);

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

  async function handleOAuthLogin(provider: OAuthProvider) {
    if (!schoolId.trim()) return;
    clearError();
    await startOAuthLogin(provider, schoolId.trim());
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

        <div className="oauth-login" aria-label={t('login.oauth.title')}>
          <button
            type="button"
            className="oauth-button oauth-button-google"
            onClick={() => void handleOAuthLogin('google')}
            disabled={isLoading || !schoolId.trim()}
          >
            <LogIn aria-hidden="true" />
            <span>{t('login.oauth.google')}</span>
          </button>
          <button
            type="button"
            className="oauth-button oauth-button-microsoft"
            onClick={() => void handleOAuthLogin('microsoft')}
            disabled={isLoading || !schoolId.trim()}
          >
            <Building2 aria-hidden="true" />
            <span>{t('login.oauth.microsoft')}</span>
          </button>
        </div>

        <div className="login-separator">
          <span>{t('login.oauth.separator')}</span>
        </div>

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
