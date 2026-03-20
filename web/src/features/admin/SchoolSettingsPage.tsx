/**
 * Admin School Settings page — school name, timezone, notification preferences.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Client-side settings stored in localStorage until backend settings endpoint is available.
 */

import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';

const STORAGE_KEY = 'ecole_school_settings';

interface SchoolSettings {
  school_name: string;
  timezone: string;
  notification_email: boolean;
  notification_push: boolean;
  notification_sms: boolean;
}

function loadSettings(): SchoolSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return JSON.parse(stored);
  } catch { /* ignore */ }
  return {
    school_name: '',
    timezone: 'Africa/Casablanca',
    notification_email: true,
    notification_push: true,
    notification_sms: false,
  };
}

function saveSettings(settings: SchoolSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

const TIMEZONES = [
  'Africa/Casablanca',
  'Europe/Paris',
  'Europe/London',
  'UTC',
];

export function SchoolSettingsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [settings, setSettings] = useState<SchoolSettings>(loadSettings);
  const [saved, setSaved] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    saveSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function update(key: keyof SchoolSettings, value: string | boolean) {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.settings.title')}</h1>

      <div className="card" style={{ maxWidth: 600 }}>
        <form onSubmit={handleSubmit}>
          <div className="settings-form">
            <div className="form-field">
              <label htmlFor="school_name">{t('admin.settings.schoolName')}</label>
              <input
                id="school_name"
                type="text"
                value={settings.school_name}
                onChange={(e) => update('school_name', e.target.value)}
                placeholder={t('admin.settings.schoolNamePlaceholder')}
              />
            </div>

            <div className="form-field">
              <label>{t('admin.settings.schoolId')}</label>
              <input type="text" value={user?.school_id || ''} disabled />
            </div>

            <div className="form-field">
              <label htmlFor="timezone">{t('admin.settings.timezone')}</label>
              <select
                id="timezone"
                className="filter-select"
                value={settings.timezone}
                onChange={(e) => update('timezone', e.target.value)}
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>

            <fieldset style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: 16, marginTop: 8 }}>
              <legend style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-secondary)', padding: '0 8px' }}>
                {t('admin.settings.notificationPrefs')}
              </legend>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={settings.notification_email}
                  onChange={(e) => update('notification_email', e.target.checked)}
                />
                {t('admin.settings.notifEmail')}
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={settings.notification_push}
                  onChange={(e) => update('notification_push', e.target.checked)}
                />
                {t('admin.settings.notifPush')}
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={settings.notification_sms}
                  onChange={(e) => update('notification_sms', e.target.checked)}
                />
                {t('admin.settings.notifSms')}
              </label>
            </fieldset>

            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button type="submit" className="btn btn-primary">
                {t('app.save')}
              </button>
              {saved && (
                <span style={{ color: 'var(--color-success)', alignSelf: 'center', fontSize: 14 }}>
                  {t('admin.settings.saved')}
                </span>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
