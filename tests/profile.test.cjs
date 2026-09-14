const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const source = readFileSync('app-web/app.js', 'utf8');
const render = source.slice(source.indexOf('function renderAlertsView()'), source.indexOf('function syncFavoriteAlerts()'));
function profile(account) {
  const context = {
    window: { PaybackBeta: { current: account } },
    state: { favorites: new Set(), promotions: [], alertPrefs: {}, pushMessage: '', user: { name: 'Old manual name' } },
    els: { statusText: {}, countText: {}, results: {} },
    PaybackPush: { enabled: () => false }, renderIcon: () => '',
    escapeHtml: value => String(value).replaceAll('<', '&lt;').replaceAll('>', '&gt;'),
  };
  vm.runInNewContext(render + '\nrenderAlertsView();', context);
  return context.els.results.innerHTML;
}
test('guest profile places direct Google login before favorite notifications and has no manual name', () => {
  const html = profile(null);
  assert.match(html, /Activá tu perfil Payback/);
  assert.match(html, /data-beta-login/);
  assert.match(html, /Activar notificaciones/);
  assert.ok(html.indexOf('data-beta-login') < html.indexOf('favorite-alerts'));
  assert.doesNotMatch(html, /name="name"|Old manual name/);
});
test('signed-in profile uses escaped Google name and account management instead of login', () => {
  const html = profile({ name: '<Google Name>', email: 'tester@example.com' });
  assert.match(html, /Hola, &lt;Google Name&gt;/);
  assert.match(html, /data-beta-open/);
  assert.doesNotMatch(html, /data-beta-login|name="name"|Old manual name/);
});
