(() => {
  "use strict";

  const app = document.querySelector("[data-linkup-app]");
  if (!app || !document.querySelector('meta[name="oap-csrf-token"]')) return;

  let started = false;
  const scripts = [
    "/static/linkup_presence.js",
    "/static/linkup_voice.js",
    "/static/linkup_share.js",
  ];

  const loadScript = (src) =>
    new Promise((resolve, reject) => {
      if (document.querySelector(`script[data-oap-optional-src="${src}"]`)) {
        resolve();
        return;
      }
      const script = document.createElement("script");
      script.src = src;
      script.defer = true;
      script.dataset.oapOptionalSrc = src;
      script.addEventListener("load", resolve, { once: true });
      script.addEventListener("error", reject, { once: true });
      document.head.appendChild(script);
    });

  const start = () => {
    if (started) return;
    started = true;
    Promise.allSettled(scripts.map(loadScript)).then((results) => {
      if (results.some((result) => result.status === "rejected")) {
        app.dataset.optionalRuntime = "degraded";
        return;
      }
      app.dataset.optionalRuntime = "ready";
    });
  };

  window.addEventListener("oap:linkup-engaged", start, { once: true });
  app.addEventListener("pointerdown", start, { once: true, passive: true });
  app.addEventListener("keydown", start, { once: true });

  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(start, { timeout: 3500 });
  } else {
    window.setTimeout(start, 2500);
  }
})();