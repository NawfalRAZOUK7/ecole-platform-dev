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

    await page.route(/\/api\/v1\/gradebook\/class-1\/period-1$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiResponse({
            class_id: 'class-1',
            class_name: 'Sixieme A',
            categories: [
              { id: 'category-quiz', name: 'Quiz', weight: 0.4 },
              { id: 'category-project', name: 'Project', weight: 0.6 },
            ],
            assignments: [
              {
                assignment_id: 'assessment-1',
                title: 'Controle 1',
                category_id: 'category-quiz',
                total_points: 20,
                due_at: '2026-02-10',
              },
              {
                assignment_id: 'assessment-2',
                title: 'Projet sciences',
                category_id: 'category-project',
                total_points: 20,
                due_at: '2026-03-18',
              },
            ],
            rows: [
              {
                student_id: 'student-1',
                student_name: 'Yassine Alaoui',
                assignments: [
                  { assignment_id: 'assessment-1', score: 12 },
                  { assignment_id: 'assessment-2', score: studentSummary.grades[1]?.value },
                ],
                weighted_average: studentSummary.overall_average,
              },
            ],
          }),
        ),
      });
    });

    await page.route(/\/api\/v1\/gradebook\/transcript\/student-1(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiResponse({
            student_id: studentSummary.student_id,
            student_name: studentSummary.student_name,
            periods: [
              {
                class_id: 'class-1',
                class_name: studentSummary.class_name,
                period_id: 'period-1',
                period_label: 'Trimestre 1',
                weighted_average: studentSummary.overall_average,
                class_rank: 1,
              },
              {
                class_id: 'class-1',
                class_name: studentSummary.class_name,
                period_id: 'assessment-1',
                period_label: 'Controle 1',
                weighted_average: studentSummary.grades[0]?.value ?? 0,
                class_rank: 1,
              },
              {
                class_id: 'class-1',
                class_name: studentSummary.class_name,
                period_id: 'assessment-2',
                period_label: 'Projet sciences',
                weighted_average: studentSummary.grades[1]?.value ?? 0,
                class_rank: 1,
              },
            ],
          }),
        ),
      });
    });

    await login(page, 'teacher');
    await page.goto('/gradebook');
    await expectPageTitle(page, /Carnet de notes|Gradebook/i);

    const studentRow = page.locator('.gradebook-table tbody tr').first();
    await expect(studentRow).toContainText(/Yassine Alaoui/i);
    await studentRow.locator('input').nth(1).fill('18');
    await page.locator('.gradebook-page__footer .btn.btn-primary').click();

    await expect(page.locator('.attendance-banner--success')).toContainText(
      /Notes enregistrees|Grades saved/i,
    );
    await expect(studentRow.locator('.gradebook-average')).toContainText('15.60');

    studentSummary = {
      ...studentSummary,
      overall_average: 15.6,
      grades: studentSummary.grades.map((grade) =>
        grade.assessment_id === 'assessment-2' ? { ...grade, value: 18 } : grade,
      ),
    };

    await logout(page);

    await login(page, 'student');
    await page.goto('/gradebook/student/student-1');
    await expectPageTitle(page, /Yassine Alaoui/i);
    await expect(page.locator('.data-table')).toContainText(/Projet sciences/i);
    await expect(page.locator('.data-table')).toContainText('18.0');
  });
});
