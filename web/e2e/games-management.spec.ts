import { expect, test } from '@playwright/test';
import { expectPageTitle, login } from './helpers';
import { apiListResponse, apiResponse, installMockSession } from './mockApi';

type RawGameConfig = {
  id: string;
  game_type: string;
  title: string;
  title_ar: string | null;
  title_fr: string | null;
  subject: string | null;
  difficulty: string;
  target_age_min: number | null;
  target_age_max: number | null;
  config: Record<string, unknown>;
  reward_stars: number;
  reward_xp: number;
  school_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

test.describe('Games management flow', () => {
  test('teacher creates and edits a memory match game', async ({ page }) => {
    let nextId = 2;
    let configs: RawGameConfig[] = [
      {
        id: 'game-1',
        game_type: 'sorting',
        title: 'Tri des couleurs',
        title_ar: null,
        title_fr: 'Tri des couleurs',
        subject: 'art',
        difficulty: 'easy',
        target_age_min: 5,
        target_age_max: 7,
        config: {
          categories: [
            {
              name: 'Rouge',
              items: ['fraise', 'pomme'],
            },
          ],
        },
        reward_stars: 8,
        reward_xp: 12,
        school_id: null,
        is_active: true,
        created_at: '2026-04-10T09:00:00.000Z',
        updated_at: '2026-04-10T09:00:00.000Z',
      },
    ];

    await installMockSession(page, 'teacher');

    await page.route(/\/api\/v1\/games\/configs(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'POST') {
        const payload = route.request().postDataJSON() as Record<string, unknown>;
        const now = new Date().toISOString();
        const created: RawGameConfig = {
          id: `game-${nextId++}`,
          game_type: String(payload.game_type ?? 'memory_match'),
          title: String(payload.title ?? ''),
          title_ar: typeof payload.title_ar === 'string' ? payload.title_ar : null,
          title_fr: typeof payload.title_fr === 'string' ? payload.title_fr : null,
          subject: typeof payload.subject === 'string' ? payload.subject : null,
          difficulty: String(payload.difficulty ?? 'easy'),
          target_age_min:
            typeof payload.target_age_min === 'number' ? payload.target_age_min : null,
          target_age_max:
            typeof payload.target_age_max === 'number' ? payload.target_age_max : null,
          config: (payload.config as Record<string, unknown> | undefined) ?? {},
          reward_stars: Number(payload.reward_stars ?? 0),
          reward_xp: Number(payload.reward_xp ?? 0),
          school_id: typeof payload.school_id === 'string' ? payload.school_id : null,
          is_active: payload.is_active !== false,
          created_at: now,
          updated_at: now,
        };
        configs = [created, ...configs];

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiResponse(created)),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse(configs)),
      });
    });

    await page.route(/\/api\/v1\/games\/configs\/[^/?]+(?:\?.*)?$/, async (route) => {
      const id = route.request().url().split('/').pop()?.split('?')[0] ?? '';
      const existing = configs.find((config) => config.id === id);

      if (!existing) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: { message: 'Not found' } }),
        });
        return;
      }

      if (route.request().method() === 'PUT') {
        const payload = route.request().postDataJSON() as Record<string, unknown>;
        const updated: RawGameConfig = {
          ...existing,
          game_type: typeof payload.game_type === 'string' ? payload.game_type : existing.game_type,
          title: typeof payload.title === 'string' ? payload.title : existing.title,
          title_ar:
            payload.title_ar === null || typeof payload.title_ar === 'string'
              ? (payload.title_ar as string | null)
              : existing.title_ar,
          title_fr:
            payload.title_fr === null || typeof payload.title_fr === 'string'
              ? (payload.title_fr as string | null)
              : existing.title_fr,
          subject:
            payload.subject === null || typeof payload.subject === 'string'
              ? (payload.subject as string | null)
              : existing.subject,
          difficulty:
            typeof payload.difficulty === 'string' ? payload.difficulty : existing.difficulty,
          target_age_min:
            payload.target_age_min === null || typeof payload.target_age_min === 'number'
              ? (payload.target_age_min as number | null)
              : existing.target_age_min,
          target_age_max:
            payload.target_age_max === null || typeof payload.target_age_max === 'number'
              ? (payload.target_age_max as number | null)
              : existing.target_age_max,
          config: (payload.config as Record<string, unknown> | undefined) ?? existing.config,
          reward_stars:
            typeof payload.reward_stars === 'number' ? payload.reward_stars : existing.reward_stars,
          reward_xp: typeof payload.reward_xp === 'number' ? payload.reward_xp : existing.reward_xp,
          school_id:
            payload.school_id === null || typeof payload.school_id === 'string'
              ? (payload.school_id as string | null)
              : existing.school_id,
          is_active:
            typeof payload.is_active === 'boolean' ? payload.is_active : existing.is_active,
          updated_at: new Date().toISOString(),
        };
        configs = configs.map((config) => (config.id === id ? updated : config));

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiResponse(updated)),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(existing)),
      });
    });

    await login(page, 'teacher');

    await page.goto('/teacher/games');
    await expectPageTitle(page, /configurations de jeux|game configurations/i);

    await page.getByRole('button', { name: /creer un jeu|create game/i }).click();
    await expect(page).toHaveURL(/\/teacher\/games\/new/);
    await expectPageTitle(page, /creer une config|create/i);

    const createdTitle = `Memory E2E ${Date.now()}`;
    await page.getByLabel(/^Titre$|^Title$/i).fill(createdTitle);
    await page.getByLabel(/Titre arabe|Arabic title/i).fill('لعبة مطابقة');
    await page.getByLabel(/Titre francais|French title/i).fill('Jeu de memoire');
    await page.getByLabel(/^Matiere$|^Subject$/i).fill('math');
    await page.getByLabel(/Difficulte|Difficulty/i).selectOption('medium');
    await page.getByLabel(/Age min|Min age/i).fill('7');
    await page.getByLabel(/Age max|Max age/i).fill('9');
    await page.getByLabel(/Etoiles offertes|Reward stars/i).fill('14');
    await page.getByLabel(/XP offert|Reward XP/i).fill('21');
    await page.getByLabel(/Colonnes de la grille|Grid columns/i).fill('3');
    await page.getByLabel(/Lignes de la grille|Grid rows/i).fill('4');
    await page.getByLabel(/Limite de temps|Time limit/i).fill('90');
    await page.getByLabel(/Texte avant|Front text/i).fill('Soleil');
    await page.getByLabel(/Texte arriere|Back text/i).fill('Sun');

    await page.getByRole('button', { name: /creer la config|create config/i }).click();
    await expect(page).toHaveURL(/\/teacher\/games\/game-2/);
    await expect(page.locator('.page-title')).toContainText(createdTitle);

    const updatedTitle = `${createdTitle} Modifie`;
    await page.getByLabel(/^Titre$|^Title$/i).fill(updatedTitle);
    await page.getByLabel(/Etoiles offertes|Reward stars/i).fill('18');
    await page.getByRole('button', { name: /enregistrer les modifications|save changes/i }).click();

    await expect(page.locator('.page-title')).toContainText(updatedTitle);
    await expect(
      page
        .locator('.card')
        .filter({ hasText: /18 etoiles|18 stars/i })
        .first(),
    ).toBeVisible();

    await page.getByRole('button', { name: /retour aux jeux|back to games/i }).click();
    await expect(page).toHaveURL('/teacher/games');
    await expect(page.getByRole('button', { name: updatedTitle })).toBeVisible();
  });
});
