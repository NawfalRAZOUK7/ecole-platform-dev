import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { Badge, DataTable, ErrorBanner, LoadingState, Pagination, SearchInput } from '@/shared/ui';
import { formatDate } from '@/shared/i18n';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useInvoices } from './useInvoices';
import type { InvoiceSummary } from './invoices.service';

type InvoiceTableRow = InvoiceSummary & Record<string, unknown>;

const madFormatter = new Intl.NumberFormat('fr-MA', {
  style: 'currency',
  currency: 'MAD',
});

function getInvoiceAmount(invoice: InvoiceSummary) {
  if (typeof invoice.total_amount === 'number') {
    return invoice.total_amount;
  }
  if (typeof invoice.total_cents === 'number') {
    return invoice.total_cents / 100;
  }
  return 0;
}

function resolveStatus(invoice: InvoiceSummary) {
  if (invoice.status !== 'paid' && new Date(invoice.due_date) < new Date()) {
    return 'overdue';
  }
  return invoice.status;
}

function getBadgeVariant(status: string) {
  if (status === 'paid') return 'success';
  if (status === 'sent') return 'info';
  if (status === 'overdue' || status === 'failed') return 'error';
  return 'neutral';
}

export function InvoicesPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const invoicesQuery = useInvoices({
    status: statusFilter || undefined,
  });

  const items = useMemo(
    () => invoicesQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [invoicesQuery.data]
  );

  const filteredItems = useMemo(() => {
    return items.filter((invoice) => {
      const normalizedStatus = resolveStatus(invoice);
      const candidate = (invoice.student_name ?? invoice.student_id ?? '').toLowerCase();
      const issuedDate = invoice.issued_date.slice(0, 10);
      const withinFrom = !from || issuedDate >= from;
      const withinTo = !to || issuedDate <= to;
      const matchesSearch = !search || candidate.includes(search.toLowerCase());
      const matchesStatus = !statusFilter || normalizedStatus === statusFilter;
      return withinFrom && withinTo && matchesSearch && matchesStatus;
    });
  }, [from, items, search, statusFilter, to]);

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const pageItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredItems.slice(start, start + pageSize);
  }, [currentPage, filteredItems, pageSize]);

  const columns: ColumnDef<InvoiceTableRow>[] = useMemo(
    () => [
      {
        key: 'id',
        header: 'invoices.invoiceNumber',
        render: (_value, row) => row.invoice_number ?? row.label ?? row.id.slice(0, 8),
      },
      {
        key: 'student_name',
        header: 'invoices.student',
        render: (value, row) => String(value ?? row.student_id ?? '—'),
      },
      {
        key: 'total_amount',
        header: 'invoices.amount',
        render: (_value, row) => madFormatter.format(getInvoiceAmount(row)),
      },
      {
        key: 'status',
        header: 'invoices.status',
        render: (value, row) => {
          const status = resolveStatus(row);
          const labelKey =
            status === 'overdue' ? 'invoices.overdue' : `invoices.statusLabels.${String(value)}`;
          return <Badge variant={getBadgeVariant(status)}>{t(labelKey, { defaultValue: status })}</Badge>;
        },
      },
      {
        key: 'due_date',
        header: 'invoices.dueDate',
        render: (value) => formatDate(String(value), i18n.language),
      },
      {
        key: 'id',
        header: 'invoices.actions',
        sortable: false,
        render: (_value, row) => (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={(event) => {
              event.stopPropagation();
              navigate(`/invoices/${row.id}`);
            }}
          >
            {t('invoices.view')}
          </button>
        ),
      },
    ],
    [i18n.language, navigate, t]
  );

  if (invoicesQuery.isLoading && !invoicesQuery.data) {
    return <LoadingState />;
  }

  return (
    <div className="page invoices-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('invoices.title')}</h1>
          <p className="page-subtitle">{t('invoices.subtitle')}</p>
        </div>
      </div>

      <ErrorBanner error={toBannerError(invoicesQuery.error, t('app.error'))} />

      <div className="filters-bar">
        <SearchInput
          value={search}
          onChange={(value) => {
            setSearch(value);
            setCurrentPage(1);
          }}
          placeholder="invoices.searchPlaceholder"
        />
        <select
          className="filter-select"
          value={statusFilter}
          onChange={(event) => {
            setStatusFilter(event.target.value);
            setCurrentPage(1);
          }}
        >
          <option value="">{t('invoices.allStatuses')}</option>
          <option value="draft">{t('invoices.statusLabels.draft')}</option>
          <option value="sent">{t('invoices.statusLabels.sent')}</option>
          <option value="paid">{t('invoices.statusLabels.paid')}</option>
          <option value="overdue">{t('invoices.overdue')}</option>
        </select>
        <input
          type="date"
          className="filter-input"
          value={from}
          lang="fr-MA"
          onChange={(event) => {
            setFrom(event.target.value);
            setCurrentPage(1);
          }}
        />
        <input
          type="date"
          className="filter-input"
          value={to}
          lang="fr-MA"
          onChange={(event) => {
            setTo(event.target.value);
            setCurrentPage(1);
          }}
        />
      </div>

      <DataTable
        columns={columns}
        data={pageItems as InvoiceTableRow[]}
        loading={invoicesQuery.isLoading}
        emptyMessage="invoices.empty"
        ariaLabel={t('invoices.title')}
        onRowClick={(row) => navigate(`/invoices/${row.id}`)}
      />

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setCurrentPage(1);
        }}
      />
    </div>
  );
}
