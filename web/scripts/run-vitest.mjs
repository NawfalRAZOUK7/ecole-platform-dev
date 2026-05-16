import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const vitestBin = require.resolve('vitest/vitest.mjs');

const env = { ...process.env };
if (!/(^|\s)--max-old-space-size=/.test(env.NODE_OPTIONS ?? '')) {
  env.NODE_OPTIONS = [env.NODE_OPTIONS, '--max-old-space-size=4096']
    .filter(Boolean)
    .join(' ');
}

const args = [vitestBin, 'run', ...process.argv.slice(2)];
if (env.CI && !args.some((arg) => arg === '--maxWorkers' || arg.startsWith('--maxWorkers='))) {
  args.push('--maxWorkers=2');
}
if (env.CI && !args.some((arg) => arg === '--minWorkers' || arg.startsWith('--minWorkers='))) {
  args.push('--minWorkers=1');
}

const child = spawn(process.execPath, args, {
  stdio: 'inherit',
  env,
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
