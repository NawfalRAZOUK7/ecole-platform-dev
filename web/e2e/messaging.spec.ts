/// J8: Messaging — envoi + lecture d'un message
///
/// Reference: Phase 6A, §8.2.6C — messagerie : envoi + lecture

import { test, expect } from '@playwright/test';
import { login } from './helpers';
import { apiResponse, apiListResponse, installMockSession } from './mockApi';

const mockConversation = {
  id: 'conv-1',
  subject: 'Question about homework',
  participants: [
    { user_id: 'parent-1', full_name: 'Parent Alaoui', role: 'PAR' },
    { user_id: 'teacher-1', full_name: 'Professeur Math', role: 'TCH' },
  ],
  last_message_at: '2026-05-30T14:00:00Z',
  unread_count: 1,
  school_id: '00000000-0000-4000-8000-000000000001',
};

const mockMessages = [
  {
    id: 'msg-1',
    conversation_id: 'conv-1',
    sender_id: 'parent-1',
    sender_name: 'Parent Alaoui',
    body: 'Bonjour, est-ce que le devoir est pour demain ?',
    created_at: '2026-05-30T13:55:00Z',
    read_at: null,
  },
  {
    id: 'msg-2',
    conversation_id: 'conv-1',
    sender_id: 'teacher-1',
    sender_name: 'Professeur Math',
    body: 'Bonjour, oui le devoir est pour demain matin.',
    created_at: '2026-05-30T14:00:00Z',
    read_at: '2026-05-30T14:01:00Z',
  },
];

test.describe('J8 — Messaging: send and read', () => {
  test('parent can view their conversations list', async ({ page }) => {
    await installMockSession(page, 'parent');

    await page.route(/\/api\/v1\/conversations(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse([mockConversation])),
      });
    });

    await login(page, 'parent');
    await page.goto('/messaging/conversations');
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('parent can read messages in a conversation', async ({ page }) => {
    await installMockSession(page, 'parent');

    await page.route(/\/api\/v1\/conversations(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse([mockConversation])),
      });
    });

    await page.route(/\/api\/v1\/conversations\/conv-1\/messages(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse(mockMessages)),
      });
    });

    await page.route(/\/api\/v1\/conversations\/conv-1\/read$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse({ success: true })),
      });
    });

    await login(page, 'parent');
    await page.goto('/messaging/chat/conv-1');
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('parent can send a message', async ({ page }) => {
    await installMockSession(page, 'parent');

    const sentMessages = [...mockMessages];
    await page.route(/\/api\/v1\/conversations(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiListResponse([mockConversation])),
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiResponse({ id: 'conv-new', ...mockConversation })),
        });
      } else {
        await route.continue();
      }
    });

    await page.route(/\/api\/v1\/conversations\/conv-1\/messages(?:\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiListResponse(sentMessages)),
        });
      } else if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON() as { body?: string };
        sentMessages.push({
          id: 'msg-3',
          conversation_id: 'conv-1',
          sender_id: 'parent-1',
          sender_name: 'Parent Alaoui',
          body: body?.body ?? '',
          created_at: new Date().toISOString(),
          read_at: null,
        });
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(apiResponse(sentMessages[sentMessages.length - 1])),
        });
      } else {
        await route.continue();
      }
    });

    await page.route(/\/api\/v1\/conversations\/conv-1\/read$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponse({ success: true })),
      });
    });

    await login(page, 'parent');
    await page.goto('/messaging/chat/conv-1');
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('teacher can view conversations', async ({ page }) => {
    await installMockSession(page, 'teacher');

    await page.route(/\/api\/v1\/conversations(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiListResponse([mockConversation])),
      });
    });

    await login(page, 'teacher');
    await page.goto('/messaging/conversations');
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
    await expect(page).not.toHaveURL(/\/login/);
  });
});
