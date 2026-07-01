/**
 * Ecole Platform — Screenshot Capture Script (v2)
 *
 * Auth cookies are Secure=true so document.cookie is empty over HTTP.
 * The app's AuthContext.tryRestore() checks document.cookie for csrf_token
 * and finds nothing on reload → redirects to /login.
 *
 * Solution: log in once per role via the form, then navigate exclusively via
 * React Router (history.pushState + popstate) to stay in the SPA
 * without triggering a full page reload (auth state in React memory stays alive).
 */

import { chromium } from '@playwright/test';
import { mkdirSync } from 'fs';
import { join } from 'path';

const BASE_URL  = 'http://localhost:5173';
const API_URL   = 'http://localhost:8000';
const OUT_DIR   = '/Users/nawfalrazouk/Ecole-Platform/ecole-platform-final-report/assets/screenshots';

const CREDS = {
  ADM: { email: 'admin@ecole-benani.ma',          password: 'admin123'      },
  TCH: { email: 'prof.math@ecole-benani.ma',      password: 'teacher123'    },
  STD: { email: 'yassine.alaoui@ecole-benani.ma', password: 'student123'    },
  SUP: { email: 'superadmin@ecole-platform.ma',   password: 'superadmin123' },
};

const delay = ms => new Promise(r => setTimeout(r, ms));

/** Navigate inside the running SPA without a full-page reload */
async function navTo(page, path, ms = 1600) {
  await page.evaluate(p => {
    window.history.pushState({}, '', p);
    window.dispatchEvent(new PopStateEvent('popstate', { state: {} }));
  }, path);
  await delay(ms);
}

/** Login via the form */
async function loginAs(ctx, role) {
  const { email, password } = CREDS[role];
  const page = await ctx.newPage();
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
  await page.fill('#email', email);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 12000 });
  await delay(1500);
  return page;
}

/** Snap a 1440×900 screenshot */
async function snap(page, rel, sel, extra = 0) {
  if (sel) await page.waitForSelector(sel, { timeout: 6000 }).catch(() => {});
  if (extra) await delay(extra);
  await page.screenshot({ path: join(OUT_DIR, rel), fullPage: false });
  console.log(`  ✓  ${rel}`);
}

const ctx = async browser => {
  const c = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
  });
  // Force the UI into French (the report is a French thesis). Arabic blocks
  // override this with their own 'ar' init script added after this one.
  await c.addInitScript(() => {
    try { localStorage.setItem('i18nextLng', 'fr'); } catch { /* ignore */ }
  });
  return c;
};

