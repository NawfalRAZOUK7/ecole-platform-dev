import { useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { EmptyState } from './EmptyState';
import { Skeleton } from './Skeleton';

type SortDirection = 'asc' | 'desc' | null;

export interface ColumnDef<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => ReactNode;
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  loading: boolean;
  emptyMessage: string;
  onRowClick?: (row: T) => void;
  sortable?: boolean;
  ariaLabel?: string;
}

function compareValues(left: unknown, right: unknown) {
  if (typeof left === 'number' && typeof right === 'number') {
    return left - right;
  }

  return String(left ?? '').localeCompare(String(right ?? ''));
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  loading,
  emptyMessage,
  onRowClick,
  sortable = true,
  ariaLabel,
}: DataTableProps<T>) {
  const { t } = useTranslation();
  const [sortKey, setSortKey] = useState<keyof T | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

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

  if (!loading && data.length === 0) {
    return <EmptyState message={t(emptyMessage)} />;
  }

  return (
    <div className="data-table__scroll">
      <table className="data-table" role="table" aria-label={ariaLabel || t('app.table', { defaultValue: 'Table' })}>
        <thead className="data-table__head" role="rowgroup">
          <tr className="data-table__header-row" role="row">
            {columns.map((column) => {
              const isSortable = sortable && column.sortable !== false;
              const isActive = sortKey === column.key;
              const ariaSort = !isSortable || !isActive || !sortDirection
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
          {loading ? (
            Array.from({ length: 3 }, (_, index) => (
              <tr key={`loading-${index}`} className="data-table__row" role="row">
                <td className="data-table__cell" role="cell" colSpan={columns.length}>
                  <Skeleton variant="table-row" count={1} />
                </td>
              </tr>
            ))
          ) : (
            sortedData.map((row, rowIndex) => (
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
                    {column.render ? column.render(row[column.key], row) : String(row[column.key] ?? '-')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
