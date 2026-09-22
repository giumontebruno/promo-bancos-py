const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
test('additional premium percentage is not the base rate', () => {
  const source = fs.readFileSync('app-web/app.js','utf8');
  const context = {isUenoPowerPromo:()=>false, normalizeDayName:s=>s.toLowerCase()};
  vm.runInNewContext(source.slice(source.indexOf('function getPromoVariants('),source.indexOf('function getVariantByKey(')),context);
  const variants = context.getPromoVariants({benefit_summary:'20% DE REINTEGRO + 5% PARA BLACK E INFINITE'});
  assert.equal(variants[0].benefit,'20% reintegro');
  assert.equal(variants[1].benefit,'25% reintegro');
});

test('stacked merchant and bank discounts use the effective rate for savings', () => {
  const source = fs.readFileSync('app-web/app.js', 'utf8');
  const context = {
    state: {uenoLevel: 1},
    getSelectedUenoLevelDetails: () => null,
    getMainBenefit: promo => promo.benefit_summary,
    percentNumber: value => Number(String(value).match(/\d+/)?.[0] || 0),
    PaybackBenefits: {
      uniqueLimit: (limits, kind) => limits.find(item => item.kind === kind)?.amount || 0,
      calculate: ({percent, purchaseCap, amount}) => ({estimated: Math.min(amount ?? purchaseCap, purchaseCap) * percent / 100, capped: false, belowMinimum: false}),
    },
  };
  vm.runInNewContext(source.slice(source.indexOf('function getEstimatedSavings('), source.indexOf('function getDetailRows(')), context);
  const benefit = {
    bank: 'GNB',
    benefit_summary: '35% de descuento anunciado',
    effective_percent: 32,
    terms: {limits: [{kind: 'purchase', amount: 1000000}]},
  };
  const savings = context.getEstimatedSavings(benefit, 100000);
  assert.equal(savings.percent, 32);
  assert.equal(savings.refundCap, 32000);
});
