#!/usr/bin/env node
/**
 * Drift guard: verifies the web SoT (`web/src/shared/taxonomy.ts`) matches the
 * backend-derived canonical set (`design-tokens/taxonomy.json`). Non-destructive
 * — it reports mismatches so a human decides (e.g. add a subject to the backend
 * enum vs. remove it from the client), rather than silently rewriting the file.
 *
 *   node scripts/check-taxonomy-sync.mjs   (wire into web-ci)
 *
 * Exit 1 on any level-band drift (hard: backend rejects unknown bands) or subject
 * drift (warn-level but still non-zero so CI surfaces it).
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..');
const tax = JSON.parse(readFileSync(resolve(repo, 'design-tokens/taxonomy.json'), 'utf8'));
const tsSrc = readFileSync(resolve(repo, 'web/src/shared/taxonomy.ts'), 'utf8');

// Extract a `export const NAME ... = [ '...', ... ]` string array from the TS file.
function tsArray(name) {
  const re = new RegExp(`export const ${name}[^=]*=\\s*\\[([\\s\\S]*?)\\]`, 'm');
  const m = tsSrc.match(re);
  if (!m) return null;
  return [...m[1].matchAll(/'([^']+)'/g)].map((x) => x[1]);
}

function diff(label, backend, web, hard) {
  if (!web) {
    console.error(`[taxonomy-sync] could not find ${label} in web/src/shared/taxonomy.ts`);
    return true;
  }
  const b = new Set(backend);
  const w = new Set(web);
  const missingInWeb = backend.filter((x) => !w.has(x));
  const extraInWeb = web.filter((x) => !b.has(x));
  if (missingInWeb.length === 0 && extraInWeb.length === 0) {
    console.log(`[taxonomy-sync] ${label}: OK (${backend.length} values).`);
    return false;
  }
  const tag = hard ? 'ERROR' : 'WARN';
  console.error(`[taxonomy-sync] ${tag} ${label} differs from backend:`);
  if (missingInWeb.length) console.error(`    missing in web: ${missingInWeb.join(', ')}`);
  if (extraInWeb.length)
    console.error(`    extra in web (backend would reject): ${extraInWeb.join(', ')}`);
  return true;
}

let failed = false;
failed = diff('LEVEL_BANDS', tax.levelBands, tsArray('LEVEL_BANDS'), true) || failed;
failed = diff('SUBJECTS', tax.subjects, tsArray('SUBJECTS'), false) || failed;

if (failed) {
  console.error('\n[taxonomy-sync] FAILED — reconcile web taxonomy.ts with the backend enums.');
  process.exit(1);
}
console.log('[taxonomy-sync] web taxonomy is in sync with the backend.');
