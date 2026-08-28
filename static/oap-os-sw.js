"use strict";

const CACHE_VERSION = "oap-os-public-v0.1";
const PUBLIC_SHELL = Object.freeze([
  "/offline",
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

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(PUBLIC_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key.startsWith("oap-os-") && key !== CACHE_VERSION)
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  if (isPrivatePath(url.pathname)) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match("/offline"))
    );
    return;
  }

  if (!PUBLIC_SHELL.includes(url.pathname)) return;
  event.respondWith(
    caches.match(url.pathname).then((cached) => cached || fetch(request))
  );
});
