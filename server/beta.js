const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
const emails = value => (value || '').split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
export const EVENT_KINDS = ['session', 'search', 'filter', 'promo_open', 'favorite_add', 'map_open', 'directions'];
export function validEvent(body) {
  return body && Object.keys(body).length === 1 && EVENT_KINDS.includes(body.kind);
}
export async function betaIdentity(request, env, token = request.headers.get('Authorization')) {
  if (!env.SUPABASE_URL || !env.SUPABASE_PUBLISHABLE_KEY) return null;
  if (!token?.startsWith('Bearer ') || token.length > 8000) return null;
  const result = await fetch(new URL('/auth/v1/user', env.SUPABASE_URL), {
    headers: { Authorization: token, apikey: env.SUPABASE_PUBLISHABLE_KEY }, signal: AbortSignal.timeout(10000),
  });
  if (!result.ok) return null;
  const user = await result.json();
  if (!user.id || !user.email_confirmed_at || !user.email) return null;
  const email = user.email.toLowerCase();
  const admin = emails(env.BETA_ADMIN_EMAILS).includes(email);
  return { id: user.id, email, admin };
}
async function bodyOf(request) {
  const text = await request.text();
  if (text.length > 6000) throw new Error('Body too large');
  return JSON.parse(text);
}
export async function handleBeta(request, env) {
  const path = new URL(request.url).pathname;
  if (path === '/api/beta/config' && request.method === 'GET') {
    const enabled = Boolean(env.DB && env.SUPABASE_URL && env.SUPABASE_PUBLISHABLE_KEY && env.BETA_ADMIN_EMAILS);
    return json({ enabled, url: enabled ? env.SUPABASE_URL : null, key: enabled ? env.SUPABASE_PUBLISHABLE_KEY : null });
  }
  if (!env.DB) return json({ error: 'Beta no disponible' }, 503);
  const user = await betaIdentity(request, env);
  if (!user) return json({ error: 'Ingresá con Google para acceder a tu cuenta.' }, 401);
  const db = env.DB;
  const now = new Date().toISOString();
  await db.prepare('INSERT OR IGNORE INTO beta_accounts (id,email,created_at) VALUES (?,?,?)').bind(user.id, user.email, now).run();
  if (path === '/api/beta/me' && request.method === 'GET') {
    const account = await db.prepare('SELECT consent,ueno_level FROM beta_accounts WHERE id=?').bind(user.id).first();
    const { results } = await db.prepare('SELECT promo_id FROM beta_favorites WHERE account_id=?').bind(user.id).all();
    return json({ email: user.email, admin: user.admin, consent: Boolean(account.consent), uenoLevel: account.ueno_level, favorites: results.map(r => r.promo_id) });
  }
  if (path === '/api/beta/me' && request.method === 'PUT') {
    const body = await bodyOf(request);
    if (typeof body.consent !== 'boolean' || !Number.isInteger(body.uenoLevel) || body.uenoLevel < 1 || body.uenoLevel > 5) return json({ error: 'Preferencias inválidas' }, 400);
    const statements = [db.prepare('UPDATE beta_accounts SET consent=?,ueno_level=? WHERE id=?').bind(Number(body.consent), body.uenoLevel, user.id)];
    if (!body.consent) statements.push(db.prepare('DELETE FROM beta_activity WHERE account_id=?').bind(user.id));
    await db.batch(statements);
    return json({ ok: true });
  }
  if (path === '/api/beta/me' && request.method === 'DELETE') {
    await db.batch([
      db.prepare("DELETE FROM deliveries WHERE EXISTS (SELECT 1 FROM devices d WHERE d.account_id=? AND deliveries.key LIKE d.id || ':%')").bind(user.id),
      db.prepare('DELETE FROM devices WHERE account_id=?').bind(user.id),
      ...['beta_activity', 'beta_reports', 'beta_favorites'].map(table => db.prepare(`DELETE FROM ${table} WHERE account_id=?`).bind(user.id)),
      db.prepare('DELETE FROM beta_accounts WHERE id=?').bind(user.id),
    ]);
    return json({ ok: true });
  }
  if (path === '/api/beta/favorite' && ['PUT', 'DELETE'].includes(request.method)) {
    const body = await bodyOf(request);
    if (!/^[a-f0-9-]{16,40}$/.test(body.promoId || '')) return json({ error: 'Promoción inválida' }, 400);
    if (request.method === 'PUT') {
      const result = await db.prepare(`INSERT OR IGNORE INTO beta_favorites(id,account_id,promo_id)
        SELECT ?,?,? WHERE (SELECT COUNT(*) FROM beta_favorites WHERE account_id=?) < 100`)
        .bind(crypto.randomUUID(), user.id, body.promoId, user.id).run();
      if (!result.meta.changes && !await db.prepare('SELECT id FROM beta_favorites WHERE account_id=? AND promo_id=?').bind(user.id, body.promoId).first()) return json({ error: 'Podés guardar hasta 100 favoritos.' }, 409);
    } else await db.prepare('DELETE FROM beta_favorites WHERE account_id=? AND promo_id=?').bind(user.id, body.promoId).run();
    return json({ ok: true });
  }
  if (path === '/api/beta/event' && request.method === 'POST') {
    const body = await bodyOf(request);
    if (!validEvent(body)) return json({ error: 'Evento inválido' }, 400);
    const account = await db.prepare('SELECT consent FROM beta_accounts WHERE id=?').bind(user.id).first();
    if (!account?.consent) return json({ ok: true });
    // Daily counters only: no query text, coordinates, or browsing history.
    const day = now.slice(0, 10);
    await db.prepare(`INSERT INTO beta_activity(id,account_id,day,kind,count) VALUES (?,?,?,?,1)
      ON CONFLICT(account_id,day,kind) DO UPDATE SET count=MIN(count+1,1000)`)
      .bind(crypto.randomUUID(), user.id, day, body.kind).run();
    await db.prepare("DELETE FROM beta_activity WHERE day < date('now','-30 days')").run();
    return json({ ok: true });
  }
  if (path === '/api/beta/report' && request.method === 'POST') {
    const body = await bodyOf(request);
    if (!['missing', 'incorrect', 'suggestion'].includes(body.kind) || typeof body.message !== 'string' || body.message.trim().length < 10 || body.message.length > 2000 || (body.promoId && !/^[a-f0-9-]{16,40}$/.test(body.promoId))) return json({ error: 'Revisá el comentario (10 a 2000 caracteres).' }, 400);
    const { n } = await db.prepare("SELECT COUNT(*) n FROM beta_reports WHERE account_id=? AND created_at >= date('now')").bind(user.id).first();
    if (n >= 10) return json({ error: 'Alcanzaste los 10 reportes de hoy.' }, 429);
    await db.prepare('INSERT INTO beta_reports(id,account_id,kind,promo_id,message,version,created_at) VALUES (?,?,?,?,?,?,?)')
      .bind(crypto.randomUUID(), user.id, body.kind, body.promoId || null, body.message.trim(), 'beta-1', now).run();
    return json({ ok: true });
  }
  if (path === '/api/beta/admin' && request.method === 'GET') {
    if (!user.admin) return json({ error: 'No autorizado' }, 403);
    const participants = await db.prepare(`SELECT a.email,a.consent,e.day,e.kind,e.count FROM beta_accounts a
      LEFT JOIN beta_activity e ON e.account_id=a.id AND e.day >= date('now','-30 days') ORDER BY a.email,e.day DESC`).all();
    const reports = await db.prepare(`SELECT r.kind,r.promo_id,r.message,r.created_at,a.email FROM beta_reports r
      JOIN beta_accounts a ON a.id=r.account_id ORDER BY r.created_at DESC LIMIT 100`).all();
    return json({ participants: participants.results, reports: reports.results });
  }
  return json({ error: 'Ruta no disponible' }, 404);
}
