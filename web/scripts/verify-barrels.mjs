#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const strict = process.argv.includes('--strict');
const root = process.cwd();
const srcRoot = path.join(root, 'src');
const layerNames = ['features', 'entities', 'widgets', 'pages'];
const internalFolderNames = new Set(['api', 'model', 'ui', 'lib', 'types']);

function isDirectory(targetPath) {
  return fs.existsSync(targetPath) && fs.statSync(targetPath).isDirectory();
}

function hasIndex(targetPath) {
  return fs.existsSync(path.join(targetPath, 'index.ts'));
}

function readDirs(targetPath) {
  if (!isDirectory(targetPath)) return [];

  return fs
    .readdirSync(targetPath, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith('.'))
    .map((entry) => path.join(targetPath, entry.name));
}

function isModuleFolder(targetPath) {
  const children = readDirs(targetPath).map((dir) => path.basename(dir));
  return children.some((name) => internalFolderNames.has(name));
}

function collectModuleFolders(layerPath) {
  const modules = [];
  const topLevel = readDirs(layerPath);

  for (const dir of topLevel) {
    modules.push(dir);

    for (const child of readDirs(dir)) {
      if (!internalFolderNames.has(path.basename(child)) && isModuleFolder(child)) {
        modules.push(child);
      }
    }
  }

  return modules;
}

const missing = [];

for (const layerName of layerNames) {
  const layerPath = path.join(srcRoot, layerName);
  for (const modulePath of collectModuleFolders(layerPath)) {
    if (!hasIndex(modulePath)) {
      missing.push(path.relative(root, modulePath));
    }
  }
}

if (missing.length > 0) {
  console.error('Missing index.ts barrels:');
  for (const modulePath of missing) {
    console.error(`- ${modulePath}/index.ts`);
  }

  if (strict) {
    process.exit(1);
  }
} else {
  console.log('All checked modules have index.ts barrels.');
}
