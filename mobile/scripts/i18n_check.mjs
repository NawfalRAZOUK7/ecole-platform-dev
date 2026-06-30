#!/usr/bin/env node
/**
 * Mobile i18n guard: fails (exit 1) if the `fr`, `ar`, `en` sub-maps of
 * `lib/l10n/app_localizations.dart` don't have exactly the same key set.
 * Mirrors the web guard (`web/scripts/i18n-check.mjs`). Run in CI / pre-commit:
 *   node mobile/scripts/i18n_check.mjs
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const file = resolve(here, '../lib/l10n/app_localizations.dart');
const src = readFileSync(file, 'utf8');
const lines = src.split('\n');

const LOCALES = ['fr', 'ar', 'en'];
const keys = { fr: new Set(), ar: new Set(), en: new Set() };
let current = null;

const localeOpen = /^\s{2}'(fr|ar|en)':\s*\{/;
const keyLine = /^\s{4}'([^']+)'\s*:/;
const localeClose = /^\s{2}\},?\s*$/;

for (const line of lines) {
  const lo = line.match(localeOpen);
  if (lo) { current = lo[1]; continue; }
  if (current && localeClose.test(line)) { current = null; continue; }
  if (current) {
    const km = line.match(keyLine);
    if (km) keys[current].add(km[1]);
  }
}

const ref = keys.fr;
let failed = false;
for (const loc of ['ar', 'en']) {
  const missing = [...ref].filter((k) => !keys[loc].has(k)).sort();
  const extra = [...keys[loc]].filter((k) => !ref.has(k)).sort();
  if (missing.length || extra.length) {
    failed = true;
    console.error(`\n[mobile-i18n] ${loc} out of sync with fr:`);
    if (missing.length) console.error(`  Missing (${missing.length}): ${missing.slice(0, 25).join(', ')}${missing.length > 25 ? ' …' : ''}`);
    if (extra.length) console.error(`  Extra (${extra.length}): ${extra.slice(0, 25).join(', ')}${extra.length > 25 ? ' …' : ''}`);
  } else {
    console.log(`[mobile-i18n] ${loc}: OK (${keys[loc].size} keys).`);
  }
}
console.log(`[mobile-i18n] fr: ${keys.fr.size} keys.`);

if (failed) {
  console.error('\n[mobile-i18n] FAILED: fr/ar/en key sets must match.');
  process.exit(1);
}
console.log('[mobile-i18n] All locales aligned with fr.');
