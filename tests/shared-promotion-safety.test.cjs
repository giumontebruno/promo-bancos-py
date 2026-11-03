const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const promotions = JSON.parse(fs.readFileSync('public/promotions.json', 'utf8'));
for (const app of ['app-web', 'beta-web']) {
  test(`${app} uses the shared catalog and excludes disputed Familiar and expired BNF offers`, () => {
    const source = fs.readFileSync(`${app}/app.js`, 'utf8');
    assert.match(source, /const DATA_URL = "\.\.\/public\/promotions.json"/);
    const context = { getDateTimeFormatter: () => ({ format: () => '2026-11-03' }), Date };
    const start = source.indexOf('function isActivePromotion(');
    vm.runInNewContext(source.slice(start, source.indexOf('function shouldShowPromotion(', start)), context);
    const disputed = promotions.filter(p => p.bank === 'Familiar' && /mariscal/i.test(p.merchant_name) && /jueves\s+mariano/i.test(p.original_source_text || ''));
    assert.equal(context.isActivePromotion({ source_verification: 'unconfirmed', terms: { ends_on: '2026-12-31' } }), false);
    for (const promo of disputed) {
      assert.equal(promo.source_verification, 'unconfirmed');
      assert.equal(context.isActivePromotion(promo), false);
    }
    const expired = promotions.filter(p => p.bank === 'BNF' && p.terms?.ends_on < '2026-11-01');
    assert.equal(context.isActivePromotion({ terms: { ends_on: '2026-10-31' } }), false);
    for (const promo of expired) assert.equal(context.isActivePromotion(promo), false);
  });
}
