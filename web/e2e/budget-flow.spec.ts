import { expect, test, type Page } from '@playwright/test';
import { SCHOOL_ID, expectPageTitle, login, logout } from './helpers';
import { apiListResponse, apiResponse, installMockSession } from './mockApi';

async function loginWithCredentials(page: Page, email: string, password: string) {
  await page.goto('/login');
  const emailInput = page.locator('#email');
  await expect(emailInput).toBeEnabled({ timeout: 10_000 });
  await emailInput.fill(email);
  await page.locator('#password').fill(password);
  await page.locator('#schoolId').fill(SCHOOL_ID);
  await page.locator('.login-submit').click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), {
    timeout: 10_000,
  });
}

test.describe('Budget flow', () => {
  test('admin creates a budget and director approves a request', async ({ page }) => {
    let budgets = [
      {
        id: 'budget-seed',
        name: 'Budget existant',
        total_amount: 12000,
        spent_amount: 3000,
        remaining_amount: 9000,
        status: 'active',
        start_date: '2026-01-01',
        end_date: '2026-06-30',
        created_at: '2026-03-01T08:00:00.000Z',
      },
    ];

    let requests = [
      {
        id: 'request-1',
        budget_id: 'budget-seed',
        requester_name: 'Equipe pedagogique',
        amount: 2500,
        category: 'Tablettes',
        justification: 'Renouvellement du parc numerique',
        status: 'pending',
      },
    ];

    await installMockSession(page, 'admin');

    await page.route(/\/api\/v1\/budgets(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'POST') {
        const payload = route.request().postDataJSON() as {
          name: string;
          total_amount: number;
          start_date: string;
          end_date: string;
        };

        const budget = {
          id: `budget-${budgets.length + 1}`,
          name: payload.name,
          total_amount: payload.total_amount,
          spent_amount: 0,
          remaining_amount: payload.total_amount,
          status: 'active',
          start_date: payload.start_date,
          end_date: payload.end_date,
          created_at: '2026-04-06T10:30:00.000Z',
        };

        budgets = [budget, ...budgets];
        requests = [
          {
            id: 'request-2',
            budget_id: budget.id,
            requester_name: 'Direction pedagogique',
            amount: 1800,
            category: 'Materiel',
            justification: 'Achat de kits scientifiques',
            status: 'pending',
          },
          ...requests,
        ];

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiResponse(budget)),
        });
        return;
      }

      const url = new URL(route.request().url());
      const statusFilter = url.searchParams.get('status');
      const filteredBudgets = statusFilter
        ? budgets.filter((budget) => budget.status === statusFilter)
        : budgets;

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse(filteredBudgets)),
      });
    });

    await page.route(/\/api\/v1\/budgets\/requests\/request-\d+\/approve$/, async (route) => {
      const requestId = route.request().url().split('/').at(-2) ?? '';
      requests = requests.map((request) =>
        request.id === requestId ? { ...request, status: 'approved' } : request,
      );

      const approvedRequest = requests.find((request) => request.id === requestId);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(approvedRequest ?? null)),
      });
    });

    await page.route(/\/api\/v1\/budgets\/budget-\d+$/, async (route) => {
      const budgetId = route.request().url().split('/').at(-1) ?? '';
      const budget = budgets.find((item) => item.id === budgetId) ?? budgets[0];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(budget)),
      });
    });

    await page.route(/\/api\/v1\/budgets\/budget-\d+\/allocations$/, async (route) => {
      const budgetId = route.request().url().split('/').at(-2) ?? '';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiResponse([
            {
              id: `allocation-${budgetId}`,
              label: 'Numerique',
              category: 'Innovation',
              amount: 5000,
              remaining: 3200,
            },
          ]),
        ),
      });
    });

    await page.route(
      /\/api\/v1\/budgets\/allocations\/allocation-budget-\d+\/requests(?:\?.*)?$/,
      async (route) => {
        const allocationId = route.request().url().split('/').at(-2) ?? '';
        const budgetId = allocationId.replace('allocation-', '');
        const statusFilter = new URL(route.request().url()).searchParams.get('status');
        const filteredRequests = requests.filter((request) => {
          return (
            request.budget_id === budgetId && (!statusFilter || request.status === statusFilter)
          );
        });

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiListResponse(filteredRequests)),
        });
      },
    );

    await page.route(
      /\/api\/v1\/budgets\/allocations\/allocation-budget-\d+\/transactions$/,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(
            apiListResponse([
              {
                id: 'transaction-1',
                date: '2026-04-01',
                amount: 600,
                type: 'purchase',
                description: 'Commande fournitures',
              },
            ]),
          ),
        });
      },
    );

    await login(page, 'admin');
    await page.goto('/budgets');
    await expectPageTitle(page, /Budgets/i);

    await page.locator('.page-header .btn.btn-primary').click();
    const form = page.locator('.budgets-page__form');
    await expect(form).toBeVisible();
    await form.locator('input[type="text"]').fill('Budget innovation STEM');
    await form.locator('input[type="number"]').fill('28000');
    await form.locator('input[type="date"]').nth(0).fill('2026-04-01');
    await form.locator('input[type="date"]').nth(1).fill('2026-06-30');
    await page.locator('.budgets-page__form .btn.btn-primary').click();

    await expect(page.locator('.data-table')).toContainText(/Budget innovation STEM/i);

    const createdBudgetId = budgets[0]?.id;
    await logout(page);

    await loginWithCredentials(page, 'director@ecole-benani.ma', 'director123');
    await page.goto(`/budgets/${createdBudgetId}`);
    await expectPageTitle(page, /Budget innovation STEM/i);

    await page.getByRole('tab', { name: /Demandes|Requests/i }).click();
    const approveButton = page.locator('.tabs__panel button.btn.btn-primary').first();
    await expect(approveButton).toBeVisible();
    await approveButton.click();
    await expect(page.locator('.confirm-dialog')).toBeVisible();
    await page.locator('.confirm-dialog .btn.btn-primary').click();
    await expect(page.locator('.confirm-dialog')).toBeHidden();
    await expect(page.locator('.tabs__panel button.btn.btn-primary')).toHaveCount(0);
  });
});
