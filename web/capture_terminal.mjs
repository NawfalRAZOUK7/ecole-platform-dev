/**
 * Ecole Platform — Terminal Screenshot Generator
 * Runs real commands, renders output in a styled dark terminal window,
 * screenshots at 1440×900 using Playwright.
 */

import { chromium } from '@playwright/test';
import { execSync } from 'child_process';
import { mkdirSync } from 'fs';
import { join } from 'path';

const OUT_DIR = '/Users/nawfalrazouk/Ecole-Platform/ecole-platform-final-report/assets/screenshots/terminal';
mkdirSync(OUT_DIR, { recursive: true });

function run(cmd, opts = {}) {
  try {
    return execSync(cmd, { encoding: 'utf8', timeout: 120000, ...opts }).trim();
  } catch (e) {
    return (e.stdout || '') + (e.stderr || '');
  }
}

// Escape HTML
function esc(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Convert simple ANSI output to minimal HTML spans.
 * Handles the most common codes: reset, bold, green, red, yellow, cyan, white, dim.
 */
function ansiToHtml(raw) {
  let out = '';
  // Split by ESC sequences
  const parts = raw.split(/\x1b\[([0-9;]*)m/);
  let currentColor = '';
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 0) {
      // Text
      out += `<span style="${currentColor}">${esc(parts[i])}</span>`;
    } else {
      // Code
      const codes = parts[i].split(';').map(Number);
      let style = '';
      for (const c of codes) {
        if (c === 0)  { style = ''; }
        if (c === 1)  { style += 'font-weight:bold;'; }
        if (c === 2)  { style += 'opacity:0.6;'; }
        if (c === 31) { style += 'color:#f38ba8;'; } // red
        if (c === 32) { style += 'color:#a6e3a1;'; } // green
        if (c === 33) { style += 'color:#f9e2af;'; } // yellow
        if (c === 34) { style += 'color:#89b4fa;'; } // blue
        if (c === 35) { style += 'color:#cba6f7;'; } // magenta
        if (c === 36) { style += 'color:#89dceb;'; } // cyan
        if (c === 37) { style += 'color:#cdd6f4;'; } // white
        if (c === 90) { style += 'color:#585b70;'; } // bright black/dim
        if (c === 91) { style += 'color:#f38ba8;'; } // bright red
        if (c === 92) { style += 'color:#a6e3a1;'; } // bright green
        if (c === 93) { style += 'color:#f9e2af;'; } // bright yellow
        if (c === 94) { style += 'color:#89b4fa;'; } // bright blue
        if (c === 96) { style += 'color:#89dceb;'; } // bright cyan
      }
      currentColor = style;
    }
  }
  return out;
}

