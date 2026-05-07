/// J1: Parent — Login → feed → notification → logout
///
/// Reference: Phase 6A, Journey 1

import { test, expect } from '@playwright/test';
import { login, logout, expectPageTitle } from './helpers';
import { installMockSession } from './mockApi';

test.describe('J1 — Parent journey', () => {
  test('login → feed → notifications → logout', async ({ page }) => {
    await installMockSession(page, 'parent');

    // 1. Login as parent
    await login(page, 'parent');

    // 2. Should land on /feed (PAR default)
    await expect(page).toHaveURL(/\/feed/);
    await expectPageTitle(page, /fil|news feed/i);

    // 3. Navigate to notifications
    await page.locator('a[href="/notifications"]').click();
    await expect(page).toHaveURL(/\/notifications/);
    await expectPageTitle(page, /notification/i);

    // 4. Logout
    await logout(page);
    await expect(page).toHaveURL(/\/login/);
  });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/feed');
    await expect(page).toHaveURL(/\/login/);
  });
});
