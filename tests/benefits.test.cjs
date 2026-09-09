const { test } = require('node:test');
const assert = require('node:assert/strict');
const rules = require('../app-web/benefit-rules.js');

test('purchase cap and refund cap are separate, not interchangeable', () => {
  const limits = rules.explicitLimits('Tope de compra: Gs. 500.000; Tope de reintegro: Gs. 100.000');
  assert.equal(rules.uniqueLimit(limits, 'purchase'), 500000);
  assert.equal(rules.uniqueLimit(limits, 'refund'), 100000);
  assert.equal(rules.calculate({ percent: 20, purchaseCap: 500000, refundCap: 100000 }).estimated, 100000);
});
test('estimated savings obey the smaller of eligible spend and refund cap', () => {
  assert.equal(rules.calculate({ percent: 20, purchaseCap: 100000, refundCap: 500000, amount: 700000 }).estimated, 20000);
  assert.equal(rules.calculate({ percent: 20, purchaseCap: 500000, refundCap: 50000, amount: 500000 }).estimated, 50000);
});
test('unknown or conflicting caps are not guessed from an unrelated amount', () => {
  assert.deepEqual(rules.explicitLimits('Gs. 500.000; Gs. 100.000'), []);
  assert.equal(rules.uniqueLimit([{ kind: 'refund', amount: 100000 }, { kind: 'refund', amount: 200000 }], 'refund'), 0);
  assert.equal(rules.calculate({ percent: 20 }).estimated, 0);
});
test('minimum spend and invalid percentage do not promise savings', () => {
  assert.equal(rules.calculate({ percent: 20, minimum: 100000, amount: 50000 }).estimated, 0);
  assert.equal(rules.calculate({ percent: 120, amount: 500000 }).estimated, 0);
});
test('display casing preserves payment brands', () => {
  assert.equal(rules.normalizeText('TARJETAS VISA Y MASTERCARD CON APPLE PAY'), 'Tarjetas Visa y Mastercard con Apple Pay');
});
