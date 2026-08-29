"use strict";

(() => {
  const shell = document.querySelector("[data-oap-map]");
  if (!shell) return;

  const button = shell.querySelector("[data-oap-map-load]");
  const status = shell.querySelector("[data-oap-map-status]");
  if (!button || !status) return;

  button.addEventListener("click", () => {
    try {
      const mapUrl = new URL(shell.dataset.mapUrl || "", window.location.origin);
      const approved = mapUrl.protocol === "https:"
        && mapUrl.hostname === "www.openstreetmap.org"
        && mapUrl.pathname === "/export/embed.html";
      if (!approved) throw new Error("unapproved_map_url");

      const frame = document.createElement("iframe");
      frame.title = "OpenStreetMap orientation for the Notting Hill Carnival area";
      frame.loading = "lazy";
      frame.referrerPolicy = "no-referrer";
      frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-popups");
      frame.src = mapUrl.toString();
      shell.replaceChildren(frame);
    } catch (_error) {
      status.textContent = "The optional street map could not be loaded safely.";
      button.disabled = true;
    }
  });
})();
