/**
 * Ecole Platform — Screenshot Capture Script
 * Captures all web_* screenshots + swagger_ui via Playwright headless Chromium.
 * Run from: /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/web
 *   node /tmp/capture_screenshots.mjs
 */

import { chromium } from '@playwright/test';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const BASE_URL   = 'http://localhost:5173';
const API_URL    = 'http://localhost:8000';
const SCHOOL_ID  = '00000000-0000-4000-8000-000000000001';
const OUT_DIR    = '/Users/nawfalrazouk/Ecole-Platform/ecole-platform-final-report/assets/screenshots';

// Credentials
const CREDS = {
  ADM: { email: 'admin@ecole-benani.ma',       password: 'admin123'      },
  TCH: { email: 'prof.math@ecole-benani.ma',   password: 'teacher123'    },
  STD: { email: 'yassine.alaoui@ecole-benani.ma', password: 'student123' },
  PAR: { email: 'parent.alaoui@gmail.com',     password: 'parent123'     },
  SUP: { email: 'superadmin@ecole-platform.ma', password: 'superadmin123' },
  CMS: { email: 'cms@ecole-platform.ma',        password: 'content123'   },
};

async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

/** Log in via the form and wait for redirect away from /login */
async function loginAs(page, role) {
  const { email, password } = CREDS[role];
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
  await page.fill('input[type="email"], input[name="email"]', email);
  await page.fill('input[type="password"], input[name="password"]', password);
  // School ID field may be hidden (defaults to seed school). Fill if visible.
  const schoolInput = page.locator('input[name="school_id"], input[placeholder*="school"], input[id*="school"]');
  if (await schoolInput.count() > 0) {
    const visible = await schoolInput.first().isVisible();
    if (visible) await schoolInput.first().fill(SCHOOL_ID);
  }
  await page.click('button[type="submit"]');
  // Wait until redirected away from login
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 }).catch(() => {});
  await delay(1500);
}

/** Take full-viewport screenshot at 1440×900 */
async function snap(page, destPath, waitFor) {
  if (waitFor) {
    await page.waitForSelector(waitFor, { timeout: 8000 }).catch(() => {});
  }
  await delay(800);
  mkdirSync(join(OUT_DIR, destPath.split('/')[0]), { recursive: true });
  await page.screenshot({ path: join(OUT_DIR, destPath), fullPage: false });
  console.log(`  ✓  ${destPath}`);
}

