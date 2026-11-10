"use strict";

const CACHE_VERSION = "oap-os-public-v1.2-staged";
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

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key.startsWith("oap-os-") && key !== CACHE_VERSION)
          .map((key) => caches.delete(key))
      ))
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  if (isPrivatePath(url.pathname)) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => url.pathname === "/koradaso"
        ? caches.match("/koradaso").then((cached) => cached || caches.match("/offline"))
        : caches.match("/offline"))
    );
    return;
  }

  if (!PUBLIC_SHELL.includes(url.pathname)) return;
  event.respondWith(
    caches.match(url.pathname).then((cached) => cached || fetch(request))
  );
});
