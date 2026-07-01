import { useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { getAccessToken } from '@/core/api/client';
import { EmptyState } from './EmptyState';
import { Skeleton } from './Skeleton';

type SortDirection = 'asc' | 'desc' | null;
type ExportFormat = 'csv' | 'xlsx';

export interface ColumnDef<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => ReactNode;
  sortable?: boolean;
  width?: string;
}

export interface DataTableExportOptions {
  entity: string;
  filters?: Record<string, boolean | number | string | undefined>;
  filename?: string;
  formats?: ExportFormat[];
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  loading: boolean;
  emptyMessage: string;
  onRowClick?: (row: T) => void;
  sortable?: boolean;
  ariaLabel?: string;
  exportOptions?: DataTableExportOptions;
}

function compareValues(left: unknown, right: unknown) {
  if (typeof left === 'number' && typeof right === 'number') {
    return left - right;
  }

  return String(left ?? '').localeCompare(String(right ?? ''));
}

function getDownloadName(
  format: ExportFormat,
  options: DataTableExportOptions,
  response: Response,
) {
  const disposition = response.headers.get('content-disposition');
  const filenameMatch = disposition?.match(/filename="?([^"]+)"?/i);
  if (filenameMatch?.[1]) {
    return filenameMatch[1];
  }

  const baseName = options.filename || options.entity;
  return `${baseName}.${format}`;
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  loading,
  emptyMessage,
  onRowClick,
  sortable = true,
  ariaLabel,
  exportOptions,
}: DataTableProps<T>) {
  const { t } = useTranslation();
  const [sortKey, setSortKey] = useState<keyof T | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [exporting, setExporting] = useState<ExportFormat | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const sortedData = useMemo(() => {
    if (!sortKey || !sortDirection) {
      return data;
    }

    return [...data].sort((left, right) => {
      const result = compareValues(left[sortKey], right[sortKey]);
      return sortDirection === 'asc' ? result : -result;
    });
  }, [data, sortDirection, sortKey]);

  function toggleSort(column: ColumnDef<T>) {
    if (!sortable || column.sortable === false) {
      return;
    }

    if (sortKey !== column.key) {
      setSortKey(column.key);
      setSortDirection('asc');
      return;
    }

    if (sortDirection === 'asc') {
      setSortDirection('desc');
      return;
    }

    if (sortDirection === 'desc') {
      setSortDirection(null);
      setSortKey(null);
      return;
    }

    setSortDirection('asc');
  }

  async function handleExport(format: ExportFormat) {
    if (!exportOptions) {
      return;
    }

    const token = getAccessToken();
    const query = new URLSearchParams({ entity: exportOptions.entity });
    const filters = Object.fromEntries(
      Object.entries(exportOptions.filters || {}).filter(
        ([, value]) => value !== undefined && value !== '',
      ),
    );
    if (Object.keys(filters).length > 0) {
      query.set('filters', JSON.stringify(filters));
    }

    setExportError(null);
    setExporting(format);

    try {
      const response = await fetch(`/api/v1/export/${format}?${query.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        credentials: 'include',
      });

      if (!response.ok) {
        const failure = await response.text();
        throw new Error(failure || t('app.error'));
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = getDownloadName(format, exportOptions, response);
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setExportError(error instanceof Error ? error.message : t('app.error'));
    } finally {
      setExporting(null);
    }
  }

  if (!loading && data.length === 0) {
    return <EmptyState message={t(emptyMessage)} />;
  }

  return (
    <div>
      {exportOptions ? (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: 12,
            marginBottom: 12,
            alignItems: 'center',
          }}
        >
          <div style={{ color: 'var(--color-error)', fontSize: 13 }}>{exportError}</div>
          <details>
            <summary className="btn btn-secondary btn-sm" style={{ cursor: 'pointer' }}>
              {exporting ? t('app.loading') : t('exports.title')}
            </summary>
            <div
              className="card"
              style={{
                position: 'absolute',
                marginTop: 8,
                padding: 8,
                display: 'grid',
                gap: 8,
                minWidth: 160,
                zIndex: 5,
              }}
            >
              {(exportOptions.formats || ['csv', 'xlsx']).map((format) => (
                <button
                  key={format}
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={Boolean(exporting)}
                  onClick={() => void handleExport(format)}
                >
                  {t(`exports.${format}`)}
                </button>
              ))}
            </div>
          </details>
        </div>
      ) : null}
      <div className="data-table__scroll">
        <table
          className="data-table"
          role="table"
          aria-label={ariaLabel || t('app.table', { defaultValue: 'Table' })}
        >
          <thead className="data-table__head" role="rowgroup">
            <tr className="data-table__header-row" role="row">
              {columns.map((column) => {
                const isSortable = sortable && column.sortable !== false;
                const isActive = sortKey === column.key;
                const ariaSort =
                  !isSortable || !isActive || !sortDirection
                    ? 'none'
                    : sortDirection === 'asc'
                      ? 'ascending'
                      : 'descending';

                return (
                  <th
                    key={String(column.key)}
                    className="data-table__header"
                    role="columnheader"
                    aria-sort={ariaSort}
                    style={{ width: column.width }}
                    scope="col"
                  >
                    <button
                      type="button"
                      className={`data-table__sort ${isActive ? 'data-table__sort--active' : ''}`}
                      onClick={() => toggleSort(column)}
                      disabled={!isSortable}
                    >
                      <span>{t(column.header)}</span>
                      {isSortable && (
                        <span className="data-table__sort-icon" aria-hidden="true">
                          {isActive && sortDirection === 'desc' ? '↓' : '↑'}
                        </span>
                      )}
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="data-table__body" role="rowgroup">
            {loading
              ? Array.from({ length: 3 }, (_, index) => (
                  <tr key={`loading-${index}`} className="data-table__row" role="row">
                    <td className="data-table__cell" role="cell" colSpan={columns.length}>
                      <Skeleton variant="table-row" count={1} />
                    </td>
                  </tr>
                ))
              : sortedData.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className={`data-table__row ${onRowClick ? 'data-table__row--clickable' : ''}`}
                    role="row"
                    tabIndex={onRowClick ? 0 : undefined}
                    onClick={() => onRowClick?.(row)}
                    onKeyDown={(event) => {
                      if (onRowClick && (event.key === 'Enter' || event.key === ' ')) {
                        event.preventDefault();
                        onRowClick(row);
                      }
                    }}
                  >
                    {columns.map((column) => (
                      <td key={String(column.key)} className="data-table__cell" role="cell">
                        {column.render
                          ? column.render(row[column.key], row)
                          : String(row[column.key] ?? '-')}
                      </td>
                    ))}
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
