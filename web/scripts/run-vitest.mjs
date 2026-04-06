import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const vitestBin = require.resolve('vitest/vitest.mjs');
const child = spawn(process.execPath, [vitestBin, 'run', ...process.argv.slice(2)], {
  stdio: 'inherit',
  env: process.env,
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  const exitCode = code ?? 1;
  console.log(exitCode === 0 ? 'PASS vitest' : 'FAIL vitest');
  process.exit(exitCode);
});
