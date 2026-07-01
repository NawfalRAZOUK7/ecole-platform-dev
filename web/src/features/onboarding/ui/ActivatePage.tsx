/**
 * ActivatePage — public set-password page for onboarding-provisioned owners.
 *
 * Reached via the activation link emailed on SuperAdmin approval
 * (`/activate?token=…`). The owner chooses a password; a valid submission
 * flips their INACTIVE account to ACTIVE, after which they can log in.
 * Localized (fr/en/ar).
 */

import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { applicationsService } from '@/features/onboarding/api/applications.api';
import { CelebrationOverlay } from '@/shared/ui/CelebrationOverlay';

export function ActivatePage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => (await applicationsService.activate(token, password)).data,
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    if (password.length < 12) {
      setLocalError(
        t('activate.tooShort', 'Le mot de passe doit contenir au moins 12 caractères.'),
      );
      return;
    }
    if (password !== confirm) {
      setLocalError(t('activate.mismatch', 'Les mots de passe ne correspondent pas.'));
      return;
    }
    mutation.mutate();
  };

  if (!token) {
    return (
      <div className="page" style={{ maxWidth: 480, margin: '48px auto' }}>
        <h1 className="page-title">{t('activate.title', 'Activer votre compte')}</h1>
        <p style={{ color: 'var(--color-danger, #c00)' }}>
          {t('activate.noToken', "Lien d'activation invalide ou incomplet.")}
        </p>
        <Link to="/login">{t('activate.backToLogin', 'Aller à la connexion')}</Link>
      </div>
    );
  }

  if (mutation.isSuccess) {
    return (
      <div className="page" style={{ maxWidth: 480, margin: '48px auto', textAlign: 'center' }}>
        <CelebrationOverlay trigger="onboarding_complete" />
        <div style={{ fontSize: 56 }}>✅</div>
        <h1 className="page-title">{t('activate.doneTitle', 'Compte activé !')}</h1>
        <p>
          {t(
            'activate.doneBody',
            'Votre mot de passe a été défini et votre compte est actif. Vous pouvez maintenant vous connecter.',
          )}
        </p>
        <Link
          className="btn btn-primary"
          to="/login"
          style={{ marginTop: 16, display: 'inline-block' }}
        >
          {t('activate.goLogin', 'Se connecter')}
        </Link>
      </div>
    );
  }

  const serverError = mutation.isError
    ? ((mutation.error as { response?: { data?: { error?: { message?: string } } } })?.response
        ?.data?.error?.message ??
      t('activate.failed', "L'activation a échoué. Le lien est peut-être expiré ou déjà utilisé."))
    : null;

  return (
    <div className="page" style={{ maxWidth: 480, margin: '48px auto' }}>
      <h1 className="page-title">{t('activate.title', 'Activer votre compte')}</h1>
      <p style={{ color: 'var(--color-text-secondary)' }}>
        {t('activate.subtitle', 'Choisissez un mot de passe pour finaliser votre compte.')}
      </p>
      <form
        onSubmit={submit}
        style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}
      >
        <label>
          {t('activate.password', 'Mot de passe')}
          <input
            type="password"
            className="input"
            value={password}
            autoComplete="new-password"
            minLength={12}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%' }}
          />
        </label>
        <label>
          {t('activate.confirm', 'Confirmer le mot de passe')}
          <input
            type="password"
            className="input"
            value={confirm}
            autoComplete="new-password"
            minLength={12}
            onChange={(e) => setConfirm(e.target.value)}
            style={{ width: '100%' }}
          />
        </label>
        {(localError || serverError) && (
          <p style={{ color: 'var(--color-danger, #c00)' }}>{localError ?? serverError}</p>
        )}
        <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
          {mutation.isPending
            ? t('activate.activating', 'Activation…')
            : t('activate.activate', 'Activer le compte')}
        </button>
      </form>
    </div>
  );
}
