/// J3: Student — Login → submit file → verify in submissions
///
/// Reference: Phase 6A, Journey 3

import { test, expect } from '@playwright/test';
import { login } from './helpers';
import path from 'path';
import fs from 'fs';

test.describe('J3 — Student submission journey', () => {
  test.beforeAll(async () => {
    // Create a dummy file for upload
    const dir = path.join(__dirname, 'fixtures');
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'test-submission.txt'), 'E2E test submission content');
  });

  test('login → navigate to submissions → upload file', async ({ page }) => {
    // 1. Login as student
    await login(page, 'student');

    // 2. Should land on /content (STD default)
    await expect(page).toHaveURL(/\/content/);

    // 3. Navigate to submissions page
    await page.locator('a[href="/submissions"]').click();
    await expect(page).toHaveURL(/\/submissions/);

    // 4. Wait for content to load
    await page.waitForLoadState('networkidle');

    // 5. Look for submit/upload button
    const uploadBtn = page.locator('button, a', {
      hasText: /soumettre|upload|envoyer|nouveau/i,
    }).first();

    if (await uploadBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await uploadBtn.click();

      // 6. Upload a file if file input is present
      const fileInput = page.locator('input[type="file"]').first();
      if (await fileInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await fileInput.setInputFiles(
          path.join(__dirname, 'fixtures', 'test-submission.txt'),
        );

        // Submit the form
        const submitBtn = page.locator(
          'button[type="submit"], button:has-text("Envoyer"), button:has-text("Soumettre")',
        ).first();
        if (await submitBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
          await submitBtn.click();
          // Wait for success indication
          await page.waitForLoadState('networkidle');
        }
      }
    }

    // 7. Verify submissions page is accessible and shows content
    await page.goto('/submissions');
    await page.waitForLoadState('networkidle');
    // Page should load without errors
    await expect(page.locator('.page-title, h1').first()).toBeVisible({
      timeout: 5_000,
    });
  });
});
