import { useTranslation } from 'react-i18next';
import type { VerificationStepProps } from '../model/auth.types';

export function VerificationStep({
  loading,
  otp,
  onChangeOtp,
  onSkip,
  onSubmit,
}: VerificationStepProps) {
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
        {t('register.otpInstructions')}
      </p>

      <label className="form-field" htmlFor="reg-otp">
        <span>{t('register.otp')}</span>
        <input
          id="reg-otp"
          type="text"
          value={otp}
          onChange={(event) => onChangeOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
          placeholder="000000"
          maxLength={6}
          pattern="[0-9]{6}"
          required
          autoFocus
          disabled={loading}
          style={{ textAlign: 'center', fontSize: 18, letterSpacing: 4 }}
        />
      </label>

      <button type="submit" className="login-submit" disabled={loading || otp.length !== 6}>
        {loading ? t('app.loading') : t('register.verify')}
      </button>

      <button
        type="button"
        onClick={onSkip}
        style={{
          width: '100%',
          marginTop: 8,
          background: 'none',
          border: 'none',
          color: 'var(--color-text-secondary)',
          cursor: 'pointer',
          fontSize: 13,
        }}
      >
        {t('register.skipOtp')}
      </button>
    </form>
  );
}
