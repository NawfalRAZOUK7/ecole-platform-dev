import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import type { SecuritySettingsProps } from './profile.types';

export function SecuritySettings({
  confirmPassword,
  currentPassword,
  isPending,
  newPassword,
  passwordError,
  passwordSuccess,
  policyResults,
  showPasswordForm,
  onCancel,
  onChangeConfirmPassword,
  onChangeCurrentPassword,
  onChangeNewPassword,
  onDismissError,
  onSubmit,
  onToggle,
}: SecuritySettingsProps) {
  const { t } = useTranslation();

  return (
    <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 16 }}>
      {!showPasswordForm ? (
        <button className="btn btn-secondary" onClick={() => onToggle(true)}>{t('profile.changePassword')}</button>
      ) : (
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>{t('profile.changePassword')}</h3>
          <ErrorBanner error={passwordError} onDismiss={onDismissError} />
          {passwordSuccess && (
            <div style={{ padding: 12, background: '#ecfdf5', border: '1px solid var(--color-success)', borderRadius: 'var(--radius)', marginBottom: 12, fontSize: 14, color: 'var(--color-success)' }}>
              {t('profile.passwordChanged')}
            </div>
          )}

          <form onSubmit={onSubmit}>
            <label className="form-field" style={{ marginBottom: 12 }}>
              <span>{t('profile.currentPassword')}</span>
              <input type="password" className="filter-input" value={currentPassword} onChange={(event) => onChangeCurrentPassword(event.target.value)} required autoComplete="current-password" disabled={isPending} style={{ width: '100%' }} />
            </label>
            <label className="form-field" style={{ marginBottom: 8 }}>
              <span>{t('profile.newPassword')}</span>
              <input type="password" className="filter-input" value={newPassword} onChange={(event) => onChangeNewPassword(event.target.value)} required minLength={12} autoComplete="new-password" disabled={isPending} style={{ width: '100%' }} />
            </label>

            {newPassword.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                {policyResults.map((result) => (
                  <div key={result.key} style={{ fontSize: 12, color: result.passed ? 'var(--color-success)' : 'var(--color-danger)', display: 'flex', alignItems: 'center', gap: 6, padding: '1px 0' }}>
                    <span>{result.passed ? '\u2713' : '\u2717'}</span>
                    <span>{t(`profile.policy.${result.key}`)}</span>
                  </div>
                ))}
              </div>
            )}

            <label className="form-field" style={{ marginBottom: 12 }}>
              <span>{t('profile.confirmPassword')}</span>
              <input type="password" className="filter-input" value={confirmPassword} onChange={(event) => onChangeConfirmPassword(event.target.value)} required autoComplete="new-password" disabled={isPending} style={{ width: '100%' }} />
              {confirmPassword.length > 0 && newPassword !== confirmPassword && (
                <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>{t('profile.passwordMismatch')}</span>
              )}
            </label>

            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" className="btn btn-primary" disabled={isPending || !currentPassword || !newPassword || newPassword !== confirmPassword}>
                {isPending ? t('app.loading') : t('profile.changePassword')}
              </button>
              <button type="button" className="btn btn-secondary" onClick={onCancel}>{t('app.cancel')}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
