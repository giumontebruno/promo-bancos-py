import { execFileSync } from 'node:child_process';
import { appendFileSync } from 'node:fs';

// Never rebase an already-generated data snapshot onto newer code or data.
// Even a data-only advance is conservatively deferred to the next refresh.
const git = (...args) => execFileSync('git', args, { encoding: 'utf8', timeout: 30000 }).trim();
let current = false;
try {
  const checkout = git('rev-parse', 'HEAD');
  git('fetch', '--no-tags', 'origin', 'refs/heads/main');
  const latest = git('rev-parse', 'FETCH_HEAD');
  current = checkout === latest;
  const message = current
    ? `Refresh revision guard passed: ${checkout}.`
    : `Data commit blocked: main advanced from ${checkout} to ${latest}. Keep the newer snapshot; the next refresh must start from updated main.`;
  console.log(message);
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, `\n### Refresh revision guard\n${message}\n`);
} catch (error) {
  console.error(`Data commit blocked: cannot verify current main revision (${error.message}).`);
} finally {
  if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, `current=${current}\n`);
}
if (!current) process.exitCode = 1;
