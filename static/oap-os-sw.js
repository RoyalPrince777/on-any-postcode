"use strict";

const CACHE_VERSION = "oap-os-public-__KORADASO_RELEASE__";
const PUBLIC_SHELL = Object.freeze([
  "/offline",
  "/koradaso",
  "/static/oap/koradaso_internet_logo.jpg",
  "/manifest.webmanifest",
  "/assets/oap.css",
  "/assets/oap-os.js",
  "/assets/oap-os-icon-192.png",
  "/assets/oap-os-icon-512.png"
]);
const PRIVATE_PREFIXES = Object.freeze([
  "/auth",
  "/enter-my-world",
  "/my-world",
  "/mission",
  "/infrastructure"
]);

const isPrivatePath = (pathname) => PRIVATE_PREFIXES.some(
  (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
);

// Stage updates: do not force a waiting worker onto open Link Up or SMI clients.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(PUBLIC_SHELL))
      .catch((error) => {
        // Installation fails; do not delete a cache possibly shared with the
        // current active worker. A fully isolated staging cache is still unproven.
        throw error;
      })
  );
});

// Retain the latest previous public shell for bounded offline recovery.
// Cache keys are returned in creation order: keep the newest prior cache,
// rather than deleting the only possible recovery point on activation.
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      const previous = keys.filter(
        (key) => key.startsWith("oap-os-public-") && key !== CACHE_VERSION
      );
      return Promise.all(previous.slice(0, -1).map((key) => caches.delete(key)));
    })
  );
});

// Prefer the current release. Older public cache is only a fallback if the
// current shell asset is missing, never a way to override a working update.
async function publicShellFallback(pathname) {
  const current = await caches.open(CACHE_VERSION);
  const fresh = await current.match(pathname);
  if (fresh) return fresh;
  const keys = await caches.keys();
  const previous = keys.filter(
    (key) => key.startsWith("oap-os-public-") && key !== CACHE_VERSION
  );
  if (previous.length) {
    const lastGood = await caches.open(previous[previous.length - 1]);
    const cached = await lastGood.match(pathname);
    if (cached) return cached;
  }
  return caches.match("/offline");
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  if (isPrivatePath(url.pathname)) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => url.pathname === "/koradaso"
        ? publicShellFallback("/koradaso")
        : publicShellFallback("/offline"))
    );
    return;
  }

  if (!PUBLIC_SHELL.includes(url.pathname)) return;
  event.respondWith(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.match(url.pathname))
      .then((cached) => cached || fetch(request))
  );
});
