const CACHE_NAME = 'tascam-pwa-v2';
const STATIC_ASSETS = [
    '/static/style.css?v=10',
    '/static/app.js?v=5',
    '/static/icons/icon.svg',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap',
    'https://cdn.mcorp.no/mcorp.js',
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

    // Bypass cache for API, Auth, Admin, and Audio Streams (Network Only)
    if (url.pathname.startsWith('/api/') || 
        url.pathname.startsWith('/login') || 
        url.pathname.startsWith('/logout') ||
        url.pathname.startsWith('/auth') ||
        url.pathname.startsWith('/admin')) {
        return; 
    }

    // Cache-First strategy for the UI Shell
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            return fetch(event.request);
        })
    );
});