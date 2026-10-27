/* Network-first shell, and NEVER cache outage data; stale forecasts are safety-sensitive. */
const SHELL_CACHE = "nashe-svitlo-static-v13";
const STATIC = ["./", "./favicon.svg", "./touch-bulb-v2.png", "./manifest.webmanifest", "./ecoflow.css", "./ecoflow.js"];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(SHELL_CACHE).then(cache => cache.addAll(STATIC)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key !== SHELL_CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.endsWith("/data.json")) {
    // Always fetch real schedule data from the network, including within the installed iPhone app.
    event.respondWith(fetch(request, {cache: "no-store"}));
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).then(response => {
        if (response.ok) {
          const copy = response.clone();
          event.waitUntil(caches.open(SHELL_CACHE).then(cache => cache.put("./", copy)));
        }
        return response;
      }).catch(async () => (await caches.match("./")) || Response.error())
    );
    return;
  }
  if (STATIC.some(path => url.pathname.endsWith(path.slice(1)))) {
    event.respondWith(caches.match(request).then(cached => cached || fetch(request)));
  }
});
