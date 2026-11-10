/* First-party KORADASO public shell update checks only.
 * Detects published code; never authorizes deployment, model or OS upgrades. */
(() => {
  "use strict";
  if (!("serviceWorker" in navigator) || !window.isSecureContext) return;
  const periodMs = 15 * 60 * 1000;
  const currentRelease = document.documentElement.dataset.koradasoRelease || "";
  let registration;
  let refreshing = false;
  let pendingRelease = false;
  let checking = false;

  const isIdle = () => {
    const input = document.querySelector("#studio-input, #address");
    const messages = document.getElementById("messages");
    // Empty but focused composer is still active: don't interrupt typing.
    return (!input || (document.activeElement !== input && !input.value.trim()))
      && (!messages || !messages.children.length);
  };
  const updateStatus = status => {
    // Non-sensitive status only: no message text, identities or browsing history.
    document.documentElement.dataset.koradasoUpdate = status;
  };
  const applyWhenIdle = () => {
    if (!pendingRelease || refreshing || !isIdle()) return;
    if (document.visibilityState !== "visible" || !navigator.onLine) return;
    // A waiting worker must not be forced onto another active OAP client.
    // Keep this page usable until the browser activates it naturally.
    if (registration && registration.waiting) {
      updateStatus("pending");
      return;
    }
    refreshing = true;
    updateStatus("refreshing");
    window.location.reload();
  };
  const check = async () => {
    if (!navigator.onLine || document.visibilityState !== "visible" || checking) return;
    checking = true;
    try {
      // A worker update alone does not detect changed HTML or server templates.
      if (registration) await registration.update();
      const response = await fetch("/koradaso/release", {
        method: "GET", cache: "no-store", credentials: "same-origin",
        redirect: "error"
      });
      if (!response.ok) throw new Error("public_release_unavailable");
      const payload = await response.json();
      if (!/^[a-f0-9]{20}$/.test(payload.release)) throw new Error("invalid_public_release");
      if (currentRelease && payload.release !== currentRelease) {
        pendingRelease = true;
        updateStatus("pending");
      } else if (!pendingRelease) {
        updateStatus("current");
      }
      applyWhenIdle();
    } catch (_) {
      updateStatus("unknown");
      // Fail safely: keep the current public shell and retry at the next check.
    } finally {
      checking = false;
    }
  };
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    // Existing worker may activate in the background. Only page reload is deferred;
    // full cross-client worker staging is a separate release-safety gate.
    pendingRelease = true;
    updateStatus("pending");
    applyWhenIdle();
  });
  document.addEventListener("input", applyWhenIdle);
  document.addEventListener("focusout", applyWhenIdle);
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js", {scope: "/"})
      .then(found => {registration = found; check();})
      .catch(() => {updateStatus("unknown"); check();});
  });
  window.addEventListener("online", check);
  document.addEventListener("visibilitychange", () => {check(); applyWhenIdle();});
  window.setInterval(check, periodMs);
})();
