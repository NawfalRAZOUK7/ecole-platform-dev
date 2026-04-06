import { expect, test } from '@playwright/test';
import { login } from './helpers';
import { installMockSession } from './mockApi';

test.describe('Dark mode', () => {
  test('toggle changes theme variables and persists after reload', async ({ page }) => {
    await installMockSession(page, 'parent');

    await login(page, 'parent');
    await page.goto('/feed');
    await expect(page.locator('html')).toHaveAttribute('data-theme', /light|dark/);

    const initialTheme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    );
    const initialSurface = await page.evaluate(() =>
      getComputedStyle(document.documentElement)
        .getPropertyValue('--color-surface')
        .trim()
    );

    await page.locator('.theme-toggle').click();

    const toggledTheme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    );
    const toggledSurface = await page.evaluate(() =>
      getComputedStyle(document.documentElement)
        .getPropertyValue('--color-surface')
        .trim()
    );

    expect(toggledTheme).not.toBe(initialTheme);
    expect(toggledSurface).not.toBe(initialSurface);

    await page.context().addCookies([
      {
        name: 'csrf_token',
        value: 'mock-csrf',
        url: 'http://localhost:5173',
      },
    ]);

    await page.reload();
    await page.waitForURL(/\/feed/);
    await expect(page.locator('html')).toHaveAttribute('data-theme', String(toggledTheme));

    const persistedTheme = await page.evaluate(() => ({
      attr: document.documentElement.getAttribute('data-theme'),
      stored: window.localStorage.getItem('ecole-theme'),
      surface: getComputedStyle(document.documentElement)
        .getPropertyValue('--color-surface')
        .trim(),
    }));

    expect(persistedTheme.attr).toBe(toggledTheme);
    expect(persistedTheme.stored).toBe(toggledTheme);
    expect(persistedTheme.surface).toBe(toggledSurface);
  });
});
