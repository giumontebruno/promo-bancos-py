const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function client(permission = 'granted', subscription = { toJSON: () => ({}) }) {
  const shown = [];
  const storage = new Map([['paybackPy.pushEnabled', 'true'], ['paybackPy.deviceToken', 'test-token']]);
  const context = {
    navigator: { serviceWorker: { ready: Promise.resolve({
      pushManager: { getSubscription: async () => subscription },
      showNotification: async (...args) => shown.push(args),
    }) } },
    PushManager: {}, Notification: { permission },
    localStorage: { getItem: key => storage.get(key), removeItem: key => storage.delete(key) },
    fetch: async () => ({ ok: true, json: async () => ({ serviceUrl: 'https://example.com' }) }),
    URL, AbortSignal, setTimeout, clearTimeout,
  };
  vm.runInNewContext(fs.readFileSync('app-web/push-client.js', 'utf8'), context);
  return { api: context.PaybackPush, shown };
}

test('device test displays a notification after subscription synchronization', async () => {
  const { api, shown } = client();
  await api.test(new Set(['promo']), 2);
  assert.equal(shown.length, 1);
  assert.equal(shown[0][1].tag, 'payback-device-test');
});

test('revoked permission cannot appear enabled or trigger a test', async () => {
  const { api, shown } = client('denied');
  assert.equal(api.enabled(), false);
  await assert.rejects(api.test(new Set(), 1));
  assert.equal(shown.length, 0);
});

test('expired subscription does not report a successful local test', async () => {
  const { api, shown } = client('granted', null);
  await assert.rejects(api.test(new Set(), 1));
  assert.equal(api.enabled(), false);
  assert.equal(shown.length, 0);
});
