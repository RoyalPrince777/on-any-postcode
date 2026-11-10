/* First-party KORADASO public shell updater; no model, OS or deploy authority. */
(() => {
  "use strict";
  if (!("serviceWorker" in navigator) || !window.isSecureContext) return;
  const periodMs = 15 * 60 * 1000;
  let registration;
  let refreshing = false;
  const isIdle = () => {
    const input = document.querySelector("#studio-input, #address");
    const messages = document.getElementById("messages");
    return !input?.value.trim() && (!messages || !messages.children.length);
  };
  const check = () => {
    if (!navigator.onLine || document.visibilityState !== "visible" || !registration) return;
    registration.update().catch(() => {});
  };
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    // Never destroy a user's current chat, unsent prompt or search query.
    if (refreshing || !isIdle()) return;
    refreshing = true;
    window.location.reload();
  });
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js", {scope: "/"})
      .then(found => {registration = found; check();})
      .catch(() => {}); // Old public page stays usable if the updater is unavailable.
  });
  window.addEventListener("online", check);
  document.addEventListener("visibilitychange", check);
  window.setInterval(check, periodMs);
})();
