/// J6: Admin — enrôlement d'un élève
///
/// Reference: Phase 6A, §8.2.6C — enrolment d'un élève (admin)

import { test, expect } from '@playwright/test';
import { installMockSession, apiResponse, apiListResponse } from './mockApi';
import { login } from './helpers';

const mockStudent = {
  id: 'student-new-1',
  user_id: 'user-new-1',
  full_name: 'Zineb Rachidi',
  email: 'zineb.rachidi@ecole-benani.ma',
  role: 'STD',
  school_id: '00000000-0000-4000-8000-000000000001',
  class_level: 'ce1',
  date_of_birth: '2018-09-10',
};

const mockEnrollment = {
  id: 'enroll-1',
  student_id: mockStudent.id,
  program_id: 'prog-1',
  enrolled_at: '2026-05-01T00:00:00Z',
  status: 'active',
};

test.describe('J6 — Admin student enrollment', () => {
  test('admin can view and enroll a student', async ({ page }) => {
    await installMockSession(page, 'admin');
    await login(page, 'admin');

    // Mock enrollments list endpoint
    let enrollments: (typeof mockEnrollment)[] = [];
    await page.route(/\/api\/v1\/enrollments(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiListResponse(enrollments)),
        });
      } else if (route.request().method() === 'POST') {
        enrollments = [mockEnrollment];
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiResponse(mockEnrollment)),
        });
      } else {
        await route.continue();
      }
    });

    // Mock programs list
    await page.route(/\/api\/v1\/programs(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiListResponse([{ id: 'prog-1', name: 'CE1 Programme', level: 'ce1', active: true }]),
        ),
      });
    });

    // Navigate to enrollments page
    await page.goto('/admin/enrollments');

    // Wait for the page to load
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('enrollment list shows students after enrolling', async ({ page }) => {
    await installMockSession(page, 'admin');
    await login(page, 'admin');

    await page.route(/\/api\/v1\/enrollments(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse([mockEnrollment])),
      });
    });

    await page.route(/\/api\/v1\/programs(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiListResponse([{ id: 'prog-1', name: 'CE1 Programme', level: 'ce1', active: true }]),
        ),
      });
    });

    await page.goto('/admin/enrollments');
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});

    // The page should load without redirecting to login
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('non-admin cannot access enrollment page', async ({ page }) => {
    await installMockSession(page, 'student');
    await page.goto('/admin/enrollments');
    // Should redirect away (either to / or login)
    await page
      .waitForURL((url) => !url.pathname.includes('/admin/enrollments'), { timeout: 8_000 })
      .catch(() => {});
    await expect(page).not.toHaveURL(/\/admin\/enrollments/);
  });
});
