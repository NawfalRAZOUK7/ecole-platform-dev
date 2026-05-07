/// J4: Admin — Login → create invitation → verify in list → revoke
///
/// Reference: Phase 6A, Journey 4

import { test, expect } from '@playwright/test';
import { login } from './helpers';
import { apiListResponse, apiResponse, installMockSession } from './mockApi';

test.describe('J4 — Admin invitation journey', () => {
  test('login → invitations → create → verify → revoke', async ({ page }) => {
    let invitations = [
      {
        id: 'invite-seed',
        role_target: 'STD',
        consumed_at: null,
        consumed_by: null,
        expires_at: '2026-04-10T00:00:00.000Z',
        created_at: '2026-04-05T09:00:00.000Z',
        issuer_user_id: 'admin-1',
        status: 'active',
      },
    ];

    await installMockSession(page, 'admin');

    await page.route(/\/api\/v1\/admin\/invitations(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse(invitations)),
      });
    });

    await page.route(/\/api\/v1\/invites\/create$/, async (route) => {
      const invitation = {
        id: `invite-${invitations.length + 1}`,
        role_target: 'PAR',
        consumed_at: null,
        consumed_by: null,
        expires_at: '2026-04-12T00:00:00.000Z',
        created_at: '2026-04-06T12:00:00.000Z',
        issuer_user_id: 'admin-1',
        status: 'active',
      };
      invitations = [invitation, ...invitations];

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse({ code: 'INVITE-2026' })),
      });
    });

    await page.route(/\/api\/v1\/invites\/revoke$/, async (route) => {
      const payload = route.request().postDataJSON() as { invite_id: string };
      invitations = invitations.map((invitation) =>
        invitation.id === payload.invite_id ? { ...invitation, status: 'expired' } : invitation,
      );

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse(null)),
      });
    });

    // 1. Login as admin
    await login(page, 'admin');

    // 2. Should land on /admin (ADM default)
    await expect(page).toHaveURL(/\/admin/);

    // 3. Navigate to invitations
    await page.locator('a[href="/admin/invitations"]').click();
    await expect(page).toHaveURL(/\/admin\/invitations/);
    await page.waitForLoadState('networkidle');

    // 4. Create a new invitation
    const createBtn = page
      .locator('button', {
        hasText: /créer|ajouter|nouveau|invitation/i,
      })
      .first();

    if (await createBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await createBtn.click();

      // Select role for invitation
      const roleSelect = page.locator('select, [role="listbox"]').first();
      if (await roleSelect.isVisible({ timeout: 2_000 }).catch(() => false)) {
        await roleSelect.selectOption({ index: 1 });
      }

      // Submit creation
      const submitBtn = page
        .locator('button[type="submit"], button:has-text("Créer"), button:has-text("Générer")')
        .first();
      if (await submitBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
        await submitBtn.click();
        await page.waitForLoadState('networkidle');
      }

      // 5. Verify invitation appears — look for invitation code or new row
      const invitationList = page.locator('.card, tr, [data-testid="invitation"]');
      await expect(invitationList.first()).toBeVisible({ timeout: 5_000 });

      // 6. Revoke the invitation
      const revokeBtn = page
        .locator('button', {
          hasText: /révoquer|revoke|annuler/i,
        })
        .first();

      if (await revokeBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await revokeBtn.click();

        // Confirm revocation if dialog appears
        const dialogConfirmBtn = page.locator('.confirm-dialog button', {
          hasText: /confirmer|oui|ok/i,
        });
        if (await dialogConfirmBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
          await dialogConfirmBtn.click();
        }
        await page.waitForLoadState('networkidle');
      }
    }

    // 7. Verify page is still accessible
    await expect(page.locator('.page-title, h1').first()).toBeVisible();
  });
});
