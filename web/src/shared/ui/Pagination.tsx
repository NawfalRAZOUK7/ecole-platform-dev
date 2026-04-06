import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  pageSizeOptions?: number[];
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
}

function buildPages(currentPage: number, totalPages: number) {
  if (totalPages <= 5) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set<number>([1, totalPages, currentPage, currentPage - 1, currentPage + 1]);
  const sorted = Array.from(pages).filter((page) => page >= 1 && page <= totalPages).sort((a, b) => a - b);
  const result: Array<number | string> = [];

  for (let index = 0; index < sorted.length; index += 1) {
    const page = sorted[index];
    const previous = sorted[index - 1];

    if (previous && page - previous > 1) {
      result.push('…');
    }

    result.push(page);
  }

  return result;
}

export function Pagination({
  currentPage,
  totalPages,
  pageSize,
  pageSizeOptions = [10, 20, 50],
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const { t } = useTranslation();
  const pages = useMemo(() => buildPages(currentPage, totalPages), [currentPage, totalPages]);

  if (totalPages <= 1 && !onPageSizeChange) {
    return null;
  }

  return (
    <div className="pagination" aria-label={t('pagination.navigation', { defaultValue: 'Pagination navigation' })}>
      <button
        type="button"
        className="pagination__btn"
        disabled={currentPage === 1}
        onClick={() => onPageChange(currentPage - 1)}
      >
        {t('pagination.previous', { defaultValue: 'Previous' })}
      </button>

      <div className="pagination__pages">
        {pages.map((page, index) => (
          typeof page === 'string' ? (
            <span key={`${page}-${index}`} className="pagination__ellipsis" aria-hidden="true">
              {page}
            </span>
          ) : (
            <button
              key={page}
              type="button"
              className={`pagination__btn ${page === currentPage ? 'pagination__btn--active' : ''}`}
              onClick={() => onPageChange(page)}
              aria-current={page === currentPage ? 'page' : undefined}
            >
              {page}
            </button>
          )
        ))}
      </div>

      <button
        type="button"
        className="pagination__btn"
        disabled={currentPage === totalPages}
        onClick={() => onPageChange(currentPage + 1)}
      >
        {t('pagination.next', { defaultValue: 'Next' })}
      </button>

      {onPageSizeChange && (
        <label className="pagination__size">
          <span>{t('pagination.pageSize', { defaultValue: 'Page size' })}</span>
          <select
            className="pagination__size-select"
            value={pageSize}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
            {pageSizeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      )}
    </div>
  );
}
