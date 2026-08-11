const CACHE_NAME = "vitalia-shell-v1";

const APP_SHELL = [
  "/",
  "/campanhas",
  "/quem-somos",
  "/cada-gota-conta",
  "/seja-doadora",
  "/localizador",
  "/static/css/style.css",
  "/static/js/localizador.js",
  "/static/js/doadora.js",
  "/static/js/pwa-register.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== "GET") {
    return; // nunca intercepta POST (formulários, envio de doadora, etc.)
  }

  if (url.pathname.startsWith("/api/")) {
    // network-first, sem fallback em cache — dados do localizador devem ficar sempre atuais
    event.respondWith(fetch(request).catch(() => new Response("[]", { status: 503 })));
    return;
  }

  if (request.mode === "navigate" || url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.open(CACHE_NAME).then(async (cache) => {
        const cached = await cache.match(request);
        const network = fetch(request)
          .then((resp) => {
            if (resp.ok) cache.put(request, resp.clone());
            return resp;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
  }
});
