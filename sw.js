const CACHE = 'ifrs-guide-v36';

const ASSETS = [
  './',
  './index.html',
  './private-sector.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
  './assets/logo.svg',
  './assets/share.jpg',
  './fonts/tajawal-arabic-400-normal.woff2',
  './fonts/tajawal-arabic-500-normal.woff2',
  './fonts/tajawal-arabic-700-normal.woff2',
  './fonts/tajawal-latin-400-normal.woff2',
  './fonts/tajawal-latin-500-normal.woff2',
  './fonts/tajawal-latin-700-normal.woff2'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(ASSETS); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.map(function (k) {
          return k === CACHE ? null : caches.delete(k);
        }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== self.location.origin) return;

  // طلب تنقّل (فتح صفحة): الشبكة أولاً بمهلة 3 ثوانٍ، ثم الذاكرة
  if (req.mode === 'navigate') {
    e.respondWith(
      Promise.race([
        fetch(req).then(function (res) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
          return res;
        }),
        new Promise(function (resolve) {
          setTimeout(function () {
            resolve(caches.match(req, { ignoreSearch: true }).then(function (hit) {
              return hit || caches.match('./index.html');
            }));
          }, 3000);
        })
      ]).catch(function () {
        // the installed app launches with ?source=pwa while the precached page
        // has no query, so navigation lookups must ignore the query string
        return caches.match(req, { ignoreSearch: true }).then(function (hit) {
          return hit || caches.match('./index.html');
        });
      })
    );
    return;
  }

  // باقي الأصول: الذاكرة أولاً
  e.respondWith(
    caches.match(req).then(function (hit) {
      return hit || fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
        return res;
      });
    })
  );
});
