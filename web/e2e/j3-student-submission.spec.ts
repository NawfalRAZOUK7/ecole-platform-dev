/// J3: Student — Login → submit file → verify in submissions
///
/// Reference: Phase 6A, Journey 3

import { test, expect } from '@playwright/test';
import { login } from './helpers';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { apiListResponse, apiResponse, installMockSession } from './mockApi';

let submissionFixtureDir = '';
let submissionFixturePath = '';

test.describe('J3 — Student submission journey', () => {
  test.beforeAll(async () => {
    // Create a dummy file for upload
    submissionFixtureDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ecole-e2e-submission-'));
    submissionFixturePath = path.join(submissionFixtureDir, 'test-submission.txt');
    fs.writeFileSync(submissionFixturePath, 'E2E test submission content');
  });

  test.afterAll(async () => {
    if (submissionFixtureDir) {
      fs.rmSync(submissionFixtureDir, { recursive: true, force: true });
    }
  });

  test('login → navigate to submissions → upload file', async ({ page }) => {
    let createdSubmissionId: string | null = null;
    let uploadedFileCount = 0;

    await installMockSession(page, 'student');

    await page.route(/\/api\/v1\/assignments(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiListResponse([
            {
              id: 'assignment-1',
              title: 'Devoir de mathematiques',
              course_id: 'course-1',
              due_at: '2026-04-18T10:00:00.000Z',
              total_points: 20,
              exercise_type: 'STANDARD',
            },
          ]),
        ),
      });
    });

    await page.route(/\/api\/v1\/submissions$/, async (route) => {
      createdSubmissionId = 'submission-1';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse({ id: createdSubmissionId })),
      });
    });

    await page.route(/\/api\/v1\/submissions\/[^/]+\/files$/, async (route) => {
      uploadedFileCount += 1;
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse({ success: true })),
      });
    });

    await page.route(/\/api\/v1\/submissions\/[^/]+\/submit$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(null)),
      });
    });

    // 1. Login as student
    await login(page, 'student');

    // 2. Should land on /content (STD default)
    await expect(page).toHaveURL(/\/content/);

    // 3. Navigate to submissions page
    await page.locator('a[href="/submissions"]').click();
    await expect(page).toHaveURL(/\/submissions/);

    // 4. Complete the submission flow with mocked APIs
    await page.waitForLoadState('networkidle');
    await page.locator('select.filter-select').selectOption('assignment-1');
    await page.locator('input[type="file"]').setInputFiles(submissionFixturePath);
    await page.locator('button[type="submit"]').click();

    // 5. Verify the student journey completed and the upload happened
    await expect.poll(() => createdSubmissionId, { timeout: 5_000 }).toBe('submission-1');
    await expect.poll(() => uploadedFileCount, { timeout: 5_000 }).toBe(1);
    await expect(page.locator('.page-title, h1').first()).toBeVisible({
      timeout: 5_000,
    });
  });
});
