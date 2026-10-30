const { test } = require('node:test');
const assert = require('node:assert/strict');
const modulePromise = import('../scripts/maintenance-health.mjs');
async function fixture() {
  const { EXPECTED_SOURCES, assessHealth } = await modulePromise;
  const now = new Date('2026-10-30T15:00:00Z');
  const promotions = EXPECTED_SOURCES.flatMap(bank => Array.from({length: 4}, (_, i) => ({id: `${bank}-${i}`, bank})));
  const sources = Object.fromEntries(EXPECTED_SOURCES.map(bank => [bank, {status: 'fetched', checked_at: now.toISOString(), records: 4}]));
  const input = { now, manifest: {generated_at: now.toISOString(), promotion_count: promotions.length}, promotions, previous: promotions, sources };
  return { assessHealth, input };
}
test('healthy complete snapshot passes and reports unchanged counts', async () => {
  const { assessHealth, input } = await fixture();
  const report = assessHealth(input);
  assert.equal(report.healthy, true);
  assert.deepEqual(report.changes, {added: 0, removed: 0, modified: 0});
});
test('partial or failed source signals unhealthy without suppressing safe publication', async () => {
  const { assessHealth, input } = await fixture();
  input.sources.GNB.status = 'failed';
  input.sources.GNB.checked_at = '2026-10-24T15:00:00Z';
  input.sources.GNB.attempted_at = input.now.toISOString();
  const report = assessHealth(input);
  assert.equal(report.healthy, false);
  assert.equal(report.safe_to_commit, true);
  assert.ok(report.warnings.some(value => value.includes('72 hours')));
});
test('empty, mismatched and duplicate catalog cannot be committed', async () => {
  for (const kind of ['empty', 'mismatch', 'duplicate']) {
    const { assessHealth, input } = await fixture();
    if (kind === 'empty') input.promotions = [];
    if (kind === 'mismatch') input.manifest.promotion_count++;
    if (kind === 'duplicate') input.promotions[1].id = input.promotions[0].id;
    assert.equal(assessHealth(input).safe_to_commit, false, kind);
  }
});
test('single source collapse blocks commit even if total remains large', async () => {
  const { assessHealth, input } = await fixture();
  input.promotions = input.promotions.filter(row => row.bank !== 'GNB' || row.id.endsWith('-0'));
  input.manifest.promotion_count = input.promotions.length;
  assert.equal(assessHealth(input).safe_to_commit, false);
});
test('stale generation blocks commit; stale or invalid source timestamp signals failure', async () => {
  const { assessHealth, input } = await fixture();
  input.manifest.generated_at = '2026-10-28T00:00:00Z';
  assert.equal(assessHealth(input).safe_to_commit, false);
  input.manifest.generated_at = input.now.toISOString();
  input.sources.GNB.checked_at = 'not-a-date';
  assert.equal(assessHealth(input).healthy, false);
});
test('missing source metadata or empty source is unsafe', async () => {
  const { assessHealth, input } = await fixture();
  delete input.sources.GNB;
  assert.equal(assessHealth(input).safe_to_commit, false);
});
test('change counts distinguish removals from inferred expiry', async () => {
  const { assessHealth, input } = await fixture();
  input.previous = structuredClone(input.promotions);
  input.promotions[0] = {...input.promotions[0], detail: 'new detail'};
  input.promotions[1] = {...input.promotions[1], id: 'new-id'};
  assert.deepEqual(assessHealth(input).changes, {added: 1, modified: 1, removed: 1});
});
test('CLI blocks incomplete normalization and emits usable failure artifact', async () => {
  const { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } = require('node:fs');
  const { tmpdir } = require('node:os');
  const { join, resolve } = require('node:path');
  const { spawnSync } = require('node:child_process');
  const root = mkdtempSync(join(tmpdir(), 'payback-health-'));
  try {
    mkdirSync(join(root, 'outputs'));
    writeFileSync(join(root, 'outputs/refresh_report.json'), JSON.stringify({completed_at: '2026-10-29T00:00:00Z'}));
    const result = spawnSync(process.execPath, [resolve('scripts/maintenance-health.mjs'), 'unused.json'], {cwd: root, env: {...process.env, GITHUB_OUTPUT: '', GITHUB_STEP_SUMMARY: '', REFRESH_STARTED_AT: '2026-10-30T00:00:00Z'}});
    assert.equal(result.status, 1);
    const report = JSON.parse(readFileSync(join(root, 'outputs/maintenance_report.json')));
    assert.equal(report.safe_to_commit, false);
    assert.match(report.errors[0], /did not finish normalization/);
  } finally { rmSync(root, {recursive: true, force: true}); }
});
