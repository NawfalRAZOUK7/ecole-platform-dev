import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, FileUpload, LoadingState } from '@/shared/ui';
import { formatDate } from '@/shared/i18n';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { InvoiceLineItem, PaymentRecord } from './invoices.service';
import {
  useCreatePayment,
  useInvoiceDetail,
  useInvoicePayments,
  useUploadProof,
} from './useInvoices';

type PaymentTableRow = PaymentRecord & Record<string, unknown>;

const madFormatter = new Intl.NumberFormat('fr-MA', {
  style: 'currency',
  currency: 'MAD',
});

function getBadgeVariant(status: string) {
  if (status === 'paid') return 'success';
  if (status === 'sent' || status === 'created') return 'info';
  if (status === 'overdue' || status === 'failed') return 'error';
  return 'neutral';
}

function getInvoiceTotal(items: InvoiceLineItem[]) {
  return items.reduce((sum, item) => sum + item.amount, 0);
}

export function InvoiceDetailPage() {
  const { t, i18n } = useTranslation();
  const { id = '' } = useParams();
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('card');
  const [selectedPaymentId, setSelectedPaymentId] = useState('');
  const [proofFile, setProofFile] = useState<File | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const invoiceDetailQuery = useInvoiceDetail(id);
  const paymentsQuery = useInvoicePayments(id);
  const createPaymentMutation = useCreatePayment();
  const uploadProofMutation = useUploadProof();

  const invoice = invoiceDetailQuery.data;
  const payments = paymentsQuery.data ?? [];
  const total = invoice ? getInvoiceTotal(invoice.items ?? []) : 0;
  const paidAmount = payments
    .filter((payment) => payment.status === 'paid')
    .reduce((sum, payment) => sum + payment.amount, 0);
  const balanceDue = typeof invoice?.balance_due === 'number' ? invoice.balance_due : total - paidAmount;

  const paymentColumns: ColumnDef<PaymentTableRow>[] = useMemo(
    () => [
      {
        key: 'created_at',
        header: 'invoices.paymentDate',
        render: (value, row) => formatDate(String(value ?? row.finalized_at ?? ''), i18n.language),
      },
      {
        key: 'amount',
        header: 'invoices.amount',
        render: (value) => madFormatter.format(Number(value)),
      },
      {
        key: 'method',
        header: 'invoices.method',
      },
      {
        key: 'status',
        header: 'invoices.status',
        render: (value) => (
          <span className={`badge badge--${getBadgeVariant(String(value))} badge--md`}>
            {t(`invoices.statusLabels.${String(value)}`, { defaultValue: String(value) })}
          </span>
        ),
      },
    ],
    [i18n.language, t]
  );

  async function handleCreatePayment() {
    if (!invoice || !amount) {
      return;
    }

    const response = await createPaymentMutation.mutateAsync({
      invoiceId: invoice.id,
      amount: Number(amount),
      method,
    });
    setSelectedPaymentId(response.data.id);
    setSuccessMessage(t('invoices.paymentCreated'));
  }

  async function handleUploadProof() {
    if (!selectedPaymentId || !proofFile) {
      return;
    }

    await uploadProofMutation.mutateAsync({
      paymentId: selectedPaymentId,
      file: proofFile,
    });
    setSuccessMessage(t('invoices.proofUploaded'));
  }

  if (invoiceDetailQuery.isLoading || paymentsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page invoice-detail-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{invoice?.invoice_number ?? invoice?.label ?? t('invoices.detailTitle')}</h1>
          <p className="page-subtitle">
            {formatDate(invoice?.issued_date ?? '', i18n.language)} · {formatDate(invoice?.due_date ?? '', i18n.language)}
          </p>
        </div>
        <div className="invoice-detail-page__totals">
          <strong>{madFormatter.format(total)}</strong>
          <span>{t('invoices.balanceDue')}: {madFormatter.format(balanceDue)}</span>
        </div>
      </div>

      <ErrorBanner
        error={toBannerError(
          invoiceDetailQuery.error ??
            paymentsQuery.error ??
            createPaymentMutation.error ??
            uploadProofMutation.error,
          t('app.error')
        )}
      />

      {successMessage && <div className="attendance-banner attendance-banner--success">{successMessage}</div>}

      <div className="invoice-detail-page__grid">
        <section className="card">
          <h2 className="attendance-page__section-title">{t('invoices.lineItems')}</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('invoices.description')}</th>
                <th>{t('invoices.quantity')}</th>
                <th>{t('invoices.unitPrice')}</th>
                <th>{t('invoices.total')}</th>
              </tr>
            </thead>
            <tbody>
              {(invoice?.items ?? []).map((item) => (
                <tr key={item.id}>
                  <td>{item.description}</td>
                  <td>{item.quantity}</td>
                  <td>{madFormatter.format(item.unit_price)}</td>
                  <td>{madFormatter.format(item.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card">
          <h2 className="attendance-page__section-title">{t('invoices.paymentHistory')}</h2>
          <DataTable
            columns={paymentColumns}
            data={payments as PaymentTableRow[]}
            loading={paymentsQuery.isLoading}
            emptyMessage="invoices.noPayments"
            ariaLabel={t('invoices.paymentHistory')}
          />
        </section>

        <section className="card invoice-detail-page__payment-form">
          <h2 className="attendance-page__section-title">{t('invoices.createPayment')}</h2>
          <div className="filters-bar">
            <input
              type="number"
              className="filter-input"
              min="0"
              step="0.01"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              placeholder={t('invoices.amount')}
            />
            <select
              className="filter-select"
              value={method}
              onChange={(event) => setMethod(event.target.value)}
            >
              <option value="card">{t('invoices.methods.card')}</option>
              <option value="bank_transfer">{t('invoices.methods.bank_transfer')}</option>
              <option value="cash">{t('invoices.methods.cash')}</option>
            </select>
            <button
              type="button"
              className="btn btn-primary"
              disabled={createPaymentMutation.isPending}
              onClick={() => void handleCreatePayment()}
            >
              {createPaymentMutation.isPending ? t('app.loading') : t('invoices.pay')}
            </button>
          </div>
        </section>

        <section className="card invoice-detail-page__proof">
          <h2 className="attendance-page__section-title">{t('invoices.uploadProof')}</h2>
          <div className="filters-bar">
            <select
              className="filter-select"
              value={selectedPaymentId}
              onChange={(event) => setSelectedPaymentId(event.target.value)}
            >
              <option value="">{t('invoices.selectPayment')}</option>
              {payments.map((payment) => (
                <option key={payment.id} value={payment.id}>
                  {formatDate(payment.created_at ?? payment.finalized_at ?? '', i18n.language)} · {madFormatter.format(payment.amount)}
                </option>
              ))}
            </select>
          </div>
          <FileUpload
            maxFiles={1}
            maxSizeMb={5}
            accept=".pdf,.jpg,.jpeg,.png"
            onFilesSelected={(files) => setProofFile(files[0] ?? null)}
          />
          <button
            type="button"
            className="btn btn-secondary"
            disabled={uploadProofMutation.isPending || !selectedPaymentId || !proofFile}
            onClick={() => void handleUploadProof()}
          >
            {uploadProofMutation.isPending ? t('app.loading') : t('invoices.uploadProof')}
          </button>
        </section>
      </div>
    </div>
  );
}
