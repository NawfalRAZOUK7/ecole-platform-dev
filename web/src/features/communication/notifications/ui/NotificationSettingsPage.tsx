import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiClientError, type ApiError } from '@/core/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';
import {
  useNotificationDevices,
  useNotificationDigestPreferences,
  useNotificationPreferences,
  useRemoveNotificationDevice,
  useSaveNotificationSettings,
} from '../model/useNotifications';
import type { DeviceItem, NotificationPreference } from '../model/types';

const CATEGORY_ORDER = ['academic', 'billing', 'attendance', 'system', 'announcement'];

function toBannerError(error: unknown, fallback: string): ApiError | string | null {
  if (!error) {
    return null;
  }
  if (error instanceof ApiClientError) {
    return error.apiError;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

export function NotificationSettingsPage() {
  const { t, i18n } = useTranslation();
  const preferencesQuery = useNotificationPreferences();
  const digestQuery = useNotificationDigestPreferences();
  const devicesQuery = useNotificationDevices();
  const saveSettingsMutation = useSaveNotificationSettings();
  const removeDeviceMutation = useRemoveNotificationDevice();
  const [preferences, setPreferences] = useState<NotificationPreference[]>(
    () => preferencesQuery.data ?? [],
  );
  const [digestFrequency, setDigestFrequency] = useState(
    () => digestQuery.data?.digest_frequency ?? 'off',
  );
  const [saved, setSaved] = useState(false);
  const [dismissedError, setDismissedError] = useState(false);

  const devices: DeviceItem[] = devicesQuery.data ?? [];
  const loading =
    preferencesQuery.isLoading ||
    digestQuery.isLoading ||
    devicesQuery.isLoading ||
    !preferencesQuery.data ||
    !digestQuery.data ||
    !devicesQuery.data;

  const channels = useMemo(
    () => Array.from(new Set(preferences.map((preference) => preference.channel))),
    [preferences],
  );
  const loadError = preferencesQuery.error ?? digestQuery.error ?? devicesQuery.error;
  const actionError = saveSettingsMutation.error ?? removeDeviceMutation.error;
  const bannerError = useMemo(
    () => toBannerError(loadError ?? actionError, t('app.error')),
    [actionError, loadError, t],
  );

  useEffect(() => {
    if (preferencesQuery.data) {
      setPreferences(preferencesQuery.data);
    }
  }, [preferencesQuery.data]);

  useEffect(() => {
    if (digestQuery.data) {
      setDigestFrequency(digestQuery.data.digest_frequency);
    }
  }, [digestQuery.data]);

  useEffect(() => {
    setDismissedError(false);
  }, [bannerError]);

  function updatePreference(category: string, channel: string, enabled: boolean) {
    setSaved(false);
    setPreferences((prev) =>
      prev.map((preference) =>
        preference.category === category && preference.channel === channel
          ? { ...preference, enabled }
          : preference,
      ),
    );
  }

  async function handleSave() {
    await saveSettingsMutation.mutateAsync({ preferences, digestFrequency });
    setSaved(true);
  }

  async function handleRemoveDevice(deviceId: string) {
    await removeDeviceMutation.mutateAsync(deviceId);
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
          {saved && (
            <span className="save-state save-state--success">{t('notifications.saved')}</span>
          )}
          <button
            className="btn btn-primary"
            onClick={() => void handleSave()}
            disabled={saveSettingsMutation.isPending}
          >
            {saveSettingsMutation.isPending ? t('app.loading') : t('app.save')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={dismissedError ? null : bannerError}
        onDismiss={() => setDismissedError(true)}
        onRetry={
          loadError
            ? () =>
                void Promise.all([
                  preferencesQuery.refetch(),
                  digestQuery.refetch(),
                  devicesQuery.refetch(),
                ])
            : undefined
        }
      />

      <section className="card settings-card">
        <div className="settings-card__header">
          <h2>{t('notifications.preferenceMatrixTitle')}</h2>
          <p>{t('notifications.preferenceMatrixSubtitle')}</p>
          <p>{t('notifications.consentSync')}</p>
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
                      (item) => item.category === category && item.channel === channel,
                    );
                    return (
                      <td key={`${category}-${channel}`}>
                        <label className="switch-field">
                          <input
                            type="checkbox"
                            checked={preference?.enabled ?? false}
                            onChange={(event) =>
                              updatePreference(category, channel, event.target.checked)
                            }
                          />
                          <span>
                            {preference?.enabled
                              ? t('notifications.enabled')
                              : t('notifications.disabled')}
                          </span>
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
                <button
                  className="btn btn-secondary"
                  onClick={() => void handleRemoveDevice(device.id)}
                  disabled={removeDeviceMutation.isPending}
                >
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
