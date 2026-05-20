import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { authService } from '@/features/auth/api/auth.api';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';

function getPasswordStrength(password: string): 'weak' | 'medium' | 'strong' {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 2) return 'weak';
  if (score <= 3) return 'medium';
  return 'strong';
}

const STRENGTH_COLOR: Record<string, string> = {
  weak: 'var(--color-danger)',
  medium: 'var(--color-warning)',
  strong: 'var(--color-success)',
};

export function ResetPasswordPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const strength = newPassword ? getPasswordStrength(newPassword) : null;
  const mismatch = confirmPassword && newPassword !== confirmPassword;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError(t('resetPassword.mismatch'));
      return;
    }
    if (!token) {
      setError(t('resetPassword.invalidToken'));
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      await authService.resetPassword(token, newPassword);
      navigate('/login', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    } finally {
      setIsLoading(false);
    }
  }

  if (!token) {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="login-header">
            <h1 className="login-title">{t('app.name')}</h1>
            <LanguageSwitcher />
          </div>
          <p style={{ color: 'var(--color-danger)', textAlign: 'center', marginBottom: 16 }}>
            {t('resetPassword.invalidToken')}
          </p>
          <div style={{ textAlign: 'center' }}>
            <Link to="/forgot-password" style={{ color: 'var(--color-primary)', fontSize: 14 }}>
              {t('forgotPassword.title')}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">{t('app.name')}</h1>
          <LanguageSwitcher />
        </div>

        <h2 className="login-subtitle">{t('resetPassword.title')}</h2>

        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-field">
            <label htmlFor="newPassword">{t('resetPassword.newPassword')}</label>
            <input
              id="newPassword"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              autoComplete="new-password"
              disabled={isLoading}
            />
            {strength && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                <div
                  style={{
                    flex: 1,
                    height: 4,
                    borderRadius: 2,
                    backgroundColor: 'var(--color-border)',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      borderRadius: 2,
                      backgroundColor: STRENGTH_COLOR[strength],
                      width: strength === 'weak' ? '33%' : strength === 'medium' ? '66%' : '100%',
                      transition: 'width 0.2s',
                    }}
                  />
                </div>
                <span style={{ fontSize: 12, color: STRENGTH_COLOR[strength] }}>
                  {t(`resetPassword.strength.${strength}`)}
                </span>
              </div>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="confirmPassword">{t('resetPassword.confirmPassword')}</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
              disabled={isLoading}
              style={mismatch ? { borderColor: 'var(--color-danger)' } : undefined}
            />
            {mismatch && (
              <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>
                {t('resetPassword.mismatch')}
              </span>
            )}
          </div>

          <button
            type="submit"
            className="login-submit"
            disabled={isLoading || !newPassword || !confirmPassword || Boolean(mismatch)}
          >
            {isLoading ? t('app.loading') : t('resetPassword.submit')}
          </button>

          <div style={{ textAlign: 'center', marginTop: 12 }}>
            <Link to="/login" style={{ color: 'var(--color-primary)', fontSize: 14 }}>
              {t('forgotPassword.backToLogin')}
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
