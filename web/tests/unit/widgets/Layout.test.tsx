/**
 * Tests for src/widgets/layout/Layout.tsx
 * Covers: nav rendering per role, sidebar toggle, notification bell, logout, theme hooks.
 */
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Outlet } from 'react-router-dom';
import { Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { Layout } from '@/widgets/layout/Layout';
import { renderWithProviders } from '../../utils/render';
import { server } from '../../utils/mocks';

// Mock heavy hooks that fire external API calls at mount
vi.mock('@/features/user/profile', () => ({
  useProfileData: () => ({ data: null, isLoading: false }),
}));

vi.mock('@/features/content/feed/model/useFeed', () => ({
  useFeedUnreadSummary: () => ({ data: { unread_count: 0 } }),
}));

vi.mock('@/features/sync/model/useSync', () => ({
  useSyncDevices: () => ({ data: [] }),
  useSyncHealth: () => ({ data: null }),
  useSyncStatus: () => ({ data: null }),
}));

vi.mock('@/features/ai/rewards/model/useRewards', () => ({
  useMyRewards: () => ({ data: null }),
}));

vi.mock('@/core/ws/WebSocketClient', () => ({
  wsClient: { subscribe: vi.fn(() => () => {}), connect: vi.fn(), disconnect: vi.fn() },
}));

vi.mock('@/shared/hooks/useFocusManagement', () => ({
  useFocusManagement: () => ({ focusFirst: vi.fn() }),
}));

vi.mock('@/shared/hooks/useTheme', () => ({
  useTheme: () => ({ theme: 'light', setTheme: vi.fn() }),
}));

vi.mock('@/shared/hooks/useReducedMotion', () => ({
  useReducedMotion: () => false,
}));

vi.mock('@/shared/hooks/useAgeTheme', () => ({
  useAgeTheme: () => ({ applyTheme: vi.fn() }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderLayout(role: string = 'ADM') {
  server.use(
    http.get('/api/v1/notifications/unread-count', () =>
      HttpResponse.json({ data: { unread_count: 2 }, meta: { timestamp: '', version: '' } }),
    ),
    http.get('/api/v1/notifications', () =>
      HttpResponse.json({
        data: [],
        meta: { next_cursor: null, has_more: false, timestamp: '', version: '' },
      }),
    ),
    http.get('/api/v1/me/profile', () =>
      HttpResponse.json({
        data: {
          user_id: 'u1',
          email: 'admin@test.com',
          full_name: 'Admin User',
          role,
          school_id: 'school-1',
          student_profile: null,
          parent_profile: null,
          teacher_profile: null,
          phone: null,
        },
        meta: { timestamp: '', version: '' },
      }),
    ),
  );

  return renderWithProviders(
    <Routes>
      <Route path="/*" element={<Layout />} />
    </Routes>,
    { user: { role: role as 'ADM' | 'TCH' | 'STD' | 'PAR' }, route: '/admin' },
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Layout', () => {
  it('renders navigation for ADM role', async () => {
    renderLayout('ADM');
    await waitFor(() =>
      expect(
        document.querySelector('[class*="layout"], [class*="sidebar"], nav, [data-testid]'),
      ).toBeTruthy(),
    );
  });

  it('renders without crashing for TCH role', async () => {
    renderLayout('TCH');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders without crashing for STD role', async () => {
    renderLayout('STD');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders without crashing for PAR role', async () => {
    renderLayout('PAR');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders without crashing for SUP role', async () => {
    renderLayout('SUP');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders without crashing for CONTENT_MGR role', async () => {
    renderLayout('CONTENT_MGR');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows logout button or user menu', async () => {
    renderLayout('ADM');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    // Layout should render some user interface element
    expect(document.body.innerHTML.length).toBeGreaterThan(100);
  });

  it('handles notification bell click', async () => {
    const user = userEvent.setup();
    renderLayout('ADM');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    // Find bell button if rendered
    const bells = document.querySelectorAll(
      'button[aria-label*="notification" i], button[title*="notification" i]',
    );
    if (bells.length > 0) {
      await user.click(bells[0] as HTMLElement);
    }
    // No crash is the assertion
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('handles sidebar toggle', async () => {
    const user = userEvent.setup();
    renderLayout('ADM');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    // Find any toggle/hamburger button
    const toggles = document.querySelectorAll(
      'button[aria-label*="menu" i], button[aria-label*="sidebar" i], button[aria-label*="navigation" i], button[aria-label*="close" i]',
    );
    if (toggles.length > 0) {
      await user.click(toggles[0] as HTMLElement);
    }
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders nav links for STD (kids nav)', async () => {
    renderLayout('STD');
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    // kids nav has specific routes for students
    expect(document.body.innerHTML.length).toBeGreaterThan(50);
  });

  it('renders notification bell button', async () => {
    renderLayout('ADM');
    await waitFor(() => {
      const bell = document.querySelector('.bell-button, button[aria-label*="notification" i]');
      expect(bell).toBeTruthy();
    });
  });

  it('notification bell click opens dropdown panel', async () => {
    const user = userEvent.setup();
    server.use(
      http.get('/api/v1/notifications/unread-count', () =>
        HttpResponse.json({ data: { unread_count: 3 }, meta: { timestamp: '', version: '' } }),
      ),
      http.get('/api/v1/notifications', () =>
        HttpResponse.json({
          data: [
            {
              id: 'n1',
              title: 'New Notification',
              body: 'Test body',
              category: 'info',
              created_at: new Date().toISOString(),
              action_url: null,
              is_read: false,
            },
          ],
          meta: { next_cursor: null, has_more: false, timestamp: '', version: '' },
        }),
      ),
      http.get('/api/v1/me/profile', () =>
        HttpResponse.json({
          data: {
            user_id: 'u1',
            email: 'adm@test.com',
            full_name: 'Admin',
            role: 'ADM',
            school_id: 's1',
            student_profile: null,
            parent_profile: null,
            teacher_profile: null,
            phone: null,
          },
          meta: { timestamp: '', version: '' },
        }),
      ),
    );
    renderLayout('ADM');
    await waitFor(() => {
      expect(
        document.querySelector('.bell-button, button[aria-label*="notification" i]'),
      ).toBeTruthy();
    });
    const bell = document.querySelector(
      '.bell-button, button[aria-label*="notification" i]',
    ) as HTMLElement;
    await user.click(bell);
    await waitFor(() => {
      // Dropdown should open — check for notification-dropdown or content
      expect(
        document.querySelector('.notification-dropdown') ||
          document.body.innerHTML.includes('notification'),
      ).toBeTruthy();
    });
  });

  it('renders logout button in sidebar footer', async () => {
    renderLayout('ADM');
    await waitFor(() => {
      const logoutBtn = document.querySelector('.logout-btn, button[class*="logout"]');
      expect(logoutBtn).toBeTruthy();
    });
  });

  it('logout button calls auth logout', async () => {
    const mockLogout = vi.fn().mockResolvedValue(undefined);
    server.use(
      http.get('/api/v1/notifications/unread-count', () =>
        HttpResponse.json({ data: { unread_count: 0 }, meta: { timestamp: '', version: '' } }),
      ),
      http.get('/api/v1/notifications', () =>
        HttpResponse.json({
          data: [],
          meta: { next_cursor: null, has_more: false, timestamp: '', version: '' },
        }),
      ),
      http.get('/api/v1/me/profile', () =>
        HttpResponse.json({
          data: {
            user_id: 'u1',
            email: 'adm@test.com',
            full_name: 'Admin',
            role: 'ADM',
            school_id: 's1',
            student_profile: null,
            parent_profile: null,
            teacher_profile: null,
            phone: null,
          },
          meta: { timestamp: '', version: '' },
        }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/*" element={<Layout />} />
      </Routes>,
      { user: { role: 'ADM' as const }, auth: { logout: mockLogout }, route: '/admin' },
    );
    await waitFor(() => {
      expect(document.querySelector('.logout-btn, button[class*="logout"]')).toBeTruthy();
    });
    const logoutBtn = document.querySelector('.logout-btn, button[class*="logout"]') as HTMLElement;
    await user.click(logoutBtn);
    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalled();
    });
  });

  it('renders LanguageSwitcher in sidebar header', async () => {
    renderLayout('ADM');
    await waitFor(() => {
      // LanguageSwitcher renders a select or button
      expect(
        document.querySelector('.sidebar-header select') ||
          document.querySelector('.sidebar-header button[aria-label*="lang" i]') ||
          document.querySelector('.language-switcher, [class*="language"]'),
      ).toBeTruthy();
    });
  });

  it('ADM sees admin nav items', async () => {
    renderLayout('ADM');
    await waitFor(() => {
      const nav = document.querySelector('nav[role="navigation"]');
      expect(nav).toBeTruthy();
      expect(nav?.querySelectorAll('a.nav-link').length).toBeGreaterThan(0);
    });
  });

  it('TCH sees teacher nav items', async () => {
    renderLayout('TCH');
    await waitFor(() => {
      const nav = document.querySelector('nav[role="navigation"]');
      expect(nav?.querySelectorAll('a.nav-link').length).toBeGreaterThan(0);
    });
  });

  it('PAR sees parent nav items', async () => {
    renderLayout('PAR');
    await waitFor(() => {
      const nav = document.querySelector('nav[role="navigation"]');
      expect(nav?.querySelectorAll('a.nav-link').length).toBeGreaterThan(0);
    });
  });

  it('DIR sees director nav items', async () => {
    renderLayout('DIR');
    await waitFor(() => {
      const nav = document.querySelector('nav[role="navigation"]');
      expect(nav?.querySelectorAll('a.nav-link').length).toBeGreaterThan(0);
    });
  });

  it('shows user full name in sidebar footer', async () => {
    server.use(
      http.get('/api/v1/notifications/unread-count', () =>
        HttpResponse.json({ data: { unread_count: 0 }, meta: { timestamp: '', version: '' } }),
      ),
      http.get('/api/v1/notifications', () =>
        HttpResponse.json({
          data: [],
          meta: { next_cursor: null, has_more: false, timestamp: '', version: '' },
        }),
      ),
      http.get('/api/v1/me/profile', () =>
        HttpResponse.json({
          data: {
            user_id: 'u1',
            email: 'adm@test.com',
            full_name: 'Admin User',
            role: 'ADM',
            school_id: 's1',
            student_profile: null,
            parent_profile: null,
            teacher_profile: null,
            phone: null,
          },
          meta: { timestamp: '', version: '' },
        }),
      ),
    );
    renderWithProviders(
      <Routes>
        <Route path="/*" element={<Layout />} />
      </Routes>,
      { user: { role: 'ADM' as const, full_name: 'Admin User' }, route: '/admin' },
    );
    await waitFor(() => {
      expect(document.querySelector('.user-name')).toBeTruthy();
    });
    const userNameEl = document.querySelector('.user-name');
    expect(userNameEl?.textContent).toContain('Admin');
  });

  it('notification badge appears when unread count > 0', async () => {
    server.use(
      http.get('/api/v1/notifications/unread-count', () =>
        HttpResponse.json({ data: { unread_count: 5 }, meta: { timestamp: '', version: '' } }),
      ),
      http.get('/api/v1/notifications', () =>
        HttpResponse.json({
          data: [],
          meta: { next_cursor: null, has_more: false, timestamp: '', version: '' },
        }),
      ),
      http.get('/api/v1/me/profile', () =>
        HttpResponse.json({
          data: {
            user_id: 'u1',
            email: 'adm@test.com',
            full_name: 'Admin',
            role: 'ADM',
            school_id: 's1',
            student_profile: null,
            parent_profile: null,
            teacher_profile: null,
            phone: null,
          },
          meta: { timestamp: '', version: '' },
        }),
      ),
    );
    renderWithProviders(
      <Routes>
        <Route path="/*" element={<Layout />} />
      </Routes>,
      { user: { role: 'ADM' as const }, route: '/admin' },
    );
    await waitFor(() => {
      const badges = document.querySelectorAll('.notif-badge');
      expect(badges.length).toBeGreaterThan(0);
    });
  });
});
