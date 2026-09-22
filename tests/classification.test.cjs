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
const categoryContext = { normalizeDayName: value => String(value ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim() };
vm.runInNewContext(
  source.slice(source.indexOf('const CATEGORY_GROUPS ='), source.indexOf('const METRO_AREA_TERMS =')) +
  source.slice(source.indexOf('function getPromoCategoryGroup('), source.indexOf('function getCategoryOrder(')),
  categoryContext,
);
test('pharmacy merchants are shown under Farmacias even when the bank labels them Salud', () => {
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Belleza y Salud', merchant_name: 'Punto Farma' }), 'Farmacias');
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Otros', merchant_name: 'Farmavida' }), 'Farmacias');
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Tiendas', merchant_name: 'ALTEZA PERFUMERÍA' }), 'Farmacias');
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Belleza y Salud', merchant_name: 'Bela Nails' }), 'Salud y belleza');
  const promotions = JSON.parse(fs.readFileSync('public/promotions.json', 'utf8'));
  const puntoFarma = promotions.find(promo => promo.bank === 'Itaú' && promo.merchant_name === 'Punto Farma' && promo.promotion_days.includes('martes'));
  assert.ok(puntoFarma, 'Itaú Punto Farma must remain in the catalog on Tuesdays');
  assert.equal(categoryContext.getPromoCategoryGroup(puntoFarma), 'Farmacias');
});
test('the bank category outranks misleading substrings in merchant names', () => {
  const cases = [
    ['Gastronomía', 'Real Restaurante - Luque', 'Gastronomía'],
    ['Tiendas', 'Birkenstock', 'Tiendas'],
    ['Tiendas', 'Tienda Shelly', 'Tiendas'],
    ['Hogar y tecnología', 'ALEMANIA CELL-SHOPPING MARIANO', 'Hogar y construcción'],
    ['Salud y belleza', 'BAR DE CEJAS - SHOPPING COSTANERA', 'Salud y belleza'],
    ['Vehículos', 'CITROEN', 'Servicios'],
  ];
  for (const [category, merchant_name, expected] of cases) {
    assert.equal(categoryContext.getPromoCategoryGroup({ category, merchant_name }), expected, merchant_name);
  }
});
test('all source category aliases have a useful filter', () => {
  const cases = [
    ['Fast Food', 'Gastronomía'],
    ['Ópticas', 'Salud y belleza'],
    ['Electrodomésticos', 'Tecnología'],
    ['Instituciones Educativas', 'Servicios'],
    ['Laboratorios', 'Salud y belleza'],
    ['Estética', 'Salud y belleza'],
    ['Mecánica', 'Servicios'],
    ['Inmuebles', 'Servicios'],
    ['Librerías', 'Tiendas'],
    ['Frigoríficos', 'Supermercados'],
    ['Bodegas', 'Tiendas'],
    ['Servicios', 'Servicios'],
  ];
  for (const [category, expected] of cases) {
    assert.equal(categoryContext.getPromoCategoryGroup({ category, merchant_name: '' }), expected, category);
  }
});
test('generic source categories still use a recognizable merchant', () => {
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Sin categoría', merchant_name: 'Superseis' }), 'Supermercados');
  assert.equal(categoryContext.getPromoCategoryGroup({ category: 'Varios', merchant_name: 'Farmacenter' }), 'Farmacias');
});
const benefitContext = {
  getMainBenefit: promo => promo.benefit_summary,
  normalizeDayName: value => String(value).toLowerCase(),
};
vm.runInNewContext(source.slice(source.indexOf('function getBenefitLines('), source.indexOf('function getDisplayBenefit(')), benefitContext);
test('Itaú Punto Farma describes the variable QR rate as up to 35%', () => {
  const promotions = JSON.parse(fs.readFileSync('public/promotions.json', 'utf8'));
  const promo = promotions.find(item => item.bank === 'Itaú' && item.merchant_name === 'Punto Farma' && item.promotion_days.includes('martes'));
  assert.equal(benefitContext.getBenefitLines(promo)[0], 'Hasta 35% descuento · QR');
});
