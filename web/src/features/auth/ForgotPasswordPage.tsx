import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { authService } from './auth.service';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher';

export function ForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await authService.requestRecovery(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">{t('app.name')}</h1>
          <LanguageSwitcher />
        </div>

        <h2 className="login-subtitle">{t('forgotPassword.title')}</h2>

        {sent ? (
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: 'var(--color-success)', marginBottom: 16 }}>
              {t('forgotPassword.sent')}
            </p>
            <Link to="/login" style={{ color: 'var(--color-primary)', fontSize: 14 }}>
              {t('forgotPassword.backToLogin')}
            </Link>
          </div>
        ) : (
          <>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16, textAlign: 'center' }}>
              {t('forgotPassword.instructions')}
            </p>

            <ErrorBanner error={error} onDismiss={() => setError(null)} />

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

              <button
                type="submit"
                className="login-submit"
                disabled={isLoading || !email}
              >
                {isLoading ? t('app.loading') : t('forgotPassword.submit')}
              </button>

              <div style={{ textAlign: 'center', marginTop: 12 }}>
                <Link to="/login" style={{ color: 'var(--color-primary)', fontSize: 14 }}>
                  {t('forgotPassword.backToLogin')}
                </Link>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
