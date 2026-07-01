import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { formatCurrency, formatDate } from '@/shared/i18n';
import { DataTable, ErrorBanner, LoadingState } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { FinancialSnapshot } from '../model/financial-health.types';
import { useFinancialTrends } from '../model/useFinancialHealth';

type SnapshotRow = FinancialSnapshot & Record<string, unknown>;

function downloadSnapshotCsv(snapshot: FinancialSnapshot) {
  const rows = [
    [
      'snapshot_date',
      'collection_rate',
      'total_receivable',
      'total_collected',
      'overdue_amount',
      'overdue_count',
      'avg_payment_delay_days',
    ],
    [
      snapshot.snapshot_date,
      String(snapshot.collection_rate),
      String(snapshot.total_receivable),
      String(snapshot.total_collected),
      String(snapshot.overdue_amount),
      String(snapshot.overdue_count),
      String(snapshot.avg_payment_delay_days ?? ''),
    ],
  ];

  const csv = rows
    .map((row) => row.map((value) => `"${String(value).split('"').join('""')}"`).join(','))
    .join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `financial-snapshot-${snapshot.snapshot_date}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function isWithinRange(dateValue: string, startDate: string, endDate: string) {
  const value = Date.parse(dateValue);
  if (Number.isNaN(value)) {
    return false;
  }

  if (startDate) {
    const start = Date.parse(startDate);
    if (!Number.isNaN(start) && value < start) {
      return false;
    }
  }

  if (endDate) {
    const end = Date.parse(endDate);
    if (!Number.isNaN(end) && value > end) {
      return false;
    }
  }

  return true;
}

export function FinancialSnapshotsPage() {
  const { t, i18n } = useTranslation();
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const trendsQuery = useFinancialTrends(24);

  const rows = useMemo(
    () =>
      (trendsQuery.data?.snapshots ?? []).filter((snapshot) =>
        isWithinRange(snapshot.snapshot_date, fromDate, toDate),
      ),
    [fromDate, toDate, trendsQuery.data?.snapshots],
  );

  const columns: ColumnDef<SnapshotRow>[] = useMemo(
    () => [
      {
        key: 'snapshot_date',
        header: 'financialHealth.snapshotDate',
        render: (value) => formatDate(String(value), i18n.language),
      },
      {
        key: 'collection_rate',
        header: 'financialHealth.collectionRate',
        render: (value) => `${Number(value).toFixed(1)}%`,
      },
      {
        key: 'total_receivable',
        header: 'financialHealth.totalReceivable',
        render: (value) => formatCurrency(Number(value)),
      },
      {
        key: 'total_collected',
        header: 'financialHealth.totalCollected',
        render: (value) => formatCurrency(Number(value)),
      },
      {
        key: 'overdue_amount',
        header: 'financialHealth.overdueAmount',
        render: (value) => formatCurrency(Number(value)),
      },
      { key: 'overdue_count', header: 'financialHealth.overdueCount' },
      {
        key: 'id',
        header: 'financialHealth.export',
        sortable: false,
        render: (_value, row) => (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => downloadSnapshotCsv(row)}
          >
            {t('financialHealth.exportSnapshot')}
          </button>
        ),
      },
    ],
    [i18n.language, t],
  );

  if (trendsQuery.isLoading && !trendsQuery.data) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('financialHealth.snapshotsTitle')}</h1>
        <p className="page-subtitle">{t('financialHealth.snapshotsSubtitle')}</p>
      </div>

      <ErrorBanner error={toBannerError(trendsQuery.error, t('app.error'))} />

      <div className="filters-bar">
        <input
          className="filter-input"
          type="date"
          value={fromDate}
          onChange={(event) => setFromDate(event.target.value)}
        />
        <input
          className="filter-input"
          type="date"
          value={toDate}
          onChange={(event) => setToDate(event.target.value)}
        />
      </div>

      <DataTable
        columns={columns}
        data={rows as SnapshotRow[]}
        loading={trendsQuery.isLoading}
        emptyMessage="financialHealth.emptySnapshots"
        ariaLabel={t('financialHealth.snapshotsTitle')}
      />
    </div>
  );
}
