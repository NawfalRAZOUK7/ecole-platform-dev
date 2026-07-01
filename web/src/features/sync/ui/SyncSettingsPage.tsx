import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, LoadingState } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { SyncDevice } from '../model/sync.types';
import {
  useCreateSyncCheckpoint,
  usePullSyncChanges,
  usePushSyncChanges,
  useRegisterSyncDevice,
  useSyncDevices,
} from '../model/useSync';

const SYNC_SETTINGS_KEY = 'ecole.sync.settings';

type DeviceRow = SyncDevice & Record<string, unknown>;

export function SyncSettingsPage() {
  const { t } = useTranslation();
  const [deviceName, setDeviceName] = useState('');
  const [deviceType, setDeviceType] = useState<'browser' | 'mobile' | 'local_server'>('browser');
  const [firmwareVersion, setFirmwareVersion] = useState('1.0.0');
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [intervalMinutes, setIntervalMinutes] = useState('15');
  const [scope, setScope] = useState('attendance,grades,content');
  const devicesQuery = useSyncDevices();
  const registerDeviceMutation = useRegisterSyncDevice();
  const pushMutation = usePushSyncChanges();
  const pullMutation = usePullSyncChanges();
  const checkpointMutation = useCreateSyncCheckpoint();

  useEffect(() => {
    const rawValue = window.localStorage.getItem(SYNC_SETTINGS_KEY);
    if (!rawValue) {
      return;
    }

    try {
      const parsed = JSON.parse(rawValue);
      setIntervalMinutes(String(parsed.intervalMinutes ?? '15'));
      setScope(String(parsed.scope ?? 'attendance,grades,content'));
    } catch {
      // ignore malformed local settings
    }
  }, []);

  useEffect(() => {
    if (!selectedDeviceId && (devicesQuery.data?.length ?? 0) > 0) {
      setSelectedDeviceId(devicesQuery.data?.[0].id ?? '');
    }
  }, [devicesQuery.data, selectedDeviceId]);

  const deviceColumns: ColumnDef<DeviceRow>[] = useMemo(
    () => [
      { key: 'device_name', header: 'sync.deviceName' },
      { key: 'device_type', header: 'sync.deviceType' },
      { key: 'firmware_version', header: 'sync.firmwareVersion' },
      { key: 'is_active', header: 'sync.active', render: (value) => (value ? 'Yes' : 'No') },
    ],
    [],
  );

  async function handleSaveSettings() {
    window.localStorage.setItem(
      SYNC_SETTINGS_KEY,
      JSON.stringify({
        intervalMinutes,
        scope,
      }),
    );
  }

  async function handleRegisterDevice() {
    await registerDeviceMutation.mutateAsync({
      device_name: deviceName,
      device_type: deviceType,
      firmware_version: firmwareVersion,
    });
  }

  async function handleManualSync() {
    if (!selectedDeviceId) {
      return;
    }

    await pushMutation.mutateAsync({
      deviceId: selectedDeviceId,
      payload: {
        items: [
          {
            entity_type: 'settings',
            entity_id: selectedDeviceId,
            operation: 'update',
            payload: {
              intervalMinutes,
              scope,
            },
          },
        ],
      },
    });

    const pullResponse = await pullMutation.mutateAsync({ deviceId: selectedDeviceId });
    await checkpointMutation.mutateAsync({
      deviceId: selectedDeviceId,
      payload: {
        last_entity_type: pullResponse.data.changes[0]?.entity_type || 'settings',
        last_entity_id: pullResponse.data.changes[0]?.entity_id || selectedDeviceId,
        records_synced: pullResponse.data.changes.length,
      },
    });
  }

  if (devicesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('sync.settingsTitle')}</h1>
        <p className="page-subtitle">{t('sync.settingsSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          devicesQuery.error ??
            registerDeviceMutation.error ??
            pushMutation.error ??
            pullMutation.error ??
            checkpointMutation.error,
          t('app.error'),
        )}
      />

      <div className="card-list">
        <div className="card">
          <h2>{t('sync.configuration')}</h2>
          <div className="filters-bar">
            <input
              className="filter-input"
              aria-label={t('sync.intervalMinutes')}
              type="number"
              min="1"
              value={intervalMinutes}
              onChange={(event) => setIntervalMinutes(event.target.value)}
              placeholder={t('sync.intervalMinutes')}
            />
            <input
              className="filter-input"
              aria-label={t('sync.dataScope')}
              value={scope}
              onChange={(event) => setScope(event.target.value)}
              placeholder={t('sync.dataScope')}
            />
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void handleSaveSettings()}
            >
              {t('app.save')}
            </button>
          </div>
        </div>
        <div className="card">
          <h2>{t('sync.registerDevice')}</h2>
          <div className="filters-bar">
            <input
              className="filter-input"
              aria-label={t('sync.deviceName')}
              value={deviceName}
              onChange={(event) => setDeviceName(event.target.value)}
              placeholder={t('sync.deviceName')}
            />
            <select
              className="filter-select"
              aria-label={t('sync.deviceType')}
              value={deviceType}
              onChange={(event) =>
                setDeviceType(event.target.value as 'browser' | 'mobile' | 'local_server')
              }
            >
              <option value="browser">{t('sync.browser')}</option>
              <option value="mobile">{t('sync.mobile')}</option>
              <option value="local_server">{t('sync.localServer')}</option>
            </select>
            <input
              className="filter-input"
              aria-label={t('sync.firmwareVersion')}
              value={firmwareVersion}
              onChange={(event) => setFirmwareVersion(event.target.value)}
              placeholder={t('sync.firmwareVersion')}
            />
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void handleRegisterDevice()}
            >
              {t('sync.registerDevice')}
            </button>
          </div>
        </div>
        <div className="card">
          <h2>{t('sync.manualSync')}</h2>
          <div className="filters-bar">
            <select
              className="filter-select"
              aria-label={t('sync.devices')}
              value={selectedDeviceId}
              onChange={(event) => setSelectedDeviceId(event.target.value)}
            >
              {(devicesQuery.data ?? []).map((device) => (
                <option key={device.id} value={device.id}>
                  {device.device_name}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void handleManualSync()}
            >
              {t('sync.runNow')}
            </button>
          </div>
        </div>
      </div>

      <DataTable
        columns={deviceColumns}
        data={(devicesQuery.data ?? []) as DeviceRow[]}
        loading={devicesQuery.isLoading}
        emptyMessage="sync.empty"
        ariaLabel={t('sync.devices')}
      />
    </div>
  );
}
