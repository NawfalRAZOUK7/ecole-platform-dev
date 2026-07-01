import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const vitestBin = join(dirname(require.resolve('vitest/package.json')), 'vitest.mjs');

const env = { ...process.env };
if (!/(^|\s)--max-old-space-size=/.test(env.NODE_OPTIONS ?? '')) {
  env.NODE_OPTIONS = [env.NODE_OPTIONS, '--max-old-space-size=4096']
    .filter(Boolean)
    .join(' ');
}

const cliArgs = process.argv.slice(2).filter((arg) => {
  // Vitest 4 removed --minWorkers; older workflow shards still pass it.
  return arg !== '--minWorkers' && !arg.startsWith('--minWorkers=');
});

const args = [vitestBin, 'run', ...cliArgs];
if (
  !args.some((arg) => arg === '--fileParallelism' || arg.startsWith('--fileParallelism='))
) {
  args.push('--fileParallelism=false');
}
if (env.CI && !args.some((arg) => arg === '--maxWorkers' || arg.startsWith('--maxWorkers='))) {
  args.push('--maxWorkers=2');
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
