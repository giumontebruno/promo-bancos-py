// This beta intentionally keeps no CacheStorage. The main app has legacy global cleanup.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  if (event.request.mode !== 'navigate') return;
  event.respondWith(fetch(event.request).catch(() => new Response('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>paybackpy beta</title><body style="font:18px system-ui;padding:24px"><h1>Estás sin conexión</h1><p>Esta beta necesita conexión para comprobar tu sesión y cargar promociones.</p><button style="min-height:44px" onclick="location.reload()">Reintentar</button></body></html>', { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } })));
});
