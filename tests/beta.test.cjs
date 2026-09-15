const { test } = require('node:test');
const assert = require('node:assert/strict');
const { DatabaseSync } = require('node:sqlite');
const { readFileSync, readdirSync } = require('node:fs');
const beta = import('../server/beta.js');
function database() {
  const db = new DatabaseSync(':memory:');
  for (const file of readdirSync('drizzle').filter(f => f.endsWith('.sql')).sort()) db.exec(readFileSync('drizzle/' + file, 'utf8'));
  return {
    prepare(sql) {
      const stmt = db.prepare(sql); let args = [];
      return { bind(...values) { args = values; return this; }, async first() { return stmt.get(...args) || null; }, async all() { return { results: stmt.all(...args) }; }, async run() { return { meta: stmt.run(...args) }; } };
    }, async batch(items) { db.exec('BEGIN'); try { const result = []; for (const item of items) result.push(await item.run()); db.exec('COMMIT'); return result; } catch (e) { db.exec('ROLLBACK'); throw e; } },
  };
}
test('beta authentication, isolated favorites, consent, reporting and admin access', async () => {
  const { handleBeta } = await beta;
  const originalFetch = global.fetch;
  global.fetch = async (_url, options) => {
    const id = options.headers.Authorization.replace('Bearer ', '');
    return Response.json({ id, email: id + '@test.invalid', email_confirmed_at: '2026-01-01' });
  };
  const env = { DB: database(), SUPABASE_URL: 'https://auth.test.invalid', SUPABASE_PUBLISHABLE_KEY: 'public', BETA_ALLOWED_EMAILS: 'alice@test.invalid,bob@test.invalid', BETA_ADMIN_EMAILS: 'owner@test.invalid' };
  async function call(user, path, method = 'GET', body) {
    return handleBeta(new Request('https://app.test/api/beta/' + path, { method, headers: user ? { Authorization: 'Bearer ' + user } : {}, body: body ? JSON.stringify(body) : undefined }), env);
  }
  try {
    assert.equal((await call(null, 'me')).status, 401);
    assert.equal((await call('outsider', 'me')).status, 200);
    assert.equal((await (await call('outsider', 'me')).json()).admin, false);
    assert.equal((await call('outsider', 'admin')).status, 403);
    assert.equal((await call('alice', 'admin')).status, 403);
    const id = 'a'.repeat(32);
    await call('alice', 'favorite', 'PUT', { promoId: id });
    assert.deepEqual((await (await call('alice', 'me')).json()).favorites, [id]);
    assert.deepEqual((await (await call('bob', 'me')).json()).favorites, []);
    await call('bob', 'favorite', 'DELETE', { promoId: id });
    assert.deepEqual((await (await call('alice', 'me')).json()).favorites, [id]);
    await call('alice', 'event', 'POST', { kind: 'search' });
    assert.equal((await env.DB.prepare('SELECT COUNT(*) n FROM beta_activity').first()).n, 0);
    await call('alice', 'me', 'PUT', { consent: true, uenoLevel: 3 });
    assert.equal((await call('alice', 'event', 'POST', { kind: 'search', query: 'private' })).status, 400);
    await call('alice', 'event', 'POST', { kind: 'search' });
    assert.equal((await env.DB.prepare('SELECT count FROM beta_activity').first()).count, 1);
    await call('alice', 'me', 'PUT', { consent: false, uenoLevel: 3 });
    assert.equal((await env.DB.prepare('SELECT COUNT(*) n FROM beta_activity').first()).n, 0);
    assert.equal((await call('alice', 'report', 'POST', { kind: 'missing', message: 'Falta un restaurante', promoId: '' })).status, 200);
    const admin = await (await call('owner', 'admin')).json();
    assert.equal(admin.reports.length, 1);
    await call('alice', 'me', 'DELETE');
    assert.equal((await env.DB.prepare('SELECT COUNT(*) n FROM beta_favorites').first()).n, 0);
    assert.equal((await env.DB.prepare('SELECT COUNT(*) n FROM beta_reports').first()).n, 0);
  } finally { global.fetch = originalFetch; }
});
test('beta is disabled without provider configuration', async () => {
  const { handleBeta, validEvent } = await beta;
  const response = await handleBeta(new Request('https://app.test/api/beta/config'), {});
  assert.equal((await response.json()).enabled, false);
  assert.equal(validEvent({ kind: 'directions', latitude: -25 }), false);
  assert.equal(validEvent({ kind: 'unknown' }), false);
});