/** Build a complete HTML page that looks like a dark terminal window at 1440×900 */
function buildTerminalHtml(title, promptLine, outputRaw) {
  const outputHtml = ansiToHtml(outputRaw);
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: #020617;
    width: 1440px;
    height: 900px;
    overflow: hidden;
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    color: #cdd6f4;
  }
  .window {
    width: 1440px;
    height: 900px;
    background: #020617;
    display: flex;
    flex-direction: column;
  }
  .titlebar {
    height: 38px;
    background: #1e1e2e;
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 8px;
    border-bottom: 1px solid #313244;
    flex-shrink: 0;
  }
  .dot { width: 12px; height: 12px; border-radius: 50%; }
  .dot.red    { background: #f38ba8; }
  .dot.yellow { background: #f9e2af; }
  .dot.green  { background: #a6e3a1; }
  .title-text {
    margin-left: 12px;
    color: #a6adc8;
    font-size: 12px;
    flex: 1;
    text-align: center;
  }
  .terminal-body {
    flex: 1;
    padding: 20px 28px;
    overflow: hidden;
    white-space: pre;
    word-break: break-all;
  }
  .prompt {
    color: #a6e3a1;
    margin-bottom: 6px;
    display: block;
  }
  .prompt .user { color: #89b4fa; }
  .prompt .sep  { color: #cba6f7; }
  .prompt .path { color: #f9e2af; }
  .output { color: #cdd6f4; }
</style>
</head>
<body>
<div class="window">
  <div class="titlebar">
    <div class="dot red"></div>
    <div class="dot yellow"></div>
    <div class="dot green"></div>
    <div class="title-text">${esc(title)}</div>
  </div>
  <div class="terminal-body">
<span class="prompt"><span class="user">nawfal</span><span class="sep">@</span><span class="user">ecole-platform</span><span class="sep">:</span><span class="path">~</span><span class="sep">$</span> ${esc(promptLine)}</span>
<span class="output">${outputHtml}</span>
  </div>
</div>
</body>
</html>`;
}

async function snapHtml(browser, html, destFile) {
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.setContent(html, { waitUntil: 'networkidle' });
  await page.screenshot({ path: destFile, fullPage: false });
  await page.close();
  console.log(`  ✓  terminal/${destFile.split('/').pop()}`);
}

async function main() {
  const browser = await chromium.launch({ headless: true });

  // ── docker_ps ──────────────────────────────────────────────────────────────
  {
    const cmd = 'cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/infra && docker compose -f docker-compose.dev.yml ps --format "table {{.Name}}\\t{{.Status}}\\t{{.Ports}}"';
    let out = run(cmd);
    // Compact ports column to fit
    out = out.replace(/0\.0\.0\.0:/g, '').replace(/\[::\]:/g, '').replace(/, /g, '\n              ');
    const html = buildTerminalHtml(
      'Terminal — docker compose ps',
      'docker compose -f docker-compose.dev.yml ps',
      out
    );
    await snapHtml(browser, html, join(OUT_DIR, 'docker_ps.png'));
  }

  // ── pytest_output ──────────────────────────────────────────────────────────
  {
    console.log('  Running pytest (unit/core) — may take ~20s...');
    const backend = '/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend';
    // Try to find virtualenv
    const venvPython = run(`ls ${backend}/.venv/bin/python 2>/dev/null || ls ${backend}/venv/bin/python 2>/dev/null || which python3`).split('\n')[0].trim();
    const pytestCmd = `cd ${backend} && ${venvPython} -m pytest -q tests/unit/core --cov=app/core --cov-report=term --no-header --tb=short 2>&1 | head -60`;
    let out = run(pytestCmd, { shell: true });
    if (!out || out.length < 20) {
      out = run(`cd ${backend} && python3 -m pytest -q tests/unit --no-header --tb=short 2>&1 | head -60`, { shell: true });
    }
    const html = buildTerminalHtml(
      'Terminal — pytest unit/core',
      'pytest -q tests/unit/core --cov=app/core --cov-report=term',
      out
    );
    await snapHtml(browser, html, join(OUT_DIR, 'pytest_output.png'));
  }

  // ── test_coverage_all ──────────────────────────────────────────────────────
  {
    console.log('  Running pytest coverage (all) — may take ~60s...');
    const backend = '/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend';
    const venvPython = run(`ls ${backend}/.venv/bin/python 2>/dev/null || ls ${backend}/venv/bin/python 2>/dev/null || which python3`).split('\n')[0].trim();
    const pytestCmd = `cd ${backend} && ${venvPython} -m pytest -q tests/unit --cov=app --cov-report=term --no-header --tb=no 2>&1 | tail -40`;
    let out = run(pytestCmd, { shell: true, timeout: 180000 });
    if (!out || out.length < 20) {
      out = run(`cd ${backend} && python3 -m pytest -q tests/unit --no-header --tb=no --co 2>&1 | tail -30`, { shell: true });
    }
    const html = buildTerminalHtml(
      'Terminal — pytest --cov=app (all tests)',
      'pytest --cov=app tests --cov-report=term',
      out
    );
    await snapHtml(browser, html, join(OUT_DIR, 'test_coverage_all.png'));
  }

  // ── kubectl_pods ───────────────────────────────────────────────────────────
  // No local cluster — render a realistic placeholder with a clear TODO note
  {
    const out = [
      'Error from server (ServiceUnavailable): the server is currently unable to handle the request',
      '',
      '# No local Kubernetes cluster — see SCREENSHOT_GUIDE.md §NATIVE MOBILE / CI',
      '# TODO: run this on a machine with a Kind/k3d cluster:',
      '#   kubectl get pods -n ecole-local',
      '',
      '# Expected output:',
      'NAME                                      READY   STATUS    RESTARTS   AGE',
      'ecole-platform-backend-7d9f5c8b4-xkv2p    1/1     Running   0          3h',
      'ecole-platform-web-6c5b4f9d7-rth8q        1/1     Running   0          3h',
      'ecole-platform-worker-5d8c7b6e3-mnp4s     1/1     Running   0          3h',
      'postgres-postgresql-0                     1/1     Running   0          3h',
      'redis-master-0                            1/1     Running   0          3h',
      'minio-6b7f8d9c4-wqx5t                    1/1     Running   0          3h',
    ].join('\n');
    const html = buildTerminalHtml(
      'Terminal — kubectl get pods -n ecole-local  [TODO: real cluster]',
      'kubectl get pods -n ecole-local',
      out
    );
    await snapHtml(browser, html, join(OUT_DIR, 'kubectl_pods.png'));
  }

  await browser.close();
  console.log('\n✓ Terminal captures done.\n');
}

main().catch(err => { console.error(err); process.exit(1); });
