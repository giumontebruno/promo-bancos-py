import { buildPushPayload } from '@block65/webcrypto-web-push';
import { isDue, notificationBenefit, todayParts } from './schedule.js';

const APP_URL = 'https://giumontebruno.github.io/promo-bancos-py/app-web/';
const DATA_URL = new URL('../public/promotions.json', APP_URL).href;
const PUSH_HOSTS = ['fcm.googleapis.com', 'updates.push.services.mozilla.com', 'web.push.apple.com', 'wns.windows.com', 'notify.windows.com'];
const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
const hash = async value => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))].map(n => n.toString(16).padStart(2, '0')).join('');

export function validSubscription(subscription) {
  try {
    const url = new URL(subscription.endpoint);
    return url.protocol === 'https:' && !url.username && !url.password && !url.port
      && PUSH_HOSTS.some(host => url.hostname === host || url.hostname.endsWith(`.${host}`))
      && /^[A-Za-z0-9_-]{87,88}={0,2}$/.test(subscription.keys?.p256dh || '')
      && /^[A-Za-z0-9_-]{22,24}={0,2}$/.test(subscription.keys?.auth || '');
  } catch { return false; }
}

async function handle(request, env) {
  const url = new URL(request.url);
  if (url.pathname === '/api/push/config' && request.method === 'GET') {
    return json({ enabled: Boolean(env.DB && env.VAPID_PUBLIC_KEY && env.VAPID_PRIVATE_KEY), publicKey: env.VAPID_PUBLIC_KEY || null });
  }
  if (!env.DB) return json({ error: 'Servicio temporalmente no disponible' }, 503);
  if (url.pathname === '/api/push/device') {
    const token = request.headers.get('Authorization')?.replace(/^Bearer /, '') || '';
    if (!/^[a-f0-9]{64}$/.test(token)) return json({ error: 'Dispositivo no autorizado' }, 401);
    const tokenHash = await hash(token);
    if (request.method === 'DELETE') {
      await env.DB.prepare('DELETE FROM devices WHERE token_hash = ?').bind(tokenHash).run();
      return json({ ok: true });
    }
    if (request.method === 'GET') {
      const row = await env.DB.prepare('SELECT favorites, ueno_level FROM devices WHERE token_hash = ?').bind(tokenHash).first();
      return row ? json({ favorites: JSON.parse(row.favorites), uenoLevel: row.ueno_level }) : json({ error: 'Sin suscripción' }, 404);
    }
    if (request.method !== 'PUT') return json({ error: 'Método no permitido' }, 405);
    if (Number(request.headers.get('Content-Length')) > 16000) return json({ error: 'Datos demasiado grandes' }, 413);
    const raw = await request.text();
    if (raw.length > 16000) return json({ error: 'Datos demasiado grandes' }, 413);
    let body;
    try { body = JSON.parse(raw); } catch { return json({ error: 'Datos inválidos' }, 400); }
    if (!body || typeof body !== 'object') return json({ error: 'Datos inválidos' }, 400);
    if (!validSubscription(body.subscription) || !Array.isArray(body.favorites) || body.favorites.length > 100
      || body.favorites.some(id => typeof id !== 'string' || !/^[a-f0-9-]{16,40}$/.test(id))) return json({ error: 'Suscripción inválida' }, 400);
    const level = Number(body.uenoLevel || 1);
    if (!Number.isInteger(level) || level < 1 || level > 5) return json({ error: 'Nivel inválido' }, 400);
    await env.DB.prepare(`INSERT INTO devices (id, token_hash, subscription, favorites, ueno_level, updated_at)
      VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(token_hash) DO UPDATE SET subscription=excluded.subscription,
      favorites=excluded.favorites, ueno_level=excluded.ueno_level, updated_at=excluded.updated_at`)
      .bind(crypto.randomUUID(), tokenHash, JSON.stringify(body.subscription), JSON.stringify([...new Set(body.favorites)]), level, new Date().toISOString()).run();
    return json({ ok: true });
  }
  if (url.pathname === '/api/push/dispatch' && request.method === 'POST') {
    const credential = request.headers.get('Authorization') || '';
    if (!env.CRON_TOKEN || await hash(credential) !== await hash(`Bearer ${env.CRON_TOKEN}`)) return json({ error: 'No autorizado' }, 401);
    const cursor = url.searchParams.get('cursor') || '';
    const response = await fetch(DATA_URL, { cache: 'no-store', signal: AbortSignal.timeout(15000) });
    if (!response.ok) return json({ error: 'No se pudo verificar el catálogo' }, 502);
    const promotions = await response.json();
    if (!Array.isArray(promotions)) return json({ error: 'Catálogo inválido' }, 502);
    const manifestResponse = await fetch(new URL('manifest.json', DATA_URL), { cache: 'no-store', signal: AbortSignal.timeout(15000) });
    if (!manifestResponse.ok) return json({ error: 'No se pudo verificar la actualización' }, 502);
    const aliases = (await manifestResponse.json()).favorite_aliases || {};
    const { results } = await env.DB.prepare('SELECT * FROM devices WHERE id > ? ORDER BY id LIMIT 20').bind(cursor).all();
    let sent = 0, failed = 0;
    for (const device of results) {
      const favorites = new Set(JSON.parse(device.favorites).map(id => aliases[id] || id));
      const due = promotions.filter(p => favorites.has(p.id) && isDue(p)).map(p => ({ promo: p, benefit: notificationBenefit(p, device.ueno_level) })).filter(p => p.benefit);
      if (!due.length) continue;
      due.sort((a, b) => parseInt(b.benefit) - parseInt(a.benefit));
      const deliveryKey = `${device.id}:${todayParts().iso}`;
      const reservation = await env.DB.prepare("INSERT OR IGNORE INTO deliveries (key, status, created_at) VALUES (?, 'sending', ?)")
        .bind(deliveryKey, new Date().toISOString()).run();
      if (!reservation.meta.changes) continue;
      const lines = due.slice(0, 3).map(({ promo, benefit }) => `${promo.merchant_name}: ${benefit} con ${promo.bank}.`);
      try {
        const subscription = JSON.parse(device.subscription);
        if (!validSubscription(subscription)) throw new Error('Invalid stored subscription');
        const payload = await buildPushPayload({ data: { title: 'Tus favoritos tienen beneficios hoy',
          body: lines.join('\n'), url: APP_URL + '?view=favorites', tag: 'payback-' + todayParts().iso }, options: { ttl: 14400 } }, subscription,
        { subject: APP_URL, publicKey: env.VAPID_PUBLIC_KEY, privateKey: env.VAPID_PRIVATE_KEY });
        const delivered = await fetch(subscription.endpoint, { ...payload, redirect: 'error', signal: AbortSignal.timeout(15000) });
        if (delivered.status === 404 || delivered.status === 410) {
          await env.DB.prepare('DELETE FROM devices WHERE id = ?').bind(device.id).run();
        } else if (!delivered.ok) throw new Error('Push rejected');
        else sent++;
        await env.DB.prepare("UPDATE deliveries SET status = 'sent' WHERE key = ?").bind(deliveryKey).run();
      } catch {
        failed++;
        // Keep uncertain deliveries reserved to avoid duplicate alerts on retries.
        await env.DB.prepare("UPDATE deliveries SET status = 'failed' WHERE key = ?").bind(deliveryKey).run();
      }
    }
    return json({ sent, failed, cursor: results.length === 20 ? results.at(-1).id : null });
  }
  return env.ASSETS ? env.ASSETS.fetch(request) : json({ service: 'Payback PY' });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin');
    const ownOrigin = new URL(request.url).origin;
    const allowed = !origin || origin === ownOrigin || origin === 'https://giumontebruno.github.io';
    if (!allowed) return json({ error: 'Origen no permitido' }, 403);
    const headers = { 'Access-Control-Allow-Origin': origin || ownOrigin, 'Vary': 'Origin',
      'Access-Control-Allow-Methods': 'GET, PUT, DELETE, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Authorization, Content-Type' };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });
    try {
      const result = await handle(request, env);
      const response = new Response(result.body, result);
      for (const [name, value] of Object.entries(headers)) response.headers.set(name, value);
      return response;
    } catch { return new Response(JSON.stringify({ error: 'No se pudo completar la operación' }), { status: 500, headers: { ...headers, 'Content-Type': 'application/json' } }); }
  }
};
