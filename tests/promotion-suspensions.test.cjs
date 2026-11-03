const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('bank suspension is reversible, idempotent and preserves every other field and bank', async () => {
  const { applySuspensions } = await import('../scripts/promotion-suspensions.mjs');
  const rows = [
    { id: 'a', bank: 'ueno bank', raw_detail: 'original', terms: { ends_on: '2999-12-31' } },
    { id: 'b', bank: 'ueno bank', source_verification: 'official_document' },
    { id: 'c', bank: 'ueno bank', source_verification: 'unconfirmed' },
    { id: 'd', bank: 'Other', source_verification: 'official_document' },
  ];
  const snapshot = structuredClone(rows);
  const held = applySuspensions(rows, ['ueno bank']);
  assert.deepEqual(rows, snapshot);
  assert.deepEqual(held[3], rows[3]);
  assert.ok(held.slice(0, 3).every(p => p.source_verification === 'unconfirmed'));
  assert.deepEqual(applySuspensions(held, ['ueno bank']), held);
  assert.deepEqual(applySuspensions(held, []), rows);
});

test('publication reapplies suspension to fresh automated data before copying shared public files', async () => {
  const { applySuspensions } = await import('../scripts/promotion-suspensions.mjs');
  const banks = JSON.parse(fs.readFileSync('public/promotion-suspensions.json', 'utf8')).banks;
  const build = fs.readFileSync('scripts/build.mjs', 'utf8');
  assert.ok(build.indexOf("await prepareSuspensions('public')") < build.indexOf("await cp('public'"));
  const rows = JSON.parse(fs.readFileSync('public/promotions.json', 'utf8'));
  // Emulate a refresh producing a previously unseen, otherwise valid offer.
  rows.push({ id: 'future-offer', bank: 'ueno bank', source_verification: 'official_document', terms: { ends_on: '2999-12-31' } });
  const prepared = applySuspensions(rows, banks);
  for (const app of ['app-web', 'beta-web']) {
    const code = fs.readFileSync(`${app}/app.js`, 'utf8');
    assert.match(code, /const DATA_URL = "\.\.\/public\/promotions.json"/);
    const context = { getDateTimeFormatter: () => ({ format: () => '2026-11-03' }), Date };
    vm.runInNewContext(code.slice(code.indexOf('function isActivePromotion('), code.indexOf('function shouldShowPromotion(')), context);
    for (const promo of prepared.filter(p => banks.includes(p.bank))) assert.equal(context.isActivePromotion(promo), false);
    assert.equal(context.isActivePromotion({ bank: 'Other', terms: { ends_on: '2999-12-31' } }), true);
  }
});
