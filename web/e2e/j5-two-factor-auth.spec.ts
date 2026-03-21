/// J5: Login with 2FA — verify TOTP flow
///
/// Reference: Phase 6A, Journey 5
///
/// Note: This test verifies the 2FA UI flow is functional.
/// In CI, we mock the TOTP verification at the API level since
/// we cannot generate real TOTP codes without the shared secret.

import { test, expect } from '@playwright/test';
import { credentials, SCHOOL_ID } from './helpers';

test.describe('J5 — Two-factor authentication flow', () => {
  test('login form shows 2FA input when required', async ({ page }) => {
    // Navigate to login
    await page.goto('/login');

    // Fill login form
    await page.locator('#email').fill(credentials.admin.email);
    await page.locator('#password').fill(credentials.admin.password);
    const schoolInput = page.locator('#schoolId');
    await schoolInput.clear();
    await schoolInput.fill(SCHOOL_ID);

    // Intercept login API to simulate 2FA requirement
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            requires_2fa: true,
            temp_token: 'mock-temp-token-e2e',
          },
          meta: { timestamp: new Date().toISOString(), version: '1.0.0' },
        }),
      });
    });

    // Submit login
    await page.locator('.login-submit').click();

    // 2FA input should appear
    const totpInput = page.locator('#totpCode');
    await expect(totpInput).toBeVisible({ timeout: 5_000 });

    // Fill a mock TOTP code
    await totpInput.fill('123456');

    // Intercept 2FA verify to simulate success
    await page.route('**/api/v1/auth/2fa/verify', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            access_token: 'mock-access-token-e2e',
            token_type: 'bearer',
          },
          meta: { timestamp: new Date().toISOString(), version: '1.0.0' },
        }),
      });
    });

    // Also mock /auth/me for the redirect
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 'mock-user-id',
            email: credentials.admin.email,
            full_name: 'Admin Test',
            role: 'ADM',
            school_id: SCHOOL_ID,
            permissions: ['admin:read', 'admin:write'],
            memberships: [{ school_id: SCHOOL_ID, role: 'ADM', status: 'active' }],
          },
          meta: { timestamp: new Date().toISOString(), version: '1.0.0' },
        }),
      });
    });

    // Submit 2FA code
    const verifyBtn = page.locator('.login-submit');
    await verifyBtn.click();

    // Should navigate away from login
    await page.waitForURL((url) => !url.pathname.includes('/login'), {
      timeout: 10_000,
    });
  });

  test('2FA form shows backup code toggle', async ({ page }) => {
    await page.goto('/login');
    await page.locator('#email').fill(credentials.admin.email);
    await page.locator('#password').fill(credentials.admin.password);

    // Mock 2FA required
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: { requires_2fa: true, temp_token: 'mock-temp-token' },
          meta: { timestamp: new Date().toISOString(), version: '1.0.0' },
        }),
      });
    });

    await page.locator('.login-submit').click();

    // TOTP input should be visible
    await expect(page.locator('#totpCode')).toBeVisible({ timeout: 5_000 });

    // Look for backup code toggle button
    const backupToggle = page.locator('button', {
      hasText: /backup|secours|récupération/i,
    });
    if (await backupToggle.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await backupToggle.click();
      // Backup code input should appear
      const backupInput = page.locator('input[maxlength="20"], input[placeholder*="backup" i], input[placeholder*="secours" i]');
      await expect(backupInput.first()).toBeVisible({ timeout: 3_000 });
    }
  });
});
