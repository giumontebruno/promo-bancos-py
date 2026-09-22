const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('app-web/app.js', 'utf8');
const context = { normalizeDayName: value => value.toLowerCase() };
vm.runInNewContext(source.slice(source.indexOf('function isInstallmentsOnly('), source.indexOf('function getBankTheme(')), context);
test('QR discounts stay out of the financing-only section even for legacy data', () => {
  assert.equal(context.isInstallmentsOnly({benefit_summary:'6 Cuotas sin intereses 35% Pago con QR', benefit_type:'cuotas_sin_intereses'}), false);
  assert.equal(context.isInstallmentsOnly({benefit_summary:'20% de ahorro y 6 cuotas sin intereses'}), false);
  assert.equal(context.isInstallmentsOnly({benefit_summary:'6 cuotas sin intereses. Tasa 0%'}), true);
});
const categoryContext = { normalizeDayName: value => String(value).toLowerCase() };
vm.runInNewContext(
  source.slice(source.indexOf('const CATEGORY_GROUPS ='), source.indexOf('const METRO_AREA_TERMS =')) +
  source.slice(source.indexOf('function getPromoCategoryGroup('), source.indexOf('function getCategoryOrder(')),
  categoryContext,
);
test('pharmacy merchants are shown under Farmacias even when the bank labels them Salud', () => {
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Belleza y Salud', merchant_name: 'Punto Farma' }), 'Farmacias');
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Otros', merchant_name: 'Farmavida' }), 'Farmacias');
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Belleza y Salud', merchant_name: 'Bela Nails' }), 'Salud y belleza');
  const promotions = JSON.parse(fs.readFileSync('public/promotions.json', 'utf8'));
  const puntoFarma = promotions.find(promo => promo.bank === 'Itaú' && promo.merchant_name === 'Punto Farma' && promo.promotion_days.includes('martes'));
  assert.ok(puntoFarma, 'Itaú Punto Farma must remain in the catalog on Tuesdays');
  assert.equal(categoryContext.getPromoCategoryGroup(puntoFarma), 'Farmacias');
});
