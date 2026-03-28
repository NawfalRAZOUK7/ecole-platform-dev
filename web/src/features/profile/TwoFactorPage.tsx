/**
 * Two-Factor Authentication setup page.
 *
 * Reference: Phase 4C (from 2B) — 2FA setup UI
 * Calls POST /auth/2fa/setup, /verify-setup, /disable.
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useDisableTwoFactor, useTwoFactorSetup, useVerifyTwoFactorSetup } from './useProfile';

type Step = 'idle' | 'setup' | 'verify' | 'done' | 'disable';

export function TwoFactorPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [step, setStep] = useState<Step>('idle');
  const [provisioningUri, setProvisioningUri] = useState('');
  const [secret, setSecret] = useState('');
  const [code, setCode] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [disableCode, setDisableCode] = useState('');
  const setupMutation = useTwoFactorSetup();
  const verifySetupMutation = useVerifyTwoFactorSetup();
  const disableMutation = useDisableTwoFactor();
  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(setupMutation.error ?? verifySetupMutation.error ?? disableMutation.error, t('app.error')),
      [disableMutation.error, setupMutation.error, t, verifySetupMutation.error]
    )
  );
  const is2faEnabled = user?.totp_enabled === true;

  async function handleStartSetup() {
    const response = await setupMutation.mutateAsync();
    setProvisioningUri(response.provisioning_uri);
    setSecret(response.secret);
    setStep('setup');
  }

  async function handleVerifySetup(e: FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    const response = await verifySetupMutation.mutateAsync(code.trim());
    setBackupCodes(response.backup_codes);
    setStep('done');
  }

  async function handleDisable(e: FormEvent) {
    e.preventDefault();
    if (!disableCode.trim()) return;
    await disableMutation.mutateAsync(disableCode.trim());
    setStep('idle');
    setDisableCode('');
    window.location.reload();
  }

  function handleDownloadBackupCodes() {
    const text = backupCodes.join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ecole-platform-backup-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('twoFactor.title')}</h1>

      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} />

      {/* Idle: show current status + action */}
      {step === 'idle' && (
        <div className="card" style={{ maxWidth: 500 }}>
          <div style={{ marginBottom: 16 }}>
            <span style={{ fontWeight: 600 }}>{t('twoFactor.status')}:</span>{' '}
            {is2faEnabled ? (
              <span className="status-badge status-published">{t('twoFactor.enabled')}</span>
            ) : (
              <span className="status-badge status-draft">{t('twoFactor.disabled')}</span>
            )}
          </div>
          {is2faEnabled ? (
            <button className="btn btn-danger" onClick={() => setStep('disable')}>
              {t('twoFactor.disableBtn')}
            </button>
          ) : (
            <button className="btn btn-primary" onClick={() => void handleStartSetup()} disabled={setupMutation.isPending}>
              {setupMutation.isPending ? t('app.loading') : t('twoFactor.enableBtn')}
            </button>
          )}
        </div>
      )}

      {/* Setup: show QR code + secret */}
      {step === 'setup' && (
        <div className="card" style={{ maxWidth: 500 }}>
          <h3 style={{ marginBottom: 12, fontSize: 16, fontWeight: 600 }}>{t('twoFactor.scanQR')}</h3>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {t('twoFactor.scanInstructions')}
          </p>

          {/* QR code via Google Charts API — encodes the provisioning URI */}
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            <img
              src={`https://chart.googleapis.com/chart?cht=qr&chs=200x200&chl=${encodeURIComponent(provisioningUri)}`}
              alt="QR Code"
              style={{ border: '1px solid var(--color-border)', borderRadius: 8, padding: 8 }}
              width={200}
              height={200}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              {t('twoFactor.manualEntry')}
            </label>
            <div className="code-display" style={{ marginTop: 4 }}>
              <code className="invite-code">{secret}</code>
            </div>
          </div>

          <form onSubmit={handleVerifySetup}>
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
              <button className="btn btn-primary" type="submit" disabled={verifySetupMutation.isPending}>
                {verifySetupMutation.isPending ? t('app.loading') : t('twoFactor.verify')}
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => setStep('idle')}>
                {t('app.cancel')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Done: show backup codes */}
      {step === 'done' && (
        <div className="card" style={{ maxWidth: 500 }}>
          <h3 style={{ marginBottom: 12, fontSize: 16, fontWeight: 600, color: 'var(--color-success)' }}>
            {t('twoFactor.activated')}
          </h3>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {t('twoFactor.backupInstructions')}
          </p>
          <div className="code-display" style={{ marginBottom: 16, textAlign: 'start' }}>
            {backupCodes.map((c, i) => (
              <code key={i} style={{ display: 'block', fontSize: 14, fontWeight: 600, padding: '2px 0' }}>
                {c}
              </code>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={handleDownloadBackupCodes}>
              {t('twoFactor.downloadCodes')}
            </button>
            <button className="btn btn-secondary" onClick={() => window.location.reload()}>
              {t('app.close')}
            </button>
          </div>
        </div>
      )}

      {/* Disable: ask for code */}
      {step === 'disable' && (
        <div className="card" style={{ maxWidth: 500 }}>
          <h3 style={{ marginBottom: 12, fontSize: 16, fontWeight: 600 }}>{t('twoFactor.disableTitle')}</h3>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {t('twoFactor.disableInstructions')}
          </p>
          <form onSubmit={handleDisable}>
            <div className="form-field" style={{ marginBottom: 12 }}>
              <label>{t('twoFactor.enterCode')}</label>
              <input
                className="filter-input"
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value)}
                placeholder={t('twoFactor.codePlaceholder')}
                required
                autoFocus
                style={{ width: 200 }}
              />
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-danger" type="submit" disabled={disableMutation.isPending}>
                {disableMutation.isPending ? t('app.loading') : t('twoFactor.disableBtn')}
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => setStep('idle')}>
                {t('app.cancel')}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
