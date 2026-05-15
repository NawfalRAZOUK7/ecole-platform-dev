#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

function readArg(name) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

function toPascalCase(value) {
  return value
    .split(/[-_/]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');
}

function toCamelCase(value) {
  const pascal = toPascalCase(value);
  return pascal.charAt(0).toLowerCase() + pascal.slice(1);
}

function writeIfMissing(filePath, content) {
  if (fs.existsSync(filePath)) {
    console.log(`exists ${path.relative(process.cwd(), filePath)}`);
    return;
  }

  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content);
  console.log(`created ${path.relative(process.cwd(), filePath)}`);
}

const layer = readArg('layer');
const name = readArg('name');

if (!layer || !name) {
  console.error('Usage: npm run create:module -- --layer features --name create-invoice');
  process.exit(1);
}

const allowedLayers = new Set(['features', 'entities', 'widgets', 'pages']);
if (!allowedLayers.has(layer)) {
  console.error(`Unsupported layer "${layer}". Expected one of: ${Array.from(allowedLayers).join(', ')}`);
  process.exit(1);
}

const modulePath = path.join(process.cwd(), 'src', layer, name);
const pascal = toPascalCase(name);
const camel = toCamelCase(name);

if (layer === 'features') {
  writeIfMissing(
    path.join(modulePath, 'api', `${name}.api.ts`),
    `export const ${camel}Api = {};\n`,
  );
  writeIfMissing(
    path.join(modulePath, 'model', `use${pascal}.ts`),
    `export function use${pascal}() {\n  return null;\n}\n`,
  );
  writeIfMissing(
    path.join(modulePath, 'ui', `${pascal}.tsx`),
    `export function ${pascal}() {\n  return null;\n}\n`,
  );
  writeIfMissing(
    path.join(modulePath, 'index.ts'),
    `export * from './api/${name}.api';\nexport * from './model/use${pascal}';\nexport * from './ui/${pascal}';\n`,
  );
} else if (layer === 'entities') {
  writeIfMissing(
    path.join(modulePath, 'model', 'types.ts'),
    `export interface ${pascal} {\n  id: string;\n}\n`,
  );
  writeIfMissing(
    path.join(modulePath, 'api', `${name}.api.ts`),
    `export const ${camel}Api = {};\n`,
  );
  writeIfMissing(
    path.join(modulePath, 'index.ts'),
    `export * from './api/${name}.api';\nexport * from './model/types';\n`,
  );
} else if (layer === 'widgets') {
  writeIfMissing(
    path.join(modulePath, 'ui', `${pascal}.tsx`),
    `export function ${pascal}() {\n  return null;\n}\n`,
  );
  writeIfMissing(path.join(modulePath, 'index.ts'), `export * from './ui/${pascal}';\n`);
} else {
  writeIfMissing(
    path.join(modulePath, 'ui', `${pascal}Page.tsx`),
    `export function ${pascal}Page() {\n  return null;\n}\n`,
  );
  writeIfMissing(path.join(modulePath, 'index.ts'), `export * from './ui/${pascal}Page';\n`);
}
