import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';
import type {
  DeviceItem,
  NotificationDigestResponse,
  NotificationPreference,
  NotificationPreferencesResponse,
} from './types';

const CATEGORY_ORDER = ['academic', 'billing', 'attendance', 'system', 'announcement'];

export function NotificationSettingsPage() {
  const { t, i18n } = useTranslation();
  const [preferences, setPreferences] = useState<NotificationPreference[]>([]);
  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [digestFrequency, setDigestFrequency] = useState('off');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const channels = useMemo(
    () => Array.from(new Set(preferences.map((preference) => preference.channel))),
    [preferences]
  );

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [prefsResp, digestResp, devicesResp] = await Promise.all([
          api.get<NotificationPreferencesResponse>('/notifications/preferences'),
          api.get<NotificationDigestResponse>('/notifications/digest/preferences'),
          api.list<DeviceItem>('/devices'),
        ]);
        setPreferences(prefsResp.data.preferences);
        setDigestFrequency(digestResp.data.digest_frequency);
        setDevices(devicesResp.data);
        setError(null);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : t('app.error'));
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [t]);

  function updatePreference(category: string, channel: string, enabled: boolean) {
    setSaved(false);
    setPreferences((prev) => prev.map((preference) => (
      preference.category === category && preference.channel === channel
        ? { ...preference, enabled }
        : preference
    )));
  }

  async function handleSave() {
    setSaving(true);
    try {
      await Promise.all([
        api.post('/notifications/preferences', { preferences }),
        api.post('/notifications/digest/preferences', { digest_frequency: digestFrequency }),
      ]);
      setSaved(true);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSaving(false);
    }
  }

  async function handleRemoveDevice(deviceId: string) {
    try {
      await api.delete(`/devices/${deviceId}`);
      setDevices((prev) => prev.filter((device) => device.id !== deviceId));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  if (loading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('notifications.settingsTitle')}</h1>
          <p className="page-subtitle">{t('notifications.settingsSubtitle')}</p>
        </div>
        <div className="page-actions">
          {saved && <span className="save-state save-state--success">{t('notifications.saved')}</span>}
          <button className="btn btn-primary" onClick={() => void handleSave()} disabled={saving}>
            {saving ? t('app.loading') : t('app.save')}
          </button>
        </div>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => void handleSave()} />

      <section className="card settings-card">
        <div className="settings-card__header">
          <h2>{t('notifications.preferenceMatrixTitle')}</h2>
          <p>{t('notifications.preferenceMatrixSubtitle')}</p>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('notifications.filters.category')}</th>
                {channels.map((channel) => (
                  <th key={channel}>{t(`notifications.channels.${channel}`)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CATEGORY_ORDER.map((category) => (
                <tr key={category}>
                  <td>{t(`notifications.categories.${category}`)}</td>
                  {channels.map((channel) => {
                    const preference = preferences.find(
                      (item) => item.category === category && item.channel === channel
                    );
                    return (
                      <td key={`${category}-${channel}`}>
                        <label className="switch-field">
                          <input
                            type="checkbox"
                            checked={preference?.enabled ?? false}
                            onChange={(event) => updatePreference(category, channel, event.target.checked)}
                          />
                          <span>{preference?.enabled ? t('notifications.enabled') : t('notifications.disabled')}</span>
                        </label>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card settings-card">
        <div className="settings-card__header">
          <h2>{t('notifications.digestTitle')}</h2>
          <p>{t('notifications.digestSubtitle')}</p>
        </div>
        <select
          className="filter-select"
          value={digestFrequency}
          onChange={(event) => {
            setSaved(false);
            setDigestFrequency(event.target.value);
          }}
        >
          <option value="off">{t('notifications.digest.off')}</option>
          <option value="daily">{t('notifications.digest.daily')}</option>
          <option value="weekly">{t('notifications.digest.weekly')}</option>
        </select>
      </section>

      <section className="card settings-card">
        <div className="settings-card__header">
          <h2>{t('notifications.devicesTitle')}</h2>
          <p>{t('notifications.devicesSubtitle')}</p>
        </div>

        {devices.length === 0 ? (
          <EmptyState message={t('notifications.noDevices')} icon="📱" />
        ) : (
          <div className="card-list">
            {devices.map((device) => (
              <div key={device.id} className="device-card">
                <div>
                  <strong>{device.device_name || t('notifications.unknownDevice')}</strong>
                  <p>{t(`notifications.devicePlatforms.${device.platform}`)}</p>
                  <p>{device.token_preview}</p>
                  <p>
                    {t('notifications.lastSeen')}:{' '}
                    {formatDate(device.last_active_at, i18n.language, {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </p>
                </div>
                <button className="btn btn-secondary" onClick={() => void handleRemoveDevice(device.id)}>
                  {t('notifications.removeDevice')}
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
