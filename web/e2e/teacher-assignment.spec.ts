/// J2: Teacher — Login → create assignment → verify in list
///
/// Reference: Phase 6A, Journey 2

import { test, expect } from '@playwright/test';
import { login } from './helpers';
import { apiListResponse, apiResponse, installMockSession } from './mockApi';

test.describe('J2 — Teacher assignment journey', () => {
  test('login → navigate to assignments → create → verify', async ({ page }) => {
    let assignments = [
      {
        id: 'assignment-seed',
        course_id: 'course-1',
        title: 'Evaluation initiale',
        description: 'Controle de demarrage',
        due_at: '2026-04-15T10:00:00.000Z',
        total_points: 20,
      },
    ];

    const courses = [
      {
        id: 'course-1',
        class_id: 'class-1',
        title: 'Mathematiques 6A',
        description: 'Cours principal',
        status: 'active',
      },
    ];

    await installMockSession(page, 'teacher');

    await page.route(/\/api\/v1\/courses(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse(courses)),
      });
    });

    await page.route(/\/api\/v1\/assignments(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'POST') {
        const payload = route.request().postDataJSON() as {
          course_id: string;
          title: string;
          description?: string | null;
          due_at?: string | null;
          total_points?: number;
        };

        assignments = [
          {
            id: `assignment-${assignments.length + 1}`,
            course_id: payload.course_id,
            title: payload.title,
            description: payload.description ?? null,
            due_at: payload.due_at ?? null,
            total_points: payload.total_points ?? 0,
          },
          ...assignments,
        ];

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiResponse(null)),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse(assignments)),
      });
    });

    // 1. Login as teacher
    await login(page, 'teacher');

    // 2. Should land on /teacher (TCH default)
    await expect(page).toHaveURL(/\/teacher/);

    // 3. Navigate to assignments page
    await page.locator('a[href="/teacher/assignments"]').click();
    await expect(page).toHaveURL(/\/teacher\/assignments/);

    // 4. Wait for page to load
    await page.waitForLoadState('networkidle');

    // 5. Open the create form
    const addBtn = page.locator('button', { hasText: /new|ajouter|créer|nouveau/i });
    await addBtn.click();

    // 6. Fill assignment form
    const uniqueTitle = `Test Assignment E2E ${Date.now()}`;
    await page.locator('form select.filter-select').selectOption('course-1');
    await page.locator('form input.filter-input').first().fill(uniqueTitle);
    await page.locator('form button[type="submit"]').click();

    // 7. Verify the new assignment appears in the list
    await expect(page.locator(`text=${uniqueTitle}`)).toBeVisible({
      timeout: 5_000,
    });
  });
});
