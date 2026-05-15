import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { InviteCodeStepProps } from '../model/auth.types';

export function InviteCodeStep({ code, loading, onChangeCode, onSubmit }: InviteCodeStepProps) {
  const { t } = useTranslation();

  return (
    <form onSubmit={onSubmit} className="login-form">
      <p
        style={{
          fontSize: 14,
          color: 'var(--color-text-secondary)',
          marginBottom: 16,
          textAlign: 'center',
        }}
      >
        {t('register.step1')}
      </p>
      <div className="form-field">
        <label htmlFor="code">{t('register.code')}</label>
        <input
          id="code"
          type="text"
          value={code}
          onChange={(event) => onChangeCode(event.target.value.toUpperCase())}
          placeholder={t('register.codePlaceholder')}
          maxLength={8}
          required
          autoFocus
          disabled={loading}
          style={{ textAlign: 'center', fontSize: 18, letterSpacing: 4 }}
        />
      </div>
      <button type="submit" className="login-submit" disabled={loading || code.length !== 8}>
        {loading ? t('app.loading') : t('register.next')}
      </button>
      <div style={{ textAlign: 'center', marginTop: 12 }}>
        <Link to="/login" style={{ color: 'var(--color-primary)', fontSize: 14 }}>
          {t('register.hasAccount')}
        </Link>
      </div>
    </form>
  );
}
