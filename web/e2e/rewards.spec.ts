import { expect, test } from '@playwright/test';
import { expectPageTitle, login } from './helpers';
import { apiListResponse, apiResponse, installMockSession } from './mockApi';

test.describe('Rewards flow', () => {
  test('student views rewards summary, badges, and leaderboard', async ({ page }) => {
    await installMockSession(page, 'student');

    await page.route(/\/api\/v1\/rewards\/me$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiResponse({
            id: 'reward-1',
            student_id: 'student-1',
            stars: 128,
            xp: 540,
            level: 6,
            streak_days: 9,
            longest_streak: 15,
            badges: ['EXPLORER', 'STREAK_STARTER'],
            last_activity_at: '2026-04-15T09:00:00.000Z',
            level_progress: 72,
          }),
        ),
      });
    });

    await page.route(/\/api\/v1\/rewards\/badges(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiListResponse([
            {
              id: 'badge-1',
              code: 'EXPLORER',
              title_fr: 'Explorateur',
              title_ar: 'مستكشف',
              title_en: 'Explorer',
              description_fr: 'Termine trois activites de lecture.',
              description_ar: 'اكمل ثلاث انشطة قراءة.',
              description_en: 'Complete three reading activities.',
              icon: '🧭',
              criteria_type: 'event_count',
              criteria_value: 3,
              display_order: 1,
              is_active: true,
            },
            {
              id: 'badge-2',
              code: 'STREAK_STARTER',
              title_fr: 'Serie lancee',
              title_ar: 'بداية السلسلة',
              title_en: 'Streak Starter',
              description_fr: 'Travaille trois jours de suite.',
              description_ar: 'اعمل ثلاثة ايام متتالية.',
              description_en: 'Work three days in a row.',
              icon: '🔥',
              criteria_type: 'streak_days',
              criteria_value: 3,
              display_order: 2,
              is_active: true,
            },
          ]),
        ),
      });
    });

    await page.route(/\/api\/v1\/rewards\/student\/student-1\/history(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiListResponse([
            {
              id: 'event-1',
              event_type: 'content_completed',
              stars_earned: 12,
              xp_earned: 30,
              source_type: 'content',
              source_id: 'content-1',
              created_at: '2026-04-15T09:00:00.000Z',
            },
            {
              id: 'event-2',
              event_type: 'game_completed',
              stars_earned: 8,
              xp_earned: 20,
              source_type: 'game',
              source_id: 'game-1',
              created_at: '2026-04-14T11:30:00.000Z',
            },
          ]),
        ),
      });
    });

    await page.route(/\/api\/v1\/enrollments(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiListResponse([
            {
              class_id: 'class-1',
              class_name: '6A',
            },
          ]),
        ),
      });
    });

    await page.route(/\/api\/v1\/rewards\/leaderboard\/class-1(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiListResponse([
            {
              student_id: 'student-2',
              student_name: 'Salma Idrissi',
              stars: 156,
              level: 7,
              rank: 1,
            },
            {
              student_id: 'student-1',
              student_name: 'Yassine Alaoui',
              stars: 128,
              level: 6,
              rank: 2,
            },
            {
              student_id: 'student-3',
              student_name: 'Nour Bennani',
              stars: 119,
              level: 6,
              rank: 3,
            },
          ]),
        ),
      });
    });

    await login(page, 'student');

    await page.goto('/rewards');
    await expectPageTitle(page, /recompenses|rewards/i);

    await expect(
      page
        .locator('.card')
        .filter({ hasText: /Etoiles|Stars/i })
        .first(),
    ).toContainText('128');
    await expect(
      page
        .locator('.card')
        .filter({ hasText: /Niveau|Level/i })
        .first(),
    ).toContainText('6');
    await expect(
      page
        .locator('.card')
        .filter({ hasText: /Serie actuelle|Current streak/i })
        .first(),
    ).toContainText('9');

    await expect(page.getByText(/Explorateur|Explorer/i).first()).toBeVisible();
    await expect(page.getByText(/Serie lancee|Streak Starter/i).first()).toBeVisible();
    await expect(page.getByText(/Historique des recompenses|Reward history/i)).toBeVisible();

    await page.locator('a[href="/classes/class-1/leaderboard"]').click();
    await expect(page).toHaveURL(/\/classes\/class-1\/leaderboard/);
    await expectPageTitle(page, /classement|leaderboard/i);

    await expect(page.getByText(/Top 3/i)).toBeVisible();
    await expect(page.getByRole('row', { name: /Yassine Alaoui.*128.*6/i })).toBeVisible();
    await expect(
      page.getByRole('row', { name: /Yassine Alaoui.*Vous|Yassine Alaoui.*You/i }),
    ).toBeVisible();
  });
});
