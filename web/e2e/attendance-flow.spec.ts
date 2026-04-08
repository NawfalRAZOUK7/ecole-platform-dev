import { expect, test } from '@playwright/test';
import { expectPageTitle, login, logout } from './helpers';
import { apiResponse, installMockSession } from './mockApi';

test.describe('Attendance flow', () => {
  test('teacher marks attendance and parent views history', async ({ page }) => {
    test.setTimeout(60_000);

    const today = '2026-04-06';
    const classOption = {
      id: 'class-1',
      code: '6A',
      name: 'Sixieme A',
    };

    let records = [
      {
        id: 'attendance-1',
        student_id: 'student-1',
        student_name: 'Yassine Alaoui',
        date: `${today}T08:00:00.000Z`,
        status: 'present',
        justified: false,
        justification: null,
      },
      {
        id: 'attendance-2',
        student_id: 'student-2',
        student_name: 'Sara Benkirane',
        date: `${today}T08:00:00.000Z`,
        status: 'present',
        justified: false,
        justification: null,
      },
    ];

    await installMockSession(page, 'teacher');

    await page.route(/\/api\/v1\/teacher\/classes(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse([classOption])),
      });
    });

    await page.route(/\/api\/v1\/attendance\/class\/class-1(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'POST') {
        const payload = route.request().postDataJSON() as {
          date: string;
          records: Array<{ student_id: string; status: string; note?: string }>;
        };

        records = records.map((record) => {
          const nextRecord = payload.records.find((item) => item.student_id === record.student_id);

          if (!nextRecord) {
            return record;
          }

          return {
            ...record,
            date: `${payload.date}T08:00:00.000Z`,
            status: nextRecord.status,
            justification: nextRecord.note ?? null,
          };
        });

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
        body: JSON.stringify(apiResponse(records)),
      });
    });

    await page.route(/\/api\/v1\/analytics\/attendance\/student\/.+$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiResponse(records.filter((record) => record.student_id === 'student-1')),
        ),
      });
    });

    await login(page, 'teacher');
    await page.goto('/attendance');
    await expectPageTitle(page, /Presence|Attendance/i);

    const firstLateButton = page.locator('.attendance-status-pill--late').first();
    await firstLateButton.click();
    await page.locator('.attendance-page__actions .btn.btn-primary').click();

    await expect(page.locator('.attendance-banner--success')).toContainText(
      /Presence enregistree|Attendance saved/i,
    );
    await expect(page.locator('.attendance-page__footer')).toContainText(/En retard|Late/i);

    await logout(page);

    await login(page, 'parent');
    await page.goto('/attendance/history');
    await expectPageTitle(page, /Historique de presence|Attendance history/i);

    await expect(page.locator('.attendance-heatmap')).toBeVisible();
    await expect(page.locator('.attendance-heatmap')).toContainText(/En retard|Late/i);
  });
});
