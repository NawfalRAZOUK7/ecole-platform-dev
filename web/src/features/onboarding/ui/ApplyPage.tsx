/**
 * ApplyPage — public onboarding application (no auth), localized (fr/en/ar).
 *
 * A prospective formal school or micro-école/educator submits a request with
 * optional documents/photos. A SuperAdmin reviews it; on approval the applicant
 * receives an invitation code (by email) to complete /register.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import {
  applicationsService,
  type ApplicationType,
} from '@/features/onboarding/api/applications.api';

export function ApplyPage() {
  const { t } = useTranslation();
  const [type, setType] = useState<ApplicationType>('formal_school');
  const [files, setFiles] = useState<File[]>([]);
  const [form, setForm] = useState({
    applicant_name: '',
    applicant_email: '',
    applicant_phone: '',
    city: '',
    org_name: '',
    address: '',
    neighborhood: '',
    level_band: '',
    max_capacity: '',
    notes: '',
  });

  const mutation = useMutation({
    mutationFn: async () => {
      const created =
        type === 'formal_school'
          ? (
              await applicationsService.submitFormalSchool({
                applicant_name: form.applicant_name,
                applicant_email: form.applicant_email,
                applicant_phone: form.applicant_phone || undefined,
                city: form.city || undefined,
                org_name: form.org_name,
                address: form.address || undefined,
                level_band: form.level_band || undefined,
                notes: form.notes || undefined,
              })
            ).data
          : (
              await applicationsService.submitMicroSchool({
                applicant_name: form.applicant_name,
                applicant_email: form.applicant_email,
                applicant_phone: form.applicant_phone || undefined,
                city: form.city || undefined,
                org_name: form.org_name,
                neighborhood: form.neighborhood || undefined,
                address: form.address || undefined,
                max_capacity: form.max_capacity ? Number(form.max_capacity) : undefined,
                notes: form.notes || undefined,
              })
            ).data;
      // Best-effort: upload attachments after the application exists.
      for (const file of files) {
        try {
          await applicationsService.uploadAttachment(created.id, file);
        } catch {
          // ignore individual upload failures
        }
      }
      return created;
    },
  });

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  const canSubmit =
    form.applicant_name.trim() &&
    form.applicant_email.trim() &&
    form.org_name.trim() &&
    !mutation.isPending;

  if (mutation.isSuccess) {
    return (
      <div className="page" style={{ maxWidth: 560, margin: '40px auto' }}>
        <div className="card" style={{ padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>✅</div>
          <h2>{t('apply.sentTitle', 'Demande envoyée')}</h2>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            {t(
              'apply.sentBody',
              "Votre demande a été reçue. Un administrateur de la plateforme la vérifiera. Vous recevrez un code d'invitation par email une fois approuvée.",
            )}
          </p>
          <Link className="btn btn-primary" to="/login" style={{ marginTop: 12 }}>
            {t('apply.backToLogin', 'Retour à la connexion')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page" style={{ maxWidth: 600, margin: '40px auto' }}>
      <div className="card" style={{ padding: 24 }}>
        <h1 style={{ marginTop: 0 }}>{t('apply.title', "Demande d'inscription")}</h1>
        <p style={{ color: 'var(--color-text-secondary)', marginTop: 0 }}>
          {t(
            'apply.subtitle',
            "Choisissez le type d'établissement. Votre demande sera examinée avant activation.",
          )}
        </p>

        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          <button
            type="button"
            className={`btn ${type === 'formal_school' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setType('formal_school')}
          >
            🏫 {t('apply.formal', 'École formelle')}
          </button>
          <button
            type="button"
            className={`btn ${type === 'micro_school' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setType('micro_school')}
          >
            🏡 {t('apply.micro', 'Micro-école / Éducateur')}
          </button>
        </div>

        <Field label={t('apply.yourName', 'Votre nom')} value={form.applicant_name} onChange={(v) => set('applicant_name', v)} required />
        <Field label={t('apply.email', 'Email')} type="email" value={form.applicant_email} onChange={(v) => set('applicant_email', v)} required />
        <Field label={t('apply.phone', 'Téléphone')} value={form.applicant_phone} onChange={(v) => set('applicant_phone', v)} />
        <Field label={t('apply.city', 'Ville')} value={form.city} onChange={(v) => set('city', v)} />
        <Field
          label={type === 'formal_school' ? t('apply.schoolName', "Nom de l'école") : t('apply.microName', 'Nom de la micro-école')}
          value={form.org_name}
          onChange={(v) => set('org_name', v)}
          required
        />

        {type === 'formal_school' ? (
          <>
            <Field label={t('apply.address', 'Adresse')} value={form.address} onChange={(v) => set('address', v)} />
            <Field label={t('apply.level', 'Niveau (ex. primaire, collège)')} value={form.level_band} onChange={(v) => set('level_band', v)} />
          </>
        ) : (
          <>
            <Field label={t('apply.neighborhood', 'Quartier')} value={form.neighborhood} onChange={(v) => set('neighborhood', v)} />
            <Field label={t('apply.address', 'Adresse')} value={form.address} onChange={(v) => set('address', v)} />
            <Field label={t('apply.capacity', 'Capacité (enfants)')} type="number" value={form.max_capacity} onChange={(v) => set('max_capacity', v)} />
          </>
        )}

        <div className="form-field" style={{ marginBottom: 16 }}>
          <label>{t('apply.notes', 'Message (optionnel)')}</label>
          <textarea
            className="filter-input"
            rows={3}
            value={form.notes}
            onChange={(e) => set('notes', e.target.value)}
            style={{ width: '100%' }}
          />
        </div>

        <div className="form-field" style={{ marginBottom: 16 }}>
          <label>{t('apply.documents', 'Documents / photos (optionnel)')}</label>
          <input
            type="file"
            multiple
            accept="image/*,application/pdf"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
          {files.length > 0 && (
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', display: 'block', marginTop: 4 }}>
              {files.length} {t('apply.fileSelected', 'fichier(s) sélectionné(s)')}
            </span>
          )}
        </div>

        {mutation.isError && (
          <p style={{ color: 'var(--color-danger)', fontSize: 13 }}>
            {(mutation.error as Error)?.message || t('apply.error', "L'envoi a échoué.")}
          </p>
        )}

        <button
          type="button"
          className="btn btn-primary"
          disabled={!canSubmit}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? t('apply.sending', 'Envoi…') : t('apply.submit', 'Envoyer la demande')}
        </button>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  required = false,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <div className="form-field" style={{ marginBottom: 12 }}>
      <label>
        {label}
        {required ? ' *' : ''}
      </label>
      <input
        className="filter-input"
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: '100%' }}
      />
    </div>
  );
}
