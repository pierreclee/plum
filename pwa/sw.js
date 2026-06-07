const CACHE_NAME = 'plum-v1';
const FEED_PATTERN = /\/api\/feed/;

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (!FEED_PATTERN.test(event.request.url)) return;

  event.respondWith(
    fetch(event.request.clone())
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        self.clients.matchAll().then((clients) =>
          clients.forEach((c) => c.postMessage({ type: 'OFFLINE' }))
        );
        return caches.match(event.request);
      })
  );
});