async function main() {
  const browser = await chromium.launch({ headless: true });

  const ctx = (extra = {}) => browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
    ...extra,
  });

  // ───────────────────────────────────────────
  // PUBLIC ROUTES (no login)
  // ───────────────────────────────────────────
  console.log('\n── PUBLIC ──');
  {
    const context = await ctx();
    const page = await context.newPage();

    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_auth_login.png', 'form');

    await page.goto(`${BASE_URL}/apply`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_apply_onboarding.png', 'form, main, [class*="apply"]');

    await page.goto(`${BASE_URL}/activate`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_activate_account.png', 'form, main, [class*="activate"]');

    await context.close();
  }

  // ───────────────────────────────────────────
  // ADM — Admin
  // ───────────────────────────────────────────
  console.log('\n── ADM ──');
  {
    const context = await ctx();
    const page = await context.newPage();
    await loginAs(page, 'ADM');

    // Dashboard
    await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_dashboard_admin.png', '[class*="card"], [class*="dashboard"], h1');

    // Finance — invoices
    await page.goto(`${BASE_URL}/invoices`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_finance_invoice.png', 'table, [class*="invoice"], h1');

    // Messages
    await page.goto(`${BASE_URL}/messages`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_messages_conversations.png', '[class*="conversation"], [class*="message"], h1');

    // Announcements
    await page.goto(`${BASE_URL}/announcements`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_announcements.png', 'table, [class*="announce"], h1');

    await context.close();
  }

  // ───────────────────────────────────────────
  // SUP — Platform console
  // ───────────────────────────────────────────
  console.log('\n── SUP ──');
  {
    const context = await ctx();
    const page = await context.newPage();
    await loginAs(page, 'SUP');

    await page.goto(`${BASE_URL}/platform`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_platform_sup_console.png', 'table, [class*="platform"], h1');

    await context.close();
  }

  // ───────────────────────────────────────────
  // TCH — Teacher
  // ───────────────────────────────────────────
  console.log('\n── TCH ──');
  {
    const context = await ctx();
    const page = await context.newPage();
    await loginAs(page, 'TCH');

    // ERP classes (teacher classes page)
    await page.goto(`${BASE_URL}/teacher`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_erp_classes.png', 'table, [class*="class"], h1');

    // LMS courses
    await page.goto(`${BASE_URL}/teacher/courses`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_lms_courses.png', 'table, [class*="course"], h1');

    // Content library
    await page.goto(`${BASE_URL}/teacher/content-library`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_teacher_content_library.png', '[class*="library"], [class*="content"], h1');

    // Content upload (open new/upload dialog)
    await page.goto(`${BASE_URL}/teacher/content-library`, { waitUntil: 'networkidle' });
    await delay(800);
    // Try to click Upload button
    const uploadBtn = page.locator('button').filter({ hasText: /upload|téléverser|ajouter|nouveau|new/i }).first();
    if (await uploadBtn.count() > 0 && await uploadBtn.isVisible()) {
      await uploadBtn.click();
      await delay(800);
    }
    await snap(page, 'web/web_teacher_content_upload.png', '[class*="modal"], [class*="dialog"], [class*="upload"], h1');

    // Quizzes
    await page.goto(`${BASE_URL}/teacher/quizzes`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_teacher_quizzes.png', 'table, [class*="quiz"], h1');

    // Teacher submissions
    await page.goto(`${BASE_URL}/teacher/submissions`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_teacher_submissions.png', 'table, [class*="submission"], h1');

    // Content submissions (teacher review queue) — try CMS review or content submissions
    await page.goto(`${BASE_URL}/teacher/submissions`, { waitUntil: 'networkidle' });
    // Navigate to a submissions list that shows content/assignment submissions
    await snap(page, 'web/web_teacher_content_submissions.png', 'table, [class*="submission"], h1');

    // Generate quiz dialog
    await page.goto(`${BASE_URL}/question-bank/generate`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_generate_quiz_dialog.png', 'form, [class*="generate"], [class*="quiz"], h1');

    await context.close();
  }

  // ───────────────────────────────────────────
  // STD — Student
  // ───────────────────────────────────────────
  console.log('\n── STD ──');
  {
    const context = await ctx();
    const page = await context.newPage();
    await loginAs(page, 'STD');

    // Student home / rewards
    await page.goto(`${BASE_URL}/student/home`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_student_home_rewards.png', '[class*="reward"], [class*="badge"], [class*="home"], h1');

    // Student content library
    await page.goto(`${BASE_URL}/student/content`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_student_content_library.png', '[class*="content"], [class*="library"], h1');

    // PDF player — find a PDF item and open it
    await page.goto(`${BASE_URL}/student/content`, { waitUntil: 'networkidle' });
    await delay(1000);
    // Try to click the first PDF item
    const pdfItem = page.locator('[class*="content-item"], [class*="card"], li, article').filter({ hasText: /pdf|cours|lesson/i }).first();
    if (await pdfItem.count() > 0) {
      await pdfItem.click();
      await delay(1500);
      // Look for read/open button
      const readBtn = page.locator('button, a').filter({ hasText: /lire|read|ouvrir|open|voir|view/i }).first();
      if (await readBtn.count() > 0) await readBtn.click();
      await delay(1500);
    }
    await snap(page, 'web/web_student_pdf_player.png', '[class*="pdf"], [class*="viewer"], [class*="player"], canvas, iframe');

    // Fallback: navigate directly to documents preview if no content found
    const currentUrl = page.url();
    if (currentUrl.includes('/student/content') && !currentUrl.includes('/read')) {
      // Try documents/:id/preview route
      await page.goto(`${BASE_URL}/documents`, { waitUntil: 'networkidle' });
      await delay(800);
      const docLink = page.locator('a, button').filter({ hasText: /pdf|voir|preview/i }).first();
      if (await docLink.count() > 0) await docLink.click();
      await delay(1000);
      await snap(page, 'web/web_pdf_direct_preview.png', '[class*="pdf"], [class*="viewer"], canvas, iframe');
    }

    // Writing workspace
    await page.goto(`${BASE_URL}/student/writing`, { waitUntil: 'networkidle' });
    await snap(page, 'web/web_student_writing_workspace.png', '[class*="writing"], [class*="editor"], [class*="workspace"], h1');

    await context.close();
  }

  // ───────────────────────────────────────────
  // PDF direct preview (as ADM from documents)
  // ───────────────────────────────────────────
  console.log('\n── PDF preview ──');
  {
    const context = await ctx();
    const page = await context.newPage();
    await loginAs(page, 'ADM');

    await page.goto(`${BASE_URL}/documents`, { waitUntil: 'networkidle' });
    await delay(800);
    const docLink = page.locator('a[href*="/preview"], button').filter({ hasText: /pdf|voir|aperçu|preview/i }).first();
    if (await docLink.count() > 0) {
      await docLink.click();
      await delay(1200);
    }
    await snap(page, 'web/web_pdf_direct_preview.png', '[class*="pdf"], [class*="preview"], canvas, iframe, h1');

    await context.close();
  }

  // ───────────────────────────────────────────
  // Swagger UI
  // ───────────────────────────────────────────
  console.log('\n── TOOLS ──');
  {
    const context = await ctx();
    const page = await context.newPage();
    await page.goto(`${API_URL}/docs`, { waitUntil: 'networkidle' });
    // Wait for Swagger to finish rendering
    await page.waitForSelector('.swagger-ui .info, .opblock-tag', { timeout: 15000 }).catch(() => {});
    await delay(1500);
    await snap(page, 'tools/swagger_ui.png');
    await context.close();
  }

  await browser.close();
  console.log('\n✓ All captures done.\n');
}

main().catch(err => { console.error(err); process.exit(1); });
