const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app-web/app.js', 'utf8');
function active(promo) {
  const context = { Intl, Date, getPromotionEndDate: () => null, getTodayDateOnly: () => new Date() };
  vm.runInNewContext(source.slice(source.indexOf('function isActivePromotion('), source.indexOf('function shouldShowPromotion(')), context);
  return context.isActivePromotion(promo);
}
test('missing or contradictory dates are never presented as active', () => {
  assert.equal(active({}), false);
  assert.equal(active({terms: {conflicting_dates: true, ends_on: '2999-12-31'}}), false);
});
test('unconfirmed sources retain data without becoming active by default', () => {
  assert.equal(active({source_verification: 'unconfirmed', terms: {ends_on: '2999-12-31'}}), false);
});
test('bounded offers follow dates without needing a new review flag', () => {
  assert.equal(active({terms: {ends_on: '2999-12-31'}}), true);
  assert.equal(active({terms: {ends_on: '2000-01-01'}}), false);
  assert.equal(active({terms: {starts_on: '2999-01-01', ends_on: '2999-12-31'}}), false);
});

test('an unrelated future date in source text cannot revive unknown validity', () => {
  assert.equal(active({terms: {}, validity: 'Hasta 2999-12-31', raw_detail: 'Saldo hasta 2999-12-31'}), false);
});
