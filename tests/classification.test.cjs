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
