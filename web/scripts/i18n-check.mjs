#!/usr/bin/env node
/**
 * Garde i18n : échoue (exit 1) si `en` ou `ar` n'ont pas exactement les mêmes
 * clés que `fr` (référence). Empêche le retour des langues incomplètes
 * (fallback français qui « fuit » dans une UI EN/AR).
 *
 * Usage : node scripts/i18n-check.mjs   (à brancher en CI et pre-commit)
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const localesDir = resolve(here, '../src/shared/i18n/locales');
const REFERENCE = 'fr';
const TARGETS = ['en', 'ar'];

function load(lang) {
  return JSON.parse(readFileSync(resolve(localesDir, `${lang}.json`), 'utf8'));
}

function flatten(obj, prefix = '', out = new Set()) {
  for (const [key, value] of Object.entries(obj)) {
    const full = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      flatten(value, full, out);
    } else {
      out.add(full);
    }
  }
  return out;
}

const refKeys = flatten(load(REFERENCE));
let failed = false;

// Suffixes de catégories de pluriel ICU valides (l'arabe en a plus que le français) :
// on ne signale donc PAS comme « en trop » une variante plurielle d'une clé de base connue.
const PLURAL_SUFFIXES = ['_zero', '_one', '_two', '_few', '_many', '_other'];
function isLegitPluralExtra(key) {
  for (const suffix of PLURAL_SUFFIXES) {
    if (key.endsWith(suffix)) {
      const base = key.slice(0, -suffix.length);
      // accepté si la clé de base (ou une autre variante plurielle) existe côté fr
      if (refKeys.has(base) || PLURAL_SUFFIXES.some((s) => refKeys.has(base + s))) {
        return true;
      }
    }
  }
  return false;
}

for (const lang of TARGETS) {
  const keys = flatten(load(lang));
  const missing = [...refKeys].filter((k) => !keys.has(k)).sort();
  const extra = [...keys]
    .filter((k) => !refKeys.has(k) && !isLegitPluralExtra(k))
    .sort();
  if (missing.length || extra.length) {
    failed = true;
    console.error(`\n[i18n] ${lang}.json incohérent avec ${REFERENCE}.json :`);
    if (missing.length) {
      console.error(`  Manquantes (${missing.length}) : ${missing.slice(0, 25).join(', ')}${missing.length > 25 ? ' …' : ''}`);
    }
    if (extra.length) {
      console.error(`  En trop (${extra.length}) : ${extra.slice(0, 25).join(', ')}${extra.length > 25 ? ' …' : ''}`);
    }
  } else {
    console.log(`[i18n] ${lang}.json : OK (${keys.size} clés).`);
  }
}

if (failed) {
  console.error('\n[i18n] Échec : complétez les clés manquantes avant de merger.');
  process.exit(1);
}
console.log('[i18n] Toutes les langues sont alignées sur le français.');
