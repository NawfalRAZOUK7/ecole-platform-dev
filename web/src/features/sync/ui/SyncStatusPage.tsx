import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/shared/i18n';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, LoadingState, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { SyncCheckpoint, SyncDevice } from '../model/sync.types';
import { useSyncCheckpoints, useSyncDevices, useSyncHealth, useSyncStatus } from '../model/useSync';

type DeviceRow = SyncDevice & Record<string, unknown>;
type CheckpointRow = SyncCheckpoint & Record<string, unknown>;

export function SyncStatusPage() {
  const { t, i18n } = useTranslation();
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const devicesQuery = useSyncDevices();
  const statusQuery = useSyncStatus(selectedDeviceId);
  const healthQuery = useSyncHealth(selectedDeviceId);
  const checkpointsQuery = useSyncCheckpoints(selectedDeviceId);

  useEffect(() => {
    if (!selectedDeviceId && (devicesQuery.data?.length ?? 0) > 0) {
      setSelectedDeviceId(devicesQuery.data?.[0].id ?? '');
    }
  }, [devicesQuery.data, selectedDeviceId]);

  const deviceColumns: ColumnDef<DeviceRow>[] = useMemo(
    () => [
      { key: 'device_name', header: 'sync.deviceName' },
      { key: 'device_type', header: 'sync.deviceType' },
      {
        key: 'last_seen_at',
        header: 'sync.lastSeen',
        render: (value) =>
          formatDate(String(value), i18n.language, { dateStyle: 'short', timeStyle: 'short' }),
      },
      {
        key: 'is_active',
        header: 'sync.active',
        render: (value) => (value ? t('app.confirm') : t('app.cancel')),
      },
    ],
    [i18n.language, t],
  );

  const checkpointColumns: ColumnDef<CheckpointRow>[] = useMemo(
    () => [
      { key: 'last_entity_type', header: 'sync.lastEntityType' },
      { key: 'records_synced', header: 'sync.recordsSynced' },
      {
        key: 'last_sync_at',
        header: 'sync.lastCheckpoint',
        render: (value) =>
          formatDate(String(value), i18n.language, { dateStyle: 'short', timeStyle: 'short' }),
      },
    ],
    [i18n.language],
  );

  if (devicesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('sync.title')}</h1>
        <p className="page-subtitle">{t('sync.subtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          devicesQuery.error ?? statusQuery.error ?? healthQuery.error ?? checkpointsQuery.error,
          t('app.error'),
        )}
      />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={selectedDeviceId}
          onChange={(event) => setSelectedDeviceId(event.target.value)}
        >
          {(devicesQuery.data ?? []).map((device) => (
            <option key={device.id} value={device.id}>
              {device.device_name} · {device.device_type}
            </option>
          ))}
        </select>
      </div>

      <div className="stats-grid">
        <StatCard label="sync.pending" value={statusQuery.data?.pending_count ?? 0} icon="⏳" />
        <StatCard label="sync.synced" value={statusQuery.data?.synced_count ?? 0} icon="✅" />
        <StatCard label="sync.conflicts" value={statusQuery.data?.conflict_count ?? 0} icon="⚠️" />
        <StatCard label="sync.health" value={healthQuery.data?.health || '-'} icon="💓" />
      </div>

      <DataTable
        columns={deviceColumns}
        data={(devicesQuery.data ?? []) as DeviceRow[]}
        loading={devicesQuery.isLoading}
        emptyMessage="sync.empty"
        ariaLabel={t('sync.devices')}
      />

      <DataTable
        columns={checkpointColumns}
        data={(checkpointsQuery.data ?? []) as CheckpointRow[]}
        loading={checkpointsQuery.isLoading}
        emptyMessage="sync.empty"
        ariaLabel={t('sync.checkpoints')}
      />
    </div>
  );
}
