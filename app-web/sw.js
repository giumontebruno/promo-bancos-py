const CACHE_NAME = "payback-py-v20260909-premium";
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./benefit-rules.js",
  "./push-client.js",
  "./premium.css",
  "./config.js",
  "./manifest.webmanifest",
  "./assets/logos/payback-py-wordmark.png",
  "./assets/logos/payback-py-icon-192.png",
  "./assets/logos/payback-py-icon-512.png",
  "../public/promotions.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname.includes('/api/') || url.pathname.endsWith('/notifications-config.json')) return;
  const cacheKey = url.origin + url.pathname;

  if (event.request.mode === "navigate" || url.pathname.endsWith("/app-web/index.html")) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (!response.ok) throw new Error('Navigation unavailable');
          const copy = response.clone();
          event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(cacheKey, copy)));
          return response;
        })
        .catch(async () => await caches.match(cacheKey) || await caches.match('./index.html') || Response.error())
    );
    return;
  }

  if (url.pathname.endsWith("/public/promotions.json") || url.pathname.endsWith("/public/locations.json")) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (!response.ok) throw new Error('Data unavailable');
          const copy = response.clone();
          event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(cacheKey, copy)));
          return response;
        })
        .catch(async () => await caches.match(cacheKey) || Response.error())
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request).catch(async () => await caches.match(cacheKey) || Response.error()))
  );
});

self.addEventListener('push', event => {
  let data = {};
  try { data = event.data?.json() || {}; } catch { /* A malformed push still gets a safe notification. */ }
  event.waitUntil(self.registration.showNotification(data.title || 'Payback PY', {
    body: String(data.body || 'Consultá tus beneficios de hoy.').slice(0, 600),
    icon: './assets/logos/payback-py-icon-192.png',
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
