const CACHE_NAME = 'tascam-pwa-v6';
const STATIC_ASSETS = [
    '/static/style.css?v=13',
    '/static/app.js?v=11',
    '/static/icons/icon.svg',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap',
    'https://mcorp.no/lib/mcorp-2.0.js',
    'https://cdn.jsdelivr.net/npm/@mcorp/mediasync/dist/basic-mediasync.min.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.filter((name) => name !== CACHE_NAME)
                          .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Clear all caches on logout to prevent serving stale cached / page
    if (url.pathname.startsWith('/logout')) {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((name) => caches.delete(name))
                );
            })
        );
        return; 
    }

    // Bypass cache for API, Auth, Admin, and Audio Streams (Network Only)
    if (url.pathname.startsWith('/api/') || 
        url.pathname.startsWith('/login') || 
        url.pathname.startsWith('/auth') || 
        url.pathname.startsWith('/admin')) {
        return; 
    }

    // Network-First for navigation/HTML so fresh changes are picked up immediately
    if (event.request.mode === 'navigate' || url.pathname === '/') {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
        return;
    }

    // Cache-First strategy for static assets
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            return fetch(event.request);
        })
    );
});