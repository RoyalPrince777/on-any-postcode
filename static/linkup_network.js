(() => {
  "use strict";

  const app = document.querySelector("[data-linkup-app]");
  if (!app) return;

  const status = document.querySelector("[data-oap-linkup-network-status]");
  const guardedSelector = [
    "[data-oap-link-composer]",
    "[data-oap-call-control]",
    "[data-oap-voice-control]",
    "[data-oap-ptt-control]",
    "[data-oap-voice-stop]",
    "[data-oap-share-spot-control]",
    "[data-oap-around-control]",
    "[data-oap-live-spot-control]",
    "[data-oap-live-spot-stop]",
    "[data-oap-now-form]"
  ].join(",");

  const render = () => {
    const online = navigator.onLine;
    app.dataset.network = online ? "online" : "offline";
    if (status) {
      status.dataset.online = online ? "true" : "false";
      status.textContent = online
        ? "Online · Link Up is live"
        : "Offline · private actions paused until you reconnect";
    }
  };

  document.addEventListener("submit", (event) => {
    if (navigator.onLine) return;
    if (!event.target.closest("[data-oap-link-composer], [data-oap-now-form]")) return;
    event.preventDefault();
    render();
  }, true);

  document.addEventListener("click", (event) => {
    if (navigator.onLine) return;
    const guarded = event.target.closest(guardedSelector);
    if (!guarded || guarded.matches("form")) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    render();
  }, true);

  window.addEventListener("online", render);
  window.addEventListener("offline", render);
  render();
})();