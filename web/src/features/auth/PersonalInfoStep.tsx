import { useTranslation } from 'react-i18next';
import type { PersonalInfoStepProps } from './register.types';

export function PersonalInfoStep({
  allPolicyPassed,
  confirmPassword,
  email,
  fullName,
  loading,
  password,
  phone,
  policyResults,
  onBack,
  onChangeConfirmPassword,
  onChangeEmail,
  onChangeFullName,
  onChangePassword,
  onChangePhone,
  onSubmit,
}: PersonalInfoStepProps) {
  const { t } = useTranslation();

  return (
    <form onSubmit={onSubmit} className="login-form">
      <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16, textAlign: 'center' }}>
        {t('register.step2')}
      </p>

      <label className="form-field" htmlFor="reg-email">
        <span>{t('register.email')}</span>
        <input id="reg-email" type="email" value={email} onChange={(event) => onChangeEmail(event.target.value)} required disabled={loading} autoComplete="email" />
      </label>
      <label className="form-field" htmlFor="reg-name">
        <span>{t('register.fullName')}</span>
        <input id="reg-name" type="text" value={fullName} onChange={(event) => onChangeFullName(event.target.value)} required disabled={loading} maxLength={200} />
      </label>
      <label className="form-field" htmlFor="reg-phone">
        <span>{t('register.phone')}</span>
        <input id="reg-phone" type="tel" value={phone} onChange={(event) => onChangePhone(event.target.value)} disabled={loading} maxLength={20} />
      </label>
      <label className="form-field" htmlFor="reg-password">
        <span>{t('register.password')}</span>
        <input id="reg-password" type="password" value={password} onChange={(event) => onChangePassword(event.target.value)} required minLength={12} disabled={loading} autoComplete="new-password" />
      </label>

      {password.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          {policyResults.map((result) => (
            <div key={result.key} style={{ fontSize: 12, color: result.passed ? 'var(--color-success)' : 'var(--color-danger)', display: 'flex', alignItems: 'center', gap: 6, padding: '1px 0' }}>
              <span>{result.passed ? '\u2713' : '\u2717'}</span>
              <span>{t(`profile.policy.${result.key}`)}</span>
            </div>
          ))}
        </div>
      )}

      <label className="form-field" htmlFor="reg-confirm">
        <span>{t('register.confirmPassword')}</span>
        <input id="reg-confirm" type="password" value={confirmPassword} onChange={(event) => onChangeConfirmPassword(event.target.value)} required disabled={loading} autoComplete="new-password" />
        {confirmPassword.length > 0 && password !== confirmPassword && (
          <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>{t('profile.passwordMismatch')}</span>
        )}
      </label>

      <div style={{ display: 'flex', gap: 8 }}>
        <button type="button" className="btn btn-secondary" onClick={onBack} style={{ flex: 1 }}>
          {t('app.back')}
        </button>
        <button type="submit" className="login-submit" style={{ flex: 2 }} disabled={loading || !allPolicyPassed || password !== confirmPassword}>
          {t('register.next')}
        </button>
      </div>
    </form>
  );
}
