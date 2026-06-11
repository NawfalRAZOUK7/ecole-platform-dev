/**
 * SMS-based Two-Factor Authentication section.
 *
 * Companion to TwoFactorPage (TOTP). Calls POST /auth/sms-2fa/setup,
 * /verify-setup, /disable. Phone-based OTP via the backend Twilio service.
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useDisableSmsTwoFactor,
  useSmsTwoFactorSetup,
  useVerifySmsTwoFactorSetup,
} from '../model/useProfile';

type Step = 'idle' | 'enter-phone' | 'verify' | 'disable';

export function SmsTwoFactorCard() {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();
  const [step, setStep] = useState<Step>('idle');
  const [phone, setPhone] = useState(user?.phone ?? '');
  const [code, setCode] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const setupMutation = useSmsTwoFactorSetup();
  const verifyMutation = useVerifySmsTwoFactorSetup();
  const disableMutation = useDisableSmsTwoFactor();

  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          setupMutation.error ?? verifyMutation.error ?? disableMutation.error,
          t('app.error'),
        ),
      [disableMutation.error, setupMutation.error, t, verifyMutation.error],
    ),
  );

  const isEnabled = user?.phone_otp_enabled === true;

  async function handleSendCode(e: FormEvent) {
    e.preventDefault();
    if (!phone.trim()) return;
    await setupMutation.mutateAsync(phone.trim());
    setStep('verify');
  }

  async function handleVerify(e: FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    await verifyMutation.mutateAsync(code.trim());
    setCode('');
    await refreshUser();
    setStep('idle');
  }

  async function handleDisable(e: FormEvent) {
    e.preventDefault();
    if (!disableCode.trim()) return;
    await disableMutation.mutateAsync(disableCode.trim());
    setDisableCode('');
    await refreshUser();
    setStep('idle');
  }

  return (
    <div className="card" style={{ maxWidth: 500, marginTop: 24 }}>
      <h3 style={{ marginBottom: 12, fontSize: 16, fontWeight: 600 }}>
        {t('twoFactorSms.title')}
      </h3>

      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} />

      {step === 'idle' && (
        <>
          <div style={{ marginBottom: 16 }}>
            <span style={{ fontWeight: 600 }}>{t('twoFactor.status')}:</span>{' '}
            {isEnabled ? (
              <span className="status-badge status-published">{t('twoFactor.enabled')}</span>
            ) : (
              <span className="status-badge status-draft">{t('twoFactor.disabled')}</span>
            )}
          </div>
          {isEnabled ? (
            <button className="btn btn-danger" onClick={() => setStep('disable')}>
              {t('twoFactorSms.disableBtn')}
            </button>
          ) : (
            <button className="btn btn-primary" onClick={() => setStep('enter-phone')}>
              {t('twoFactorSms.enableBtn')}
            </button>
          )}
        </>
      )}

      {step === 'enter-phone' && (
        <form onSubmit={handleSendCode}>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {t('twoFactorSms.phoneInstructions')}
          </p>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('twoFactorSms.phoneLabel')}</label>
            <input
              className="filter-input"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+212..."
              required
              autoFocus
              style={{ width: 240 }}
            />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" type="submit" disabled={setupMutation.isPending}>
              {setupMutation.isPending ? t('app.loading') : t('twoFactorSms.sendCode')}
            </button>
            <button className="btn btn-secondary" type="button" onClick={() => setStep('idle')}>
              {t('app.cancel')}
            </button>
          </div>
        </form>
      )}

      {step === 'verify' && (
        <form onSubmit={handleVerify}>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {t('twoFactorSms.verifyInstructions', { phone })}
          </p>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('twoFactor.enterCode')}</label>
            <input
              className="filter-input"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="000000"
              maxLength={6}
              pattern="[0-9]{6}"
              required
              autoFocus
              style={{ width: 160, textAlign: 'center', fontSize: 18, letterSpacing: 4 }}
            />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" type="submit" disabled={verifyMutation.isPending}>
              {verifyMutation.isPending ? t('app.loading') : t('twoFactor.verify')}
            </button>
            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => void setupMutation.mutateAsync(phone.trim())}
              disabled={setupMutation.isPending}
            >
              {t('twoFactorSms.resend')}
            </button>
            <button className="btn btn-secondary" type="button" onClick={() => setStep('idle')}>
              {t('app.cancel')}
            </button>
          </div>
        </form>
      )}

      {step === 'disable' && (
        <form onSubmit={handleDisable}>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {t('twoFactorSms.disableInstructions')}
          </p>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('twoFactor.enterCode')}</label>
            <input
              className="filter-input"
              value={disableCode}
              onChange={(e) => setDisableCode(e.target.value)}
              placeholder="000000"
              maxLength={6}
              pattern="[0-9]{6}"
              required
              autoFocus
              style={{ width: 160, textAlign: 'center', fontSize: 18, letterSpacing: 4 }}
            />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-danger" type="submit" disabled={disableMutation.isPending}>
              {disableMutation.isPending ? t('app.loading') : t('twoFactorSms.disableBtn')}
            </button>
            <button className="btn btn-secondary" type="button" onClick={() => setStep('idle')}>
              {t('app.cancel')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
