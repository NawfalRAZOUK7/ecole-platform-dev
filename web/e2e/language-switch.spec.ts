import { expect, test } from '@playwright/test';

test.describe('Language switcher', () => {
  test('switches FR to AR with RTL and back to FR', async ({ page }) => {
    await page.goto('/login');

    const buttons = page.locator('.language-switcher__button');
    await buttons.nth(0).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'fr');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');

    await buttons.nth(1).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(buttons.nth(1)).toHaveAttribute('aria-pressed', 'true');

    await buttons.nth(0).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'fr');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
    await expect(buttons.nth(0)).toHaveAttribute('aria-pressed', 'true');
  });
});
