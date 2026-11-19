// Official navigation stays fresh without purging caches used by other apps on this origin.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  if (event.request.mode !== 'navigate') return;
  event.respondWith(fetch(event.request).catch(() => new Response('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Payback PY</title><body style="font:18px system-ui;padding:24px"><h1>Estás sin conexión</h1><p>Payback necesita conexión para comprobar tu sesión y cargar promociones.</p><button style="min-height:44px" onclick="location.reload()">Reintentar</button></body></html>', { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } })));
});

self.addEventListener('push', event => {
  let data = {};
  try { data = event.data?.json() || {}; } catch { /* A malformed push still gets a safe notification. */ }
  event.waitUntil(self.registration.showNotification(data.title || 'Payback PY', {
    body: String(data.body || 'Consultá tus beneficios de hoy.').slice(0, 600),
    icon: './assets/logos/pase/icon-192.png',
    tag: data.tag || 'payback-favorites',
    data: { url: './?view=favorites' },
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = new URL('./?view=favorites', self.registration.scope).href;
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async clients => {
    const client = clients.find(client => client.url.startsWith(self.registration.scope));
    if (client) { await client.navigate(target); return client.focus(); }
    return self.clients.openWindow(target);
  }));
});
