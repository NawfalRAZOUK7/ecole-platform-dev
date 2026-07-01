import { expect, test } from '@playwright/test';
import { login } from './helpers';
import { apiResponse, installMockSession } from './mockApi';

const SCREENSHOT_DIR = '../../ecole-platform-report-jury/assets/screenshots/web';

const studentRewards = {
  id: 'reward-yassine',
  student_id: 'student-1',
  stars: 25,
  xp: 350,
  level: 3,
  streak_days: 5,
  longest_streak: 7,
  badges: ['first_login', 'streak_7', 'xp_250'],
  last_activity_at: '2026-04-15T09:00:00.000Z',
  level_progress: 50,
};

async function waitForStudentHome(page: import('@playwright/test').Page, readyText: RegExp) {
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => document.fonts?.ready);
  await expect(page.locator('.brand-splash')).toBeHidden({ timeout: 5_000 });
  await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
  await expect(page.getByRole('heading', { name: readyText })).toBeVisible();
  for (const selector of ['.app-main', '.sidebar-nav', '.sidebar-footer']) {
    await expect(page.locator(selector)).not.toContainText(/[\u0600-\u06FF]/);
  }
}

test.describe('Report i18n screenshots', () => {
  test.use({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
  });

  test('captures student home in French and English', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ecole-theme', 'light');
      window.localStorage.setItem('i18nextLng', 'fr');
    });

    await installMockSession(page, 'student');

    await page.route(/\/api\/v1\/notifications\/unread-count$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse({ unread_count: 1 })),
      });
    });

    await page.route(/\/api\/v1\/rewards\/me(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(studentRewards)),
      });
    });

    await login(page, 'student');
    await page.goto('/student/home', { waitUntil: 'networkidle' });

    await expect(page.locator('html')).toHaveAttribute('lang', 'fr');
    await waitForStudentHome(page, /Bonjour, Yassine/i);
    await expect(page.getByText('Pret a apprendre ?')).toBeVisible();
    await expect(page.getByText('Commencer a apprendre')).toBeVisible();
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web_student_home_fr.png`,
      clip: { x: 0, y: 0, width: 1440, height: 900 },
    });

    await page.getByRole('button', { name: 'English' }).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await waitForStudentHome(page, /Hello, Yassine/i);
    await expect(page.getByText('Ready to learn?')).toBeVisible();
    await expect(page.getByText('Start Learning')).toBeVisible();
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/web_student_home_en.png`,
      clip: { x: 0, y: 0, width: 1440, height: 900 },
    });
  });
});
