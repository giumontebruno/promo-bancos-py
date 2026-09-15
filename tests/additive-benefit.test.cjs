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
