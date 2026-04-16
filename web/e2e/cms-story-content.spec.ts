import { Buffer } from 'node:buffer';
import { expect, test } from '@playwright/test';
import { expectPageTitle, login } from './helpers';
import { apiListResponse, apiResponse, installMockSession } from './mockApi';

type CmsContentRecord = {
  id: string;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  page_count: number | null;
  letter: string | null;
  target_age_min: number | null;
  target_age_max: number | null;
  theme_color: string | null;
  thumbnail_path: string | null;
  origin: string;
  status: string;
  created_by: string | null;
  original_content_id: string | null;
};

test.describe('CMS story upload flow', () => {
  test('content manager uploads a story and sees it in the library', async ({ page }) => {
    let nextId = 2;
    let contents: CmsContentRecord[] = [];

    await installMockSession(page, 'content_manager');

    await page.route(/\/api\/v1\/cms\/submissions(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse([])),
      });
    });

    await page.route(/\/api\/v1\/cms\/content(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'POST') {
        const payload = route.request().postDataJSON() as Record<string, unknown>;
        const created: CmsContentRecord = {
          id: `content-${nextId++}`,
          title: String(payload.title ?? ''),
          content_type: String(payload.content_type ?? 'story'),
          level_band: typeof payload.level_band === 'string' ? payload.level_band : null,
          language: typeof payload.language === 'string' ? payload.language : null,
          subject: typeof payload.subject === 'string' ? payload.subject : null,
          description: typeof payload.description === 'string' ? payload.description : null,
          page_count: typeof payload.page_count === 'number' ? payload.page_count : null,
          letter:
            payload.letter === null || typeof payload.letter === 'string'
              ? (payload.letter as string | null)
              : null,
          target_age_min:
            typeof payload.target_age_min === 'number' ? payload.target_age_min : null,
          target_age_max:
            typeof payload.target_age_max === 'number' ? payload.target_age_max : null,
          theme_color: typeof payload.theme_color === 'string' ? payload.theme_color : null,
          thumbnail_path: null,
          origin: 'PLATFORM',
          status: String(payload.status ?? 'draft'),
          created_by: 'content-manager-1',
          original_content_id: null,
        };
        contents = [created, ...contents];

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiResponse({ id: created.id })),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse(contents)),
      });
    });

    await page.route(/\/api\/v1\/content-items\/[^/]+\/assets$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse({ uploaded: true })),
      });
    });

    await login(page, 'content_manager');
    await expect(page).toHaveURL(/\/cms/);

    await page.goto('/cms/upload');
    await expectPageTitle(page, /telecharger du contenu|upload content/i);

    await page.getByLabel(/Type de contenu|Content type/i).selectOption('story');

    await expect(page.getByLabel(/Nombre de pages|Page count/i)).toBeVisible();
    await expect(page.getByLabel(/^Lettre$|^Letter$/i)).toBeVisible();
    await expect(page.getByLabel(/Age cible min|Target age min/i)).toBeVisible();
    await expect(page.getByLabel(/Age cible max|Target age max/i)).toBeVisible();
    await expect(page.getByLabel(/Couleur du theme|Theme color/i)).toBeVisible();

    const storyTitle = `Histoire E2E ${Date.now()}`;
    await page.getByLabel(/^Titre$|^Title$/i).fill(storyTitle);
    await page.getByLabel(/Description/i).fill('Conte de test pour la bibliotheque CMS.');
    await page.getByLabel(/Nombre de pages|Page count/i).fill('8');
    await page.getByLabel(/^Lettre$|^Letter$/i).fill('AL');
    await page.getByLabel(/Age cible min|Target age min/i).fill('4');
    await page.getByLabel(/Age cible max|Target age max/i).fill('7');
    await page.getByLabel(/Couleur du theme|Theme color/i).fill('#ff8800');

    await page
      .locator('input[type="file"]')
      .first()
      .setInputFiles({
        name: 'story.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('%PDF-1.4 mock story content'),
      });

    await page.getByRole('button', { name: /^(telecharger|upload)$/i }).click();

    await expect(
      page.getByRole('button', { name: /retour a la liste|back to list/i }),
    ).toBeVisible();
    await page.getByRole('button', { name: /retour a la liste|back to list/i }).click();

    await expect(page).toHaveURL('/cms');
    const storyCard = page.locator('.card').filter({ hasText: storyTitle }).first();
    await expect(storyCard).toBeVisible();
    await expect(storyCard).toContainText(/story|histoire/i);
  });
});
