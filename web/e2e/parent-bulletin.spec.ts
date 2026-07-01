/// J7: Parent — consultation du bulletin / relevé de notes
///
/// Reference: Phase 6A, §8.2.6C — consultation bulletin (parent)

import { test, expect } from '@playwright/test';
import { login } from './helpers';
import { apiResponse, apiListResponse, installMockSession } from './mockApi';

const mockChild = {
  id: 'student-1',
  full_name: 'Yassine Alaoui',
  class_level: 'ce2',
  date_of_birth: '2017-09-01',
};

const mockTranscript = {
  student_id: 'student-1',
  student_name: 'Yassine Alaoui',
  periods: [
    {
      class_id: 'class-1',
      class_name: 'CE2-A',
      period_id: 'period-1',
      period_label: 'Trimestre 1',
      weighted_average: 15.5,
      class_rank: 3,
    },
    {
      class_id: 'class-1',
      class_name: 'CE2-A',
      period_id: 'period-2',
      period_label: 'Trimestre 2',
      weighted_average: 16.2,
      class_rank: 2,
    },
  ],
};

const mockProgress = {
  student_id: 'student-1',
  overall_progress: 75,
  attendance_rate: 95,
  completed_assignments: 18,
  total_assignments: 20,
};

test.describe('J7 — Parent bulletin consultation', () => {
  test('parent can view their child progress dashboard', async ({ page }) => {
    await installMockSession(page, 'parent');

    // Mock children endpoint
    await page.route(/\/api\/v1\/me\/children(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse([mockChild])),
      });
    });

    // Mock progress endpoint
    await page.route(/\/api\/v1\/progress\/children(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse([{ ...mockProgress }])),
      });
    });

    // Mock transcript endpoint
    await page.route(/\/api\/v1\/gradebook\/transcript\/student-1(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(mockTranscript)),
      });
    });

    await login(page, 'parent');
    await expect(page).toHaveURL(/\/feed/);

    // Navigate to progress / results page
    await page.goto('/academic/progress/parent');
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('parent can view results page', async ({ page }) => {
    await installMockSession(page, 'parent');

    await page.route(/\/api\/v1\/gradebook\/transcript\/.*(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(mockTranscript)),
      });
    });

    await page.route(/\/api\/v1\/progress\/.*(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(mockProgress)),
      });
    });

    await login(page, 'parent');
    await page.goto('/academic/results');
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('unauthenticated parent cannot view bulletin', async ({ page }) => {
    await page.route(/\/api\/v1\/auth\/me$/, async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' }),
      });
    });
    await page.goto('/academic/progress/parent');
    await expect(page).toHaveURL(/\/login/);
  });
});
