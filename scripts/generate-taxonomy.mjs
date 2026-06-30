#!/usr/bin/env node
/**
 * Single-source-of-truth generator for curriculum vocabulary.
 *
 * Source of truth: `design-tokens/taxonomy.json`, dumped from the backend enums
 * (`backend/app/models/taxonomy.py` + `curriculum.py`). This emits a typed
 * constants file for **mobile** (Dart) so the Flutter app stops using free-text
 * subjects/levels and can't drift from the backend. The web SoT
 * (`web/src/shared/taxonomy.ts`) is checked, not overwritten, by
 * `scripts/check-taxonomy-sync.mjs` (it carries editorial choices like the
 * QUIZ_SUBJECTS subset and FR display labels).
 *
 * Regenerate after changing the backend enums:
 *   (dump taxonomy.json from the backend) && node scripts/generate-taxonomy.mjs
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..');
const tax = JSON.parse(readFileSync(resolve(repo, 'design-tokens/taxonomy.json'), 'utf8'));

const dartList = (arr) => `[\n    ${arr.map((s) => `'${s}'`).join(',\n    ')},\n  ]`;
const dartTitles = (obj) =>
  '{\n' +
  Object.entries(obj)
    .map(
      ([code, t]) =>
        `    '${code}': {${['fr', 'ar', 'en']
          .filter((l) => t[l] != null)
          .map((l) => `'${l}': '${String(t[l]).replace(/'/g, "\\'")}'`)
          .join(', ')}},`,
    )
    .join('\n') +
  '\n  }';
const dartCycleSubjects = (obj) =>
  '{\n' +
  Object.entries(obj)
    .map(([cycle, subs]) => `    '${cycle}': [${subs.map((s) => `'${s}'`).join(', ')}],`)
    .join('\n') +
  '\n  }';

const dart = `// GENERATED FILE — DO NOT EDIT BY HAND.
// Source of truth: design-tokens/taxonomy.json (dumped from the backend enums).
// Regenerate: node scripts/generate-taxonomy.mjs
//
// Mirrors backend/app/models/taxonomy.py so every level/subject input in the
// mobile app draws from the same set the backend accepts.

/// Curriculum vocabulary, generated from the backend taxonomy.
class Taxonomy {
  Taxonomy._();

  static const String subjectOther = 'other';

  static const List<String> schoolCycles = ${dartList(tax.schoolCycles)};

  static const List<String> microSchoolTypes = ${dartList(tax.microSchoolTypes)};

  static const List<String> levelBands = ${dartList(tax.levelBands)};

  static const List<String> subjects = ${dartList(tax.subjects)};

  static const List<String> difficultyLevels = ${dartList(tax.difficultyLevels)};

  static const List<String> languages = ${dartList(tax.languages)};

  static const List<String> currencies = ${dartList(tax.currencies)};

  /// Subject code -> {fr, ar, en} display titles.
  static const Map<String, Map<String, String>> subjectTitles = ${dartTitles(tax.subjectTitles)};

  /// School cycle -> allowed subject codes.
  static const Map<String, List<String>> cycleSubjects = ${dartCycleSubjects(tax.cycleSubjects)};
}
`;

const outDir = resolve(repo, 'mobile/lib/shared/taxonomy');
mkdirSync(outDir, { recursive: true });
const outFile = resolve(outDir, 'taxonomy.g.dart');
writeFileSync(outFile, dart, 'utf8');
console.log(
  `[taxonomy] generated ${outFile.replace(repo + '/', '')} ` +
    `(${tax.subjects.length} subjects, ${tax.levelBands.length} level bands, ` +
    `${Object.keys(tax.subjectTitles).length} titles)`,
);
