const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = name => fs.readFileSync(path.join(__dirname, '../beta-web', name), 'utf8');

function harness() {
  const listeners = {}, storage = new Map(), classes = new Set();
  const retry = { focus() {} }, login = {}, status = {}, app = {}, nav = {}, search = { focus() {} };
  const gate = { hidden: true, dataset: {}, setAttribute() {},
    querySelector: () => retry, querySelectorAll: () => [login],
    addEventListener: (name, fn) => { listeners[name] = fn; } };
  const dialog = { open: false, close() { this.open = false; }, addEventListener() {}, querySelector() {} };
  const nodes = { authGate: gate, authStatus: status, bottomNav: nav, searchInput: { ...search, addEventListener() {} } };
  const context = vm.createContext({
    setTimeout, clearTimeout, URL, AbortSignal, Map, Set,
    CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
    localStorage: { getItem: k => storage.get(k), setItem: (k, v) => storage.set(k, v) },
    document: {
      createElement: () => dialog, getElementById: id => nodes[id],
      querySelector: () => app, addEventListener() {},
      body: { append() {}, classList: { toggle(name, enabled) { enabled ? classes.add(name) : classes.delete(name); } } },
    },
    window: { addEventListener() {}, dispatchEvent() {} },
    fetch: async () => { throw new Error('Account service unavailable'); },
    navigator: { onLine: true },
  });
  vm.runInContext(read('beta-client.js').replace(/^import[^\n]*\n/gm, '').replace(/updateGate\(\);\s*init\(\);\s*$/, ''), context);
  return { context, gate, dialog, app, nav, classes, storage, listeners, run: code => vm.runInContext(code, context) };
}

test('catalog is public before JavaScript and authentication starts', () => {
  const html = read('index.html');
  assert.match(html, /<body>/);
  assert.match(html, /<section id="authGate" hidden/);
  assert.match(html, /data-auth-guest>Seguir sin iniciar sesión/);
  assert.doesNotMatch(html, /<main[^>]*inert/);
});

test('background checking, anonymous and failed authentication leave catalog interactive', async () => {
  const h = harness();
  for (const phase of ['checking', 'anonymous', 'error']) {
    h.run(`authPhase = '${phase}'; updateGate();`);
    assert.equal(h.gate.hidden, true);
    assert.equal(h.app.inert, false);
    assert.equal(h.nav.inert, false);
    assert.equal(h.classes.has('auth-required'), false);
  }
  await h.run('init()');
  assert.equal(h.run('authPhase'), 'error');
  assert.equal(h.run('current'), null);
  assert.equal(h.gate.hidden, true);
  assert.equal(h.app.inert, false);
});

test('account access is opt-in and guest return works even during checking or errors', async () => {
  const h = harness();
  for (const phase of ['checking', 'anonymous', 'error']) {
    h.run(`authPhase = '${phase}'; show();`);
    assert.equal(h.gate.hidden, false);
    assert.equal(h.app.inert, true);
    await h.listeners.click({ target: { closest: selector => selector === '[data-auth-guest]' ? {} : null } });
    assert.equal(h.gate.hidden, true);
    assert.equal(h.app.inert, false);
    assert.equal(h.run('authRequested'), false);
  }
});

test('verified account closes opt-in gate; logout returns to guest without merging data', async () => {
  const h = harness();
  h.storage.set('paybackPyBeta.favorites', '["guest-promo"]');
  h.storage.set('paybackPyBeta.account.other', '{"favorites":["other-promo"]}');
  h.run("authRequested = true; current = {localId:'verified',favorites:['account-promo'],uenoLevel:3}; changed();");
  assert.equal(h.gate.hidden, true);
  assert.equal(h.run('authRequested'), false);
  h.run("current = null; authPhase = 'anonymous'; changed();");
  assert.equal(h.app.inert, false);
  await assert.rejects(h.run("favorite('guest-promo', true)"), /Ingresá con Google/);
  assert.equal(h.storage.get('paybackPyBeta.favorites'), '["guest-promo"]');
  assert.equal(h.storage.get('paybackPyBeta.account.other'), '{"favorites":["other-promo"]}');
  assert.equal(h.storage.has('paybackPyBeta.account.verified'), false);
});

test('switching from account dialog to guest gate closes the modal', () => {
  const h = harness();
  h.dialog.open = true;
  h.run('current = null; show();');
  assert.equal(h.dialog.open, false);
  assert.equal(h.gate.hidden, false);
});
