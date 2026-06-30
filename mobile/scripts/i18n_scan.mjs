#!/usr/bin/env node
/**
 * Mobile i18n scanner / CI guard.
 *
 * Mirrors `web/scripts/i18n-check.mjs` for the Flutter app: finds hardcoded UI
 * string literals that should be externalized to `lib/l10n/app_localizations.dart`
 * via `AppLocalizations.of(ref)` → `t('some.key')`.
 *
 * Usage:
 *   node scripts/i18n_scan.mjs            # report all hardcoded strings (informational)
 *   node scripts/i18n_scan.mjs --enforce  # exit 1 if any are found in ENFORCED_DIRS
 *   node scripts/i18n_scan.mjs --json     # machine-readable output
 *
 * The --enforce list starts on the priority screens so the team can ratchet the
 * guard tighter (add dirs to ENFORCED_DIRS) as each area is localized, without
 * blocking on the whole app at once.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const ROOT = new URL('..', import.meta.url).pathname;
const LIB = join(ROOT, 'lib');

// Priority areas (PRODUCT_QUALITY_PASS.md §7/§3 + CODEX_RUN_PROMPT.md §3).
const ENFORCED_DIRS = [
  'lib/features/academic/timetable',
  'lib/features/billing',
  'lib/features/school/micro_schools',
  'lib/features/lms/question_bank',
  'lib/features/lms/rubrics',
  'lib/features/ai/games',
  'lib/features/user/profile',
  'lib/features/auth',
];

// Widget constructors / named args that take user-facing copy.
const PATTERNS = [
  /\bText\(\s*'([^']{2,})'/g,
  /\bText\(\s*"([^"]{2,})"/g,
  /\b(?:labelText|hintText|helperText|errorText|tooltip|message|semanticLabel|title|subtitle|label):\s*'([^']{2,})'/g,
  /\bSnackBar\([^)]*content:\s*Text\(\s*'([^']{2,})'/g,
];

// Skip strings that are clearly NOT user copy.
function isProbablyCopy(s) {
  if (!/[A-Za-zÀ-ſ؀-ۿ]/.test(s)) return false; // needs a letter (latin or arabic)
  if (s.startsWith('/')) return false;          // routes
  if (s.startsWith('assets/')) return false;    // asset paths
  if (/^[a-z]+([._][a-z0-9]+)+$/i.test(s)) return false; // looks like an i18n key already (a.b.c)
  if (/^https?:\/\//.test(s)) return false;     // urls
  if (/^[#@\$].*/.test(s)) return false;        // ids / mentions
  if (/^[A-Z0-9_]{2,}$/.test(s)) return false;  // CONSTANT_CASE codes
  if (!/\s/.test(s) && s.length < 3) return false; // tiny tokens
  return true;
}

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) walk(p, acc);
    else if (name.endsWith('.dart') && !name.endsWith('.g.dart')) acc.push(p);
  }
  return acc;
}

const files = walk(LIB);
const findings = [];
for (const file of files) {
  const rel = relative(ROOT, file);
  const src = readFileSync(file, 'utf8');
  const lines = src.split('\n');
  for (const re of PATTERNS) {
    re.lastIndex = 0;
    let m;
    while ((m = re.exec(src)) !== null) {
      const text = m[1];
      if (!isProbablyCopy(text)) continue;
      const lineNo = src.slice(0, m.index).split('\n').length;
      findings.push({ file: rel, line: lineNo, text, raw: lines[lineNo - 1]?.trim() });
    }
  }
}

const enforced = findings.filter((f) =>
  ENFORCED_DIRS.some((d) => f.file.startsWith(d)),
);

if (process.argv.includes('--json')) {
  console.log(JSON.stringify({ total: findings.length, enforced: enforced.length, findings }, null, 2));
} else {
  const byFile = {};
  for (const f of findings) (byFile[f.file] ??= []).push(f);
  const fileNames = Object.keys(byFile).sort();
  for (const fn of fileNames) {
    const enf = ENFORCED_DIRS.some((d) => fn.startsWith(d)) ? ' [ENFORCED]' : '';
    console.log(`\n${fn}${enf}  (${byFile[fn].length})`);
    for (const f of byFile[fn]) console.log(`  L${f.line}: ${JSON.stringify(f.text)}`);
  }
  console.log(`\n— hardcoded UI strings: ${findings.length} total, ${enforced.length} in enforced dirs`);
}

if (process.argv.includes('--enforce') && enforced.length > 0) {
  console.error(
    `\n✖ i18n guard: ${enforced.length} hardcoded string(s) remain in enforced dirs.\n` +
      `  Externalize them to lib/l10n/app_localizations.dart (fr/ar/en) and use t('key').`,
  );
  process.exit(1);
}
