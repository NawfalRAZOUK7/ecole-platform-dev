import { expect, test } from '@playwright/test';
import { expectPageTitle, login, logout } from './helpers';
import { apiResponse, installMockSession } from './mockApi';

test.describe('Gradebook flow', () => {
  test('teacher enters grades and student views the detail page', async ({ page }) => {
    const classOption = { id: 'class-1', code: '6A', name: 'Sixieme A' };
    const periods = [
      {
        id: 'period-1',
        label: 'Trimestre 1',
        date_start: '2026-01-05',
        date_end: '2026-03-30',
      },
    ];

    const columns = [
      { assessment_id: 'assessment-1', title: 'Controle 1', weight: 0.4 },
      { assessment_id: 'assessment-2', title: 'Projet sciences', weight: 0.6 },
    ];

    let studentSummary = {
      student_id: 'student-1',
      student_name: 'Yassine Alaoui',
      class_name: 'Sixieme A',
      overall_average: 12,
      grades: [
        {
          assessment_id: 'assessment-1',
          title: 'Controle 1',
          date: '2026-02-10',
          value: 12,
          weight: 0.4,
        },
        {
          assessment_id: 'assessment-2',
          title: 'Projet sciences',
          date: '2026-03-18',
          value: null,
          weight: 0.6,
        },
      ],
    };

    await installMockSession(page, 'teacher');

    await page.route(/\/api\/v1\/teacher\/classes(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse([classOption])),
      });
    });

    await page.route(/\/api\/v1\/teacher\/periods(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(periods)),
      });
    });

    await page.route(/\/api\/v1\/gradebook\/class\/class-1$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiResponse({
            class_id: 'class-1',
            class_name: 'Sixieme A',
            columns,
            entries: [
              {
                student_id: 'student-1',
                student_name: 'Yassine Alaoui',
                grades: {
                  'assessment-1': 12,
                  'assessment-2': studentSummary.grades[1]?.value,
                },
                weighted_average: studentSummary.overall_average,
              },
            ],
          })
        ),
      });
    });

    await page.route(/\/api\/v1\/gradebook\/class\/class-1\/weighted-summary$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiResponse({
            class_id: 'class-1',
            class_average: studentSummary.overall_average,
            pass_rate: 100,
            highest_average: studentSummary.overall_average,
            lowest_average: studentSummary.overall_average,
          })
        ),
      });
    });

    await page.route(/\/api\/v1\/gradebook\/class\/class-1\/grades$/, async (route) => {
      const payload = route.request().postDataJSON() as {
        grades: Array<{ student_id: string; assessment_id: string; value: number }>;
      };
      const projectGrade = payload.grades.find(
        (item) =>
          item.student_id === 'student-1' && item.assessment_id === 'assessment-2'
      );

      if (projectGrade) {
        studentSummary = {
          ...studentSummary,
          overall_average: 15.6,
          grades: studentSummary.grades.map((grade) =>
            grade.assessment_id === 'assessment-2'
              ? { ...grade, value: projectGrade.value }
              : grade
          ),
        };
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(null)),
      });
    });

    await page.route(/\/api\/v1\/gradebook\/student\/student-1$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(studentSummary)),
      });
    });

    await login(page, 'teacher');
    await page.goto('/gradebook');
    await expectPageTitle(page, /Carnet de notes|Gradebook/i);

    const studentRow = page.locator('.gradebook-table tbody tr').first();
    await studentRow.locator('input').nth(1).fill('18');
    await page.locator('.gradebook-page__footer .btn.btn-primary').click();

    await expect(page.locator('.attendance-banner--success')).toContainText(
      /Notes enregistrees|Grades saved/i
    );
    await expect(studentRow.locator('.gradebook-average')).toContainText('15.60');

    await logout(page);

    await login(page, 'student');
    await page.goto('/gradebook/student/student-1');
    await expectPageTitle(page, /Yassine Alaoui/i);
    await expect(page.locator('.data-table')).toContainText(/Projet sciences/i);
    await expect(page.locator('.data-table')).toContainText('18.0');
  });
});
