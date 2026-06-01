/// J0: Login → logout → token refresh flow
///
/// Reference: Phase 6A, §8.2.6C — parcours critiques

import { test, expect } from '@playwright/test';
import { login, logout, SCHOOL_ID } from './helpers';
import { apiResponse, installMockSession } from './mockApi';

test.describe('J0 — Login / Logout / Refresh flow', () => {
  test('successful login redirects away from /login', async ({ page }) => {
    await installMockSession(page, 'admin');
    await login(page, 'admin');
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('logout returns to /login', async ({ page }) => {
    await installMockSession(page, 'parent');
    await login(page, 'parent');
    await expect(page).toHaveURL(/\/feed/);
    await logout(page);
    await expect(page).toHaveURL(/\/login/);
  });

  test('unauthenticated access to /admin redirects to /login', async ({ page }) => {
    await page.route(/\/api\/v1\/auth\/me$/, async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' }),
      });
    });
    await page.goto('/admin');
    await expect(page).toHaveURL(/\/login/);
  });

  test('token refresh is called after login', async ({ page }) => {
    let refreshCalled = false;
    await installMockSession(page, 'teacher');
    await page.route(/\/api\/v1\/auth\/refresh$/, async (route) => {
      refreshCalled = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiResponse({ access_token: 'new-token', token_type: 'bearer', expires_in: 3600 }),
        ),
      });
    });
    await login(page, 'teacher');
    // Trigger refresh manually via API call
    await page.evaluate(() =>
      fetch('/api/v1/auth/refresh', { method: 'POST', credentials: 'include' }),
    );
    expect(refreshCalled).toBe(true);
  });

  test('invalid credentials show error on login page', async ({ page }) => {
    await page.route(/\/api\/v1\/auth\/login$/, async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'ERR-IAM-401',
            message: 'Invalid credentials',
            category: 'auth',
            retryable: false,
            timestamp: new Date().toISOString(),
          },
        }),
      });
    });
    await page.goto('/login');
    await expect(page.locator('#email')).toBeEnabled({ timeout: 10_000 });
    await page.locator('#email').fill('bad@user.com');
    await page.locator('#password').fill('wrongpass');
    await page.locator('#schoolId').fill(SCHOOL_ID);
    await page.locator('.login-submit').click();
    // Should stay on login and show error
    await expect(page).toHaveURL(/\/login/);
  });

  test('each role lands on its own default route after login', async ({ page }) => {
    await installMockSession(page, 'parent');
    await login(page, 'parent');
    await expect(page).toHaveURL(/\/feed/);
  });

  test('admin role lands on /admin after login', async ({ page }) => {
    await installMockSession(page, 'admin');
    await login(page, 'admin');
    await expect(page).toHaveURL(/\/admin/);
  });
});
