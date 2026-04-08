import { expect, test } from '@playwright/test';
import { expectPageTitle, login } from './helpers';
import { apiResponse, installMockSession } from './mockApi';

test.describe('Invoice payment flow', () => {
  test('parent views an invoice and uploads payment proof', async ({ page }) => {
    const invoiceId = 'invoice-1';
    const invoice = {
      id: invoiceId,
      invoice_number: 'INV-2026-001',
      label: 'Facture T1',
      status: 'sent',
      issued_date: '2026-04-01',
      due_date: '2026-04-10',
      total_amount: 4500,
      balance_due: 4500,
      items: [
        {
          id: 'line-1',
          description: 'Frais trimestriels',
          quantity: 1,
          unit_price: 4500,
          amount: 4500,
        },
      ],
    };

    let payments = [
      {
        id: 'payment-seed',
        invoice_id: invoiceId,
        amount: 1500,
        method: 'card',
        status: 'paid',
        created_at: '2026-04-02T08:00:00.000Z',
        finalized_at: '2026-04-02T08:15:00.000Z',
        proof_url: null,
      },
    ];

    await installMockSession(page, 'parent');

    await page.route(/\/api\/v1\/invoices\/invoice-1$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(invoice)),
      });
    });

    await page.route(/\/api\/v1\/payments\/invoice-1$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(payments)),
      });
    });

    await page.route(/\/api\/v1\/payments\/initiate$/, async (route) => {
      const payload = route.request().postDataJSON() as {
        invoice_id: string;
        amount: number;
        method: string;
      };
      const payment = {
        id: `payment-${payments.length + 1}`,
        invoice_id: payload.invoice_id,
        amount: payload.amount,
        method: payload.method,
        status: 'pending',
        created_at: '2026-04-06T09:00:00.000Z',
        finalized_at: null,
        proof_url: null,
      };

      payments = [...payments, payment];

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(payment)),
      });
    });

    await page.route(/\/api\/v1\/payments\/payment-\d+\/proof$/, async (route) => {
      const paymentId = route.request().url().split('/').at(-2) ?? '';
      payments = payments.map((payment) =>
        payment.id === paymentId
          ? { ...payment, proof_url: '/uploads/payment-proof.pdf' }
          : payment,
      );

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse({ success: true })),
      });
    });

    await login(page, 'parent');
    await page.goto(`/invoices/${invoiceId}`);
    await expectPageTitle(page, /INV-2026-001/i);
    await expect(page.locator('.invoice-detail-page__grid')).toContainText(/Frais trimestriels/i);

    await page.locator('.invoice-detail-page__payment-form input[type="number"]').fill('3000');
    await page.locator('.invoice-detail-page__payment-form .btn.btn-primary').click();

    await expect(page.locator('.attendance-banner--success')).toContainText(
      /Paiement cree|Payment created/i,
    );

    await page.locator('.invoice-detail-page__proof select').selectOption('payment-2');
    await page.locator('.invoice-detail-page__proof input[type="file"]').setInputFiles({
      name: 'payment-proof.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('mock proof bytes'),
    });

    await expect(page.locator('.invoice-detail-page__proof')).toContainText(/payment-proof\.pdf/i);
    await page.locator('.invoice-detail-page__proof .btn.btn-secondary').click();

    await expect(page.locator('.attendance-banner--success')).toContainText(
      /Justificatif televerse|Proof uploaded/i,
    );
  });
});
