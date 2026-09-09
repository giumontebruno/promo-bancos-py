const { test } = require('node:test');
const assert = require('node:assert/strict');
const esbuild = require('esbuild');
const Module = require('node:module');
function loadModule(path) {
  const output = esbuild.buildSync({ entryPoints: [path], bundle: true, write: false, format: 'cjs', platform: 'node' });
  const module = new Module(path);
  module._compile(output.outputFiles[0].text, path);
  return module.exports;
}
const { isDue, notificationBenefit, todayParts } = loadModule('server/schedule.js');
const { validSubscription, default: worker } = loadModule('server/index.js');
const current = new Date('2026-09-09T12:00:00Z');
const promo = { terms: { starts_on: '2026-09-01', ends_on: '2026-09-30' }, promotion_days: ['miércoles'] };
test('alerts use Paraguay date including UTC midnight boundary', () => {
  assert.equal(todayParts(new Date('2026-09-10T01:00:00Z')).iso, '2026-09-09');
  assert.equal(isDue(promo, current), true);
});
test('expired, future, conflicting and unconfirmed validity never send', () => {
  for (const terms of [{ ends_on: '2026-08-31' }, { starts_on: '2026-09-10', ends_on: '2026-09-30' }, { ends_on: '2026-09-30', conflicting_dates: true }, {}]) {
    assert.equal(isDue({ ...promo, terms }, current), false);
  }
});
test('monthly and ordinal benefits only send on their applicable date', () => {
  assert.equal(isDue({ ...promo, month_days: [8] }, current), false);
  assert.equal(isDue({ ...promo, month_days: [9] }, current), true);
  assert.equal(isDue({ ...promo, ordinal_weekdays: [{ ordinal: 2, day: 'miércoles' }] }, current), true);
});
test('UENO notices respect the selected level; premium ambiguity is skipped', () => {
  const ueno = { bank: 'ueno bank', level_rules: 'Nivel 1: 10%; Nivel 5: 40%', level_benefits: [{ level: 1, percent: 10 }, { level: 5, percent: 40 }] };
  assert.match(notificationBenefit(ueno, 1), /^10%/);
  assert.match(notificationBenefit(ueno, 5), /^40%/);
  assert.equal(notificationBenefit({ benefit_summary: '20% reintegro y 25% con Black' }, 1), '');
});
test('only recognized HTTPS push services can receive server requests', () => {
  const keys = { p256dh: 'a'.repeat(87), auth: 'a'.repeat(22) };
  assert.equal(validSubscription({ endpoint: 'https://fcm.googleapis.com/fcm/send/test', keys }), true);
  for (const endpoint of ['https://localhost/test', 'http://fcm.googleapis.com/test', 'https://fcm.googleapis.com.evil.test/test', 'https://example.com/test']) {
    assert.equal(validSubscription({ endpoint, keys }), false);
  }
});
test('public endpoints reject foreign origins and unauthorized dispatch', async () => {
  const rejected = await worker.fetch(new Request('https://payback.test/api/push/config', { headers: { Origin: 'https://evil.test' } }), {});
  assert.equal(rejected.status, 403);
  const dispatch = await worker.fetch(new Request('https://payback.test/api/push/dispatch', { method: 'POST' }), { DB: {}, CRON_TOKEN: 'test' });
  assert.equal(dispatch.status, 401);
});
