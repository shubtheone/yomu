const CACHE_NAME = 'yomu-cache-v11';
const URLS_TO_CACHE = [
    './',
    './index.html',
    './style.css',
    './app.js',
    './manifest.json',
    './icon.svg',
    './library.json',
    './dict.json',
    './grammar.json',
    './rashomon.json',
    './kumo_no_ito.json',
    './hashire_melos.json',
    './chumon.json',
    './hana.json',
    './yume_juuya.json',
    './ningen_shikkaku.json',
    './takasebune.json'
];

// Install: pre-cache all assets
self.addEventListener('install', event => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching app shell');
                return cache.addAll(URLS_TO_CACHE);
            })
    );
});

// Activate: clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: Network-first for HTML/JSON, Cache-first for CSS/JS/images
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // Skip external requests (like Google Fonts CDN)
    if (url.origin !== location.origin) {
        // For Google Fonts, try network then cache
        if (url.hostname.includes('googleapis.com') || url.hostname.includes('gstatic.com')) {
            event.respondWith(
                caches.match(event.request).then(cached => {
                    const fetched = fetch(event.request).then(response => {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                        return response;
                    }).catch(() => cached);
                    return cached || fetched;
                })
            );
        }
        return;
    }

    // For app shell files: stale-while-revalidate
    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            const fetchPromise = fetch(event.request).then(networkResponse => {
                // Update cache with fresh response
                if (networkResponse && networkResponse.status === 200) {
                    const clone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, clone);
                    });
                }
                return networkResponse;
            }).catch(() => {
                // Network failed, return cached if available
                return cachedResponse;
            });

            // Return cached version immediately, update in background
            return cachedResponse || fetchPromise;
        })
    );
});
