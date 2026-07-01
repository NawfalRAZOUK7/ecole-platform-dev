/// Shared helpers for E2E tests.

import { type Page, expect } from '@playwright/test';

export const SCHOOL_ID = '00000000-0000-4000-8000-000000000001';

export const credentials = {
  admin: { email: 'admin@ecole-benani.ma', password: 'admin123' },
  teacher: { email: 'prof.math@ecole-benani.ma', password: 'teacher123' },
  parent: { email: 'parent.alaoui@gmail.com', password: 'parent123' },
  student: { email: 'yassine.alaoui@ecole-benani.ma', password: 'student123' },
  content_manager: { email: 'cms.manager@ecole-benani.ma', password: 'cms123' },
} as const;

/**
 * Log in as a given role via the login form.
 * Waits until the post-login redirect completes.
 */
export async function login(page: Page, role: keyof typeof credentials): Promise<void> {
  const cred = credentials[role];

  await page.goto('/login');
  const emailInput = page.locator('#email');
  await expect(emailInput).toBeEnabled({ timeout: 10_000 });
  await emailInput.fill(cred.email);
  await page.locator('#password').fill(cred.password);

  // School ID should have the default value; overwrite to be safe
  const schoolInput = page.locator('#schoolId');
  await schoolInput.clear();
  await schoolInput.fill(SCHOOL_ID);

  await page.locator('.login-submit').click();

  // Wait for navigation away from /login
  await page.waitForURL((url) => !url.pathname.includes('/login'), {
    timeout: 10_000,
  });
}

/**
 * Log out via the sidebar button.
 */
export async function logout(page: Page): Promise<void> {
  await page.locator('.logout-btn').click();
  await page.waitForURL('**/login', { timeout: 5_000 });
}

/**
 * Assert the page title (h1.page-title) contains the given text.
 */
export async function expectPageTitle(page: Page, text: string | RegExp): Promise<void> {
  await expect(page.locator('.page-title').first()).toContainText(text, {
    timeout: 5_000,
  });
}
