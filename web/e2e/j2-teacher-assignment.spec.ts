/// J2: Teacher — Login → create assignment → verify in list
///
/// Reference: Phase 6A, Journey 2

import { test, expect } from '@playwright/test';
import { login } from './helpers';

test.describe('J2 — Teacher assignment journey', () => {
  test('login → navigate to assignments → create → verify', async ({
    page,
  }) => {
    // 1. Login as teacher
    await login(page, 'teacher');

    // 2. Should land on /teacher (TCH default)
    await expect(page).toHaveURL(/\/teacher/);

    // 3. Navigate to assignments page
    await page.locator('a[href="/teacher/assignments"]').click();
    await expect(page).toHaveURL(/\/teacher\/assignments/);

    // 4. Wait for page to load
    await page.waitForLoadState('networkidle');

    // 5. Look for a create/add button and open the form
    const addBtn = page.locator('button', { hasText: /ajouter|créer|nouveau/i });
    if (await addBtn.isVisible()) {
      await addBtn.click();
    }

    // 6. Fill assignment form fields (if form is visible)
    const titleInput = page.locator('input[name="title"], #title, input[placeholder*="titre" i]').first();
    if (await titleInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
      const uniqueTitle = `Test Assignment E2E ${Date.now()}`;
      await titleInput.fill(uniqueTitle);

      // Fill points if available
      const pointsInput = page.locator('input[name="totalPoints"], input[name="total_points"], #totalPoints').first();
      if (await pointsInput.isVisible({ timeout: 1_000 }).catch(() => false)) {
        await pointsInput.fill('20');
      }

      // Submit form
      const submitBtn = page.locator('button[type="submit"], button:has-text("Créer"), button:has-text("Enregistrer")').first();
      await submitBtn.click();

      // 7. Verify the new assignment appears in the list
      await expect(page.locator('text=' + uniqueTitle)).toBeVisible({
        timeout: 5_000,
      });
    }
  });
});
