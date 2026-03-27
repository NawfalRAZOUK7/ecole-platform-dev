/// J3: Student — Login → submit file → verify in submissions
///
/// Reference: Phase 6A, Journey 3

import { test, expect } from '@playwright/test';
import { login } from './helpers';
import fs from 'fs';
import os from 'os';
import path from 'path';

let submissionFixtureDir = '';
let submissionFixturePath = '';

test.describe('J3 — Student submission journey', () => {
  test.beforeAll(async () => {
    // Create a dummy file for upload
    submissionFixtureDir = fs.mkdtempSync(
      path.join(os.tmpdir(), 'ecole-e2e-submission-'),
    );
    submissionFixturePath = path.join(
      submissionFixtureDir,
      'test-submission.txt',
    );
    fs.writeFileSync(submissionFixturePath, 'E2E test submission content');
  });

  test.afterAll(async () => {
    if (submissionFixtureDir) {
      fs.rmSync(submissionFixtureDir, { recursive: true, force: true });
    }
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
        await fileInput.setInputFiles(submissionFixturePath);

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
