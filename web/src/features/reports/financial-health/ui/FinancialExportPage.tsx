import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/shared/i18n';
import { ErrorBanner, LoadingState, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useFinancialDashboard,
  useFinancialExport,
  useFinancialTrends,
} from '../model/useFinancialHealth';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
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

function buildExcelBlob(params: {
  schoolId: string;
  fromDate: string;
  toDate: string;
  retentionRows: Array<{ period: string; rate: number }>;
  snapshotRows: Array<{ date: string; receivable: number; collected: number; overdue: number }>;
  cashflowRows: Array<{
    month: string;
    expectedIncome: number;
    expectedExpenses: number;
    net: number;
  }>;
}) {
  const rows = [
    ['section', 'label', 'value_1', 'value_2', 'value_3'],
    ['meta', 'school_id', params.schoolId, '', ''],
    ['meta', 'from_date', params.fromDate || '', '', ''],
    ['meta', 'to_date', params.toDate || '', '', ''],
    ...params.retentionRows.map((row) => ['retention', row.period, String(row.rate), '', '']),
    ...params.snapshotRows.map((row) => [
      'snapshot',
      row.date,
      String(row.receivable),
      String(row.collected),
      String(row.overdue),
    ]),
    ...params.cashflowRows.map((row) => [
      'cashflow',
      row.month,
      String(row.expectedIncome),
      String(row.expectedExpenses),
      String(row.net),
    ]),
  ];

  const content = rows.map((row) => row.join('\t')).join('\n');
  return new Blob([content], {
    type: 'application/vnd.ms-excel;charset=utf-8',
  });
}

export function FinancialExportPage() {
  const { t, i18n } = useTranslation();
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [format, setFormat] = useState<'pdf' | 'excel'>('pdf');
  const dashboardQuery = useFinancialDashboard();
  const trendsQuery = useFinancialTrends(24);
  const exportMutation = useFinancialExport();

  const filteredData = useMemo(() => {
    const retentionRows = (trendsQuery.data?.retention_metrics ?? []).map((item) => ({
      period: `${item.academic_year_from} → ${item.academic_year_to}`,
      rate: item.retention_rate,
    }));

    const snapshotRows = (trendsQuery.data?.snapshots ?? [])
      .filter((snapshot) => isWithinRange(snapshot.snapshot_date, fromDate, toDate))
      .map((snapshot) => ({
        date: snapshot.snapshot_date,
        receivable: snapshot.total_receivable,
        collected: snapshot.total_collected,
        overdue: snapshot.overdue_amount,
      }));

    const cashflowRows = (trendsQuery.data?.cashflow ?? [])
      .filter((item) => isWithinRange(item.forecast_month, fromDate, toDate))
      .map((item) => ({
        month: item.forecast_month,
        expectedIncome: item.expected_income,
        expectedExpenses: item.expected_expenses,
        net: item.expected_income - item.expected_expenses,
      }));

    return { retentionRows, snapshotRows, cashflowRows };
  }, [
    fromDate,
    toDate,
    trendsQuery.data?.cashflow,
    trendsQuery.data?.retention_metrics,
    trendsQuery.data?.snapshots,
  ]);

  async function handleExport() {
    if (format === 'pdf') {
      const result = await exportMutation.mutateAsync('pdf');
      downloadBlob(result.blob, `financial-health-${fromDate || 'all'}-${toDate || 'all'}.pdf`);
      return;
    }

    const blob = buildExcelBlob({
      schoolId: dashboardQuery.data?.school_id ?? '',
      fromDate,
      toDate,
      retentionRows: filteredData.retentionRows,
      snapshotRows: filteredData.snapshotRows,
      cashflowRows: filteredData.cashflowRows,
    });

    downloadBlob(blob, `financial-health-${fromDate || 'all'}-${toDate || 'all'}.xls`);
  }

  if (
    (dashboardQuery.isLoading && !dashboardQuery.data) ||
    (trendsQuery.isLoading && !trendsQuery.data)
  ) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('financialHealth.exportTitle')}</h1>
        <p className="page-subtitle">{t('financialHealth.exportSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          dashboardQuery.error ?? trendsQuery.error ?? exportMutation.error,
          t('app.error'),
        )}
      />

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
        <select
          className="filter-select"
          value={format}
          onChange={(event) => setFormat(event.target.value as 'pdf' | 'excel')}
        >
          <option value="pdf">{t('financialHealth.pdf')}</option>
          <option value="excel">{t('financialHealth.excel')}</option>
        </select>
        <button type="button" className="btn btn-primary" onClick={() => void handleExport()}>
          {exportMutation.isPending ? t('app.loading') : t('financialHealth.generateReport')}
        </button>
      </div>

      <div className="stats-grid">
        <StatCard
          label="financialHealth.retentionSeries"
          value={filteredData.retentionRows.length}
          icon="📊"
        />
        <StatCard
          label="financialHealth.snapshotSeries"
          value={filteredData.snapshotRows.length}
          icon="📸"
        />
        <StatCard
          label="financialHealth.cashflowSeries"
          value={filteredData.cashflowRows.length}
          icon="💹"
        />
      </div>

      <div className="card">
        <h2>{t('financialHealth.exportPreview')}</h2>
        <p>
          {t('financialHealth.previewRange')}:{' '}
          {fromDate ? formatDate(fromDate, i18n.language) : t('financialHealth.allDates')} →{' '}
          {toDate ? formatDate(toDate, i18n.language) : t('financialHealth.allDates')}
        </p>
        <p>{t('financialHealth.exportHint')}</p>
      </div>
    </div>
  );
}
