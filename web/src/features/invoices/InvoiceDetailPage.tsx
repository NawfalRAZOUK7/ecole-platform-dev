import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, FileUpload, LoadingState } from '@/shared/ui';
import { formatDate } from '@/shared/i18n';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { InvoiceLineItem, PaymentRecord } from './invoices.service';
import { invoicesService } from './invoices.service';
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

async function pollUntilReady(jobId: string): Promise<string> {
  for (let attempt = 0; attempt < 30; attempt++) {
    const resp = await invoicesService.getReportJobStatus(jobId);
    const job = resp.data;
    if (job.status === 'ready' && job.download_url) return job.download_url;
    if (job.status === 'failed') throw new Error(job.error_message ?? 'Report generation failed');
    await new Promise<void>((r) => setTimeout(r, 2000));
  }
  throw new Error('Timed out waiting for PDF');
}

function triggerDownload(url: string, filename: string) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

export function InvoiceDetailPage() {
  const { t, i18n } = useTranslation();
  const { id = '' } = useParams();
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('card');
  const [selectedPaymentId, setSelectedPaymentId] = useState('');
  const [proofFile, setProofFile] = useState<File | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // PDF / receipt download state
  const [pdfLanguage, setPdfLanguage] = useState<'fr' | 'ar'>('fr');
  const [pdfDownloading, setPdfDownloading] = useState(false);
  const [receiptDownloading, setReceiptDownloading] = useState(false);
  const [selectedReceiptPaymentId, setSelectedReceiptPaymentId] = useState('');
  const [downloadError, setDownloadError] = useState<string | null>(null);

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
  const balanceDue =
    typeof invoice?.balance_due === 'number' ? invoice.balance_due : total - paidAmount;

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
    [i18n.language, t],
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

  async function handleDownloadPdf() {
    setDownloadError(null);
    setPdfDownloading(true);
    try {
      const jobResp = await invoicesService.generateInvoicePdf(id, pdfLanguage);
      const job = jobResp.data;
      const downloadUrl =
        job.status === 'ready' && job.download_url
          ? job.download_url
          : await pollUntilReady(job.id);
      triggerDownload(downloadUrl, `invoice-${id}.pdf`);
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : t('app.error'));
    } finally {
      setPdfDownloading(false);
    }
  }

  async function handleDownloadReceipt() {
    if (!selectedReceiptPaymentId) return;
    setDownloadError(null);
    setReceiptDownloading(true);
    try {
      const jobResp = await invoicesService.generatePaymentReceipt(
        selectedReceiptPaymentId,
        pdfLanguage,
      );
      const job = jobResp.data;
      const downloadUrl =
        job.status === 'ready' && job.download_url
          ? job.download_url
          : await pollUntilReady(job.id);
      triggerDownload(downloadUrl, `receipt-${selectedReceiptPaymentId}.pdf`);
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : t('app.error'));
    } finally {
      setReceiptDownloading(false);
    }
  }

  if (invoiceDetailQuery.isLoading || paymentsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page invoice-detail-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">
            {invoice?.invoice_number ?? invoice?.label ?? t('invoices.detailTitle')}
          </h1>
          <p className="page-subtitle">
            {formatDate(invoice?.issued_date ?? '', i18n.language)} ·{' '}
            {formatDate(invoice?.due_date ?? '', i18n.language)}
          </p>
        </div>
        <div className="invoice-detail-page__totals">
          <strong>{madFormatter.format(total)}</strong>
          <span>
            {t('invoices.balanceDue')}: {madFormatter.format(balanceDue)}
          </span>
        </div>
        <div className="filters-bar">
          <select
            className="filter-select"
            aria-label={t('invoices.pdfLanguage', { defaultValue: 'PDF Language' })}
            value={pdfLanguage}
            onChange={(e) => setPdfLanguage(e.target.value as 'fr' | 'ar')}
          >
            <option value="fr">Français</option>
            <option value="ar">العربية</option>
          </select>
          <button
            type="button"
            className="btn btn-secondary"
            aria-label={t('invoices.downloadPdf', { defaultValue: 'Download PDF' })}
            disabled={pdfDownloading}
            onClick={() => void handleDownloadPdf()}
          >
            {pdfDownloading
              ? t('app.loading')
              : t('invoices.downloadPdf', { defaultValue: 'Download PDF' })}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={toBannerError(
          invoiceDetailQuery.error ??
            paymentsQuery.error ??
            createPaymentMutation.error ??
            uploadProofMutation.error,
          t('app.error'),
        )}
      />

      {downloadError && (
        <div className="attendance-banner attendance-banner--error">{downloadError}</div>
      )}

      {successMessage && (
        <div className="attendance-banner attendance-banner--success">{successMessage}</div>
      )}

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
              aria-label={t('invoices.amount')}
              min="0"
              step="0.01"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              placeholder={t('invoices.amount')}
            />
            <select
              className="filter-select"
              aria-label={t('invoices.method')}
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
              aria-label={t('invoices.pay')}
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
              aria-label={t('invoices.selectPayment')}
              value={selectedPaymentId}
              onChange={(event) => setSelectedPaymentId(event.target.value)}
            >
              <option value="">{t('invoices.selectPayment')}</option>
              {payments.map((payment) => (
                <option key={payment.id} value={payment.id}>
                  {formatDate(payment.created_at ?? payment.finalized_at ?? '', i18n.language)} ·{' '}
                  {madFormatter.format(payment.amount)}
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
            aria-label={t('invoices.uploadProof')}
            disabled={uploadProofMutation.isPending || !selectedPaymentId || !proofFile}
            onClick={() => void handleUploadProof()}
          >
            {uploadProofMutation.isPending ? t('app.loading') : t('invoices.uploadProof')}
          </button>
        </section>

        <section className="card">
          <h2 className="attendance-page__section-title">
            {t('invoices.downloadReceipt', { defaultValue: 'Download Receipt' })}
          </h2>
          <div className="filters-bar">
            <select
              className="filter-select"
              aria-label={t('invoices.selectPayment')}
              value={selectedReceiptPaymentId}
              onChange={(event) => setSelectedReceiptPaymentId(event.target.value)}
            >
              <option value="">{t('invoices.selectPayment')}</option>
              {payments.map((payment) => (
                <option key={payment.id} value={payment.id}>
                  {formatDate(payment.created_at ?? payment.finalized_at ?? '', i18n.language)} ·{' '}
                  {madFormatter.format(payment.amount)}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="btn btn-secondary"
              aria-label={t('invoices.downloadReceipt', { defaultValue: 'Download Receipt' })}
              disabled={receiptDownloading || !selectedReceiptPaymentId}
              onClick={() => void handleDownloadReceipt()}
            >
              {receiptDownloading
                ? t('app.loading')
                : t('invoices.downloadReceipt', { defaultValue: 'Download Receipt' })}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
