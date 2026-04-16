import { expect, test } from '@playwright/test';
import { expectPageTitle, login } from './helpers';
import { apiListResponse, apiResponse, installMockSession } from './mockApi';

type RawBadge = {
  id: string;
  code: string;
  title_fr: string;
  title_ar: string;
  title_en: string;
  description_fr: string | null;
  description_ar: string | null;
  description_en: string | null;
  icon: string | null;
  criteria_type: string;
  criteria_value: number;
  display_order: number;
  is_active: boolean;
};

test.describe('Admin badge management flow', () => {
  test('admin creates, edits, and toggles a badge', async ({ page }) => {
    let nextId = 2;
    let badges: RawBadge[] = [
      {
        id: 'badge-1',
        code: 'FIRST_WIN',
        title_fr: 'Premiere victoire',
        title_ar: 'اول فوز',
        title_en: 'First Win',
        description_fr: 'Gagne une premiere activite.',
        description_ar: 'اربح نشاطا اول.',
        description_en: 'Win a first activity.',
        icon: '🏆',
        criteria_type: 'event_count',
        criteria_value: 1,
        display_order: 1,
        is_active: true,
      },
    ];

    await installMockSession(page, 'admin');

    await page.route(/\/api\/v1\/rewards\/badges(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'POST') {
        const payload = route.request().postDataJSON() as Record<string, unknown>;
        const created: RawBadge = {
          id: `badge-${nextId++}`,
          code: String(payload.code ?? ''),
          title_fr: String(payload.title_fr ?? ''),
          title_ar: String(payload.title_ar ?? ''),
          title_en: String(payload.title_en ?? ''),
          description_fr:
            payload.description_fr === null || typeof payload.description_fr === 'string'
              ? (payload.description_fr as string | null)
              : null,
          description_ar:
            payload.description_ar === null || typeof payload.description_ar === 'string'
              ? (payload.description_ar as string | null)
              : null,
          description_en:
            payload.description_en === null || typeof payload.description_en === 'string'
              ? (payload.description_en as string | null)
              : null,
          icon:
            payload.icon === null || typeof payload.icon === 'string'
              ? (payload.icon as string | null)
              : null,
          criteria_type: String(payload.criteria_type ?? 'manual'),
          criteria_value: Number(payload.criteria_value ?? 0),
          display_order: Number(payload.display_order ?? 0),
          is_active: payload.is_active !== false,
        };
        badges = [...badges, created];

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
        body: JSON.stringify(apiListResponse(badges)),
      });
    });

    await page.route(/\/api\/v1\/rewards\/badges\/[^/?]+(?:\?.*)?$/, async (route) => {
      const id = route.request().url().split('/').pop()?.split('?')[0] ?? '';
      const existing = badges.find((badge) => badge.id === id);

      if (!existing) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: { message: 'Not found' } }),
        });
        return;
      }

      const payload = route.request().postDataJSON() as Record<string, unknown>;
      const updated: RawBadge = {
        ...existing,
        code: typeof payload.code === 'string' ? payload.code : existing.code,
        title_fr: typeof payload.title_fr === 'string' ? payload.title_fr : existing.title_fr,
        title_ar: typeof payload.title_ar === 'string' ? payload.title_ar : existing.title_ar,
        title_en: typeof payload.title_en === 'string' ? payload.title_en : existing.title_en,
        description_fr:
          payload.description_fr === null || typeof payload.description_fr === 'string'
            ? (payload.description_fr as string | null)
            : existing.description_fr,
        description_ar:
          payload.description_ar === null || typeof payload.description_ar === 'string'
            ? (payload.description_ar as string | null)
            : existing.description_ar,
        description_en:
          payload.description_en === null || typeof payload.description_en === 'string'
            ? (payload.description_en as string | null)
            : existing.description_en,
        icon:
          payload.icon === null || typeof payload.icon === 'string'
            ? (payload.icon as string | null)
            : existing.icon,
        criteria_type:
          typeof payload.criteria_type === 'string'
            ? payload.criteria_type
            : existing.criteria_type,
        criteria_value:
          typeof payload.criteria_value === 'number'
            ? payload.criteria_value
            : existing.criteria_value,
        display_order:
          typeof payload.display_order === 'number'
            ? payload.display_order
            : existing.display_order,
        is_active: typeof payload.is_active === 'boolean' ? payload.is_active : existing.is_active,
      };
      badges = badges.map((badge) => (badge.id === id ? updated : badge));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(updated)),
      });
    });

    await login(page, 'admin');

    await page.goto('/admin/badges');
    await expectPageTitle(page, /gestion des badges|badge management/i);

    await page.getByRole('button', { name: /creer un badge|create badge/i }).click();

    const badgeCode = `E2E_BADGE_${Date.now()}`;
    await page.getByLabel(/^Code$/i).fill(badgeCode);
    await page.getByLabel(/Titre \(francais\)|Title \(French\)/i).fill('Badge E2E');
    await page.getByLabel(/Titre \(arabe\)|Title \(Arabic\)/i).fill('شارة تجريبية');
    await page.getByLabel(/Titre \(anglais\)|Title \(English\)/i).fill('E2E Badge');
    await page
      .getByLabel(/Description \(anglais\)|Description \(English\)/i)
      .fill('Created by the Playwright test.');
    await page.getByLabel(/URL de l'icone|Icon URL or uploaded image/i).fill('🏅');
    await page.getByLabel(/Valeur du critere|Criteria Value/i).fill('4');
    await page.getByLabel(/Ordre d'affichage|Display Order/i).fill('3');
    await page.getByRole('button', { name: /^Enregistrer$|^Save$/i }).click();

    const createdRow = page.getByRole('row', { name: new RegExp(badgeCode, 'i') });
    await expect(createdRow).toBeVisible();
    await expect(createdRow).toContainText(/E2E Badge/);

    await createdRow.getByRole('button', { name: /modifier|edit/i }).click();
    await page.getByLabel(/Titre \(anglais\)|Title \(English\)/i).fill('E2E Badge Updated');
    await page.getByRole('button', { name: /^Enregistrer$|^Save$/i }).click();

    await expect(
      page.getByRole('row', { name: new RegExp(`${badgeCode}.*E2E Badge Updated`, 'i') }),
    ).toBeVisible();

    const updatedRow = page.getByRole('row', { name: new RegExp(badgeCode, 'i') });
    await updatedRow.getByRole('checkbox').click();
    await expect(updatedRow).toContainText(/Inactif|Inactive/i);

    await page.reload();
    await expect(
      page.getByRole('row', { name: new RegExp(`${badgeCode}.*(Inactif|Inactive)`, 'i') }),
    ).toBeVisible();
  });
});
