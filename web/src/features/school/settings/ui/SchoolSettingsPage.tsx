import { useEffect, useState, type FormEvent } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthContext';
import { ErrorBanner, LoadingState } from '@/shared/ui';
import { schoolsService } from '@/features/school/settings/api/schools.api';

export function SchoolSettingsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [form, setForm] = useState({ name: '', address: '', city: '', phone: '' });
  const [saved, setSaved] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  const schoolQuery = useQuery({
    queryKey: ['schools', user?.school_id],
    queryFn: async () => (await schoolsService.getSchool(user!.school_id)).data,
    enabled: Boolean(user?.school_id),
  });

  const saveMutation = useMutation({
    mutationFn: async () =>
      (
        await schoolsService.updateSchool(user!.school_id, {
          name: form.name.trim(),
          address: form.address.trim() || null,
          city: form.city.trim() || null,
          phone: form.phone.trim() || null,
        })
      ).data,
    onSuccess: async (school) => {
      setForm({
        name: school.name,
        address: school.address || '',
        city: school.city || '',
        phone: school.phone || '',
      });
      setSaved(true);
    },
    onError: (error) => setPageError(error instanceof Error ? error.message : t('app.error')),
  });

  useEffect(() => {
    if (!schoolQuery.data) {
      return;
    }

    setForm({
      name: schoolQuery.data.name,
      address: schoolQuery.data.address || '',
      city: schoolQuery.data.city || '',
      phone: schoolQuery.data.phone || '',
    });
  }, [schoolQuery.data]);

  if (!user) {
    return null;
  }

  if (schoolQuery.isLoading) {
    return <LoadingState />;
  }

  function updateField(key: keyof typeof form, value: string) {
    setSaved(false);
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPageError(null);
    await saveMutation.mutateAsync();
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('admin.settings.title')}</h1>
        <p className="page-subtitle">{t('admin.settings.subtitle')}</p>
      </div>

      <ErrorBanner
        error={pageError ?? (schoolQuery.error instanceof Error ? schoolQuery.error.message : null)}
        onDismiss={() => setPageError(null)}
        onRetry={schoolQuery.error ? () => void schoolQuery.refetch() : undefined}
      />

      <form className="card settings-card" style={{ maxWidth: 720 }} onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="school-name">{t('admin.settings.schoolName')}</label>
          <input
            id="school-name"
            className="input"
            value={form.name}
            onChange={(event) => updateField('name', event.target.value)}
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="school-address">{t('admin.settings.address')}</label>
          <input
            id="school-address"
            className="input"
            value={form.address}
            onChange={(event) => updateField('address', event.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="school-city">{t('admin.settings.city')}</label>
          <input
            id="school-city"
            className="input"
            value={form.city}
            onChange={(event) => updateField('city', event.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="school-phone">{t('admin.settings.phone')}</label>
          <input
            id="school-phone"
            className="input"
            value={form.phone}
            onChange={(event) => updateField('phone', event.target.value)}
          />
        </div>

        <div
          style={{
            display: 'grid',
            gap: 8,
            margin: '12px 0 20px',
            color: 'var(--color-text-secondary)',
            fontSize: 13,
          }}
        >
          <span>
            {t('admin.settings.schoolId')}: {user.school_id}
          </span>
          <span>
            {t('admin.settings.schoolCode')}: {schoolQuery.data?.code || '—'}
          </span>
        </div>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button type="submit" className="btn btn-primary" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? t('app.loading') : t('app.save')}
          </button>
          {saved ? (
            <span className="save-state save-state--success">{t('admin.settings.saved')}</span>
          ) : null}
        </div>
      </form>
    </div>
  );
}