async function main() {
  const browser = await chromium.launch({ headless: true });

  // ── PUBLIC ─────────────────────────────────────────────────────────────────
  console.log('\n── PUBLIC ──');
  {
    const c = await ctx(browser);
    const pg = await c.newPage();
    await pg.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    await snap(pg, 'web/web_auth_login.png', 'form');
    await pg.goto(`${BASE_URL}/apply`, { waitUntil: 'networkidle' });
    await snap(pg, 'web/web_apply_onboarding.png', 'form,main');
    await pg.goto(`${BASE_URL}/activate`, { waitUntil: 'networkidle' });
    await snap(pg, 'web/web_activate_account.png', 'form,main');
    await c.close();
  }

  // ── ADM ────────────────────────────────────────────────────────────────────
  console.log('\n── ADM ──');
  {
    const c = await ctx(browser);
    const pg = await loginAs(c, 'ADM');
    await snap(pg, 'web/web_dashboard_admin.png', 'h1');
    await navTo(pg, '/profile');
    await snap(pg, 'web/web_profile.png', 'h1,.profile-hero', 400);
    await navTo(pg, '/invoices');
    await snap(pg, 'web/web_finance_invoice.png', 'h1,table');
    await navTo(pg, '/messages');
    await snap(pg, 'web/web_messages_conversations.png', 'h1,[class*="conversation"]');
    await navTo(pg, '/announcements');
    await snap(pg, 'web/web_announcements.png', 'h1,table');
    await c.close();
  }

  // ── SUP ────────────────────────────────────────────────────────────────────
  console.log('\n── SUP ──');
  {
    const c = await ctx(browser);
    const pg = await loginAs(c, 'SUP');
    await navTo(pg, '/platform');
    await snap(pg, 'web/web_platform_sup_console.png', 'h1,table');
    await c.close();
  }

  // ── TCH ────────────────────────────────────────────────────────────────────
  console.log('\n── TCH ──');
  {
    const c = await ctx(browser);
    const pg = await loginAs(c, 'TCH');

    await navTo(pg, '/teacher');
    await snap(pg, 'web/web_erp_classes.png', 'h1,table,[class*="class"]');

    await navTo(pg, '/teacher/courses');
    await snap(pg, 'web/web_lms_courses.png', 'h1,table,[class*="course"]');

    await navTo(pg, '/teacher/content-library');
    await snap(pg, 'web/web_teacher_content_library.png', 'h1,[class*="library"]', 500);

    // Upload dialog
    await navTo(pg, '/teacher/content-library');
    await delay(600);
    const upBtn = pg.locator('button').filter({ hasText: /upload|téléverser|ajouter|nouveau|new/i }).first();
    if (await upBtn.count() > 0 && await upBtn.isVisible()) { await upBtn.click(); await delay(600); }
    await snap(pg, 'web/web_teacher_content_upload.png', 'h1,[class*="modal"],[class*="dialog"],[class*="upload"]', 300);

    await navTo(pg, '/teacher/quizzes');
    await snap(pg, 'web/web_teacher_quizzes.png', 'h1,table,[class*="quiz"]');

    await navTo(pg, '/teacher/submissions');
    await snap(pg, 'web/web_teacher_submissions.png', 'h1,table');

    // Content submissions — same page, different tab if present
    const cTab = pg.locator('[role="tab"],button').filter({ hasText: /content|contenu/i }).first();
    if (await cTab.count() > 0) { await cTab.click(); await delay(400); }
    await snap(pg, 'web/web_teacher_content_submissions.png', 'h1,table', 200);

    await navTo(pg, '/question-bank/generate');
    await snap(pg, 'web/web_generate_quiz_dialog.png', 'h1,form', 400);

    await c.close();
  }

  // ── STD ────────────────────────────────────────────────────────────────────
  console.log('\n── STD ──');
  {
    const c = await ctx(browser);
    const pg = await loginAs(c, 'STD');

    await navTo(pg, '/student/home');
    await snap(pg, 'web/web_student_home_rewards.png', 'h1,[class*="reward"],[class*="home"]', 500);

    await navTo(pg, '/student/content');
    await snap(pg, 'web/web_student_content_library.png', 'h1,[class*="content"]', 600);

    // PDF player — try clicking first content item, then fall back to API lookup
    await navTo(pg, '/student/content');
    await delay(800);
    let opened = false;
    try {
      const contentId = await pg.evaluate(async () => {
        const r = await fetch('/api/v1/lms/content-items?limit=10', { credentials: 'include' });
        const j = await r.json();
        const item = (j?.data || []).find(x => x.content_type === 'pdf' || x.file_type === 'pdf');
        return item?.id || j?.data?.[0]?.id || null;
      });
      if (contentId) {
        await pg.evaluate(p => {
          window.history.pushState({}, '', p);
          window.dispatchEvent(new PopStateEvent('popstate', { state: {} }));
        }, `/student/content/${contentId}/read`);
        await delay(1800);
        opened = true;
      }
    } catch {}
    await snap(pg, 'web/web_student_pdf_player.png', 'h1,[class*="pdf"],canvas,iframe', opened ? 600 : 200);

    await navTo(pg, '/student/writing');
    await snap(pg, 'web/web_student_writing_workspace.png', 'h1,[class*="writing"]', 400);

    // PDF direct preview
    await navTo(pg, '/documents');
    await delay(600);
    try {
      const docId = await pg.evaluate(async () => {
        const r = await fetch('/api/v1/documents?limit=5', { credentials: 'include' });
        const j = await r.json();
        return j?.data?.[0]?.id || null;
      });
      if (docId) {
        await pg.evaluate(p => {
          window.history.pushState({}, '', p);
          window.dispatchEvent(new PopStateEvent('popstate', { state: {} }));
        }, `/documents/${docId}/preview`);
        await delay(1500);
      }
    } catch {}
    await snap(pg, 'web/web_pdf_direct_preview.png', 'h1,[class*="pdf"],canvas,iframe', 300);

    await c.close();
  }

  // ── DARK MODE ────────────────────────────────────────────────────────────────
  // Fresh context with OS dark preference; the app's useTheme() picks it up via
  // matchMedia when no stored preference exists → renders the dark theme.
  console.log('\n── DARK MODE ──');
  {
    const c = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      deviceScaleFactor: 1,
      colorScheme: 'dark',
    });
    await c.addInitScript(() => {
      try { localStorage.setItem('i18nextLng', 'fr'); } catch { /* ignore */ }
    });
    const pg = await loginAs(c, 'ADM');
    await snap(pg, 'web/web_dashboard_admin_dark.png', 'h1', 400);
    await c.close();
  }

  // ── ARABIC (RTL) ─────────────────────────────────────────────────────────────
  // Seed i18next's cached language to Arabic before load; applyDirection() flips
  // the document to dir="rtl". Demonstrates the trilingual + RTL support.
  console.log('\n── ARABIC (RTL) ──');
  {
    const c = await ctx(browser);
    await c.addInitScript(() => {
      try {
        localStorage.setItem('i18nextLng', 'ar');
      } catch {
        /* ignore */
      }
    });
    const pg = await c.newPage();
    await pg.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    await snap(pg, 'web/web_login_ar.png', 'form', 400);
    await c.close();
  }
  {
    const c = await ctx(browser);
    await c.addInitScript(() => {
      try {
        localStorage.setItem('i18nextLng', 'ar');
      } catch {
        /* ignore */
      }
    });
    const pg = await loginAs(c, 'STD');
    await navTo(pg, '/student/home');
    await snap(pg, 'web/web_student_home_ar.png', 'h1', 500);
    await c.close();
  }

  // ── Swagger UI ─────────────────────────────────────────────────────────────
  console.log('\n── TOOLS ──');
  {
    const c = await ctx(browser);
    const pg = await c.newPage();
    await pg.goto(`${API_URL}/docs`, { waitUntil: 'networkidle' });
    await pg.waitForSelector('.swagger-ui .info,.opblock-tag', { timeout: 15000 }).catch(() => {});
    await delay(1500);
    await snap(pg, 'tools/swagger_ui.png');
    await c.close();
  }

  await browser.close();
  console.log('\n✓ All captures done.\n');
}

main().catch(e => { console.error(e); process.exit(1); });
