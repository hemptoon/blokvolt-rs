/* BlokVolt service worker (docs/RUNBOOK.md 3.20). Pages and the site's assets always come from the network
   first; the last 40 pages and the assets they used are kept so they open without a connection, and
   /offline.html answers any other page. /api/, /admin/ and other sites are never touched.
   To switch it off for everyone, replace this file with one that calls self.registration.unregister(). */
const CORE = 'bv-core-1', PAGES = 'bv-pages-1', ASSETS = 'bv-assets-1';
const CORE_FILES = ['/offline.html', '/assets/bv.css', '/assets/bv.js', '/assets/favicon.svg', '/assets/app/icon-192.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CORE).then((c) => c.addAll(CORE_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  const keep = [CORE, PAGES, ASSETS];
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => !keep.includes(k)).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

async function trim(name, max) {
  const c = await caches.open(name);
  const ks = await c.keys();
  for (let i = 0; i < ks.length - max; i++) await c.delete(ks[i]);
}

async function networkFirst(req, key, cacheName, max, fallback) {
  try {
    const res = await fetch(req);
    if (res.ok && res.type === 'basic' && !res.redirected) {
      const copy = res.clone();
      caches.open(cacheName).then((c) => c.put(key, copy)).then(() => trim(cacheName, max)).catch(() => {});
    }
    return res;
  } catch (err) {
    const hit = await caches.match(key, { ignoreSearch: cacheName === PAGES });
    if (hit) return hit;
    if (fallback) {
      const off = await caches.match(fallback);
      if (off) return off;
    }
    throw err;
  }
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin')) return;
  if (req.mode === 'navigate') {
    e.respondWith(networkFirst(req, url.origin + url.pathname, PAGES, 40, '/offline.html'));
  } else if (url.pathname.startsWith('/assets/')) {
    e.respondWith(networkFirst(req, req, ASSETS, 150));
  }
});
