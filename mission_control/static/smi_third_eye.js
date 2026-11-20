(() => {
  "use strict";

  // Third Eye is one Founder-private tool inside the existing SMI chat.
  // No location, camera, video, microphone or background requests are made here.
  function boot() {
    if (document.getElementById("smi-third-eye-menu-button")) return;
    const menu = document.getElementById("attach-menu");
    const strip = document.getElementById("interaction-strip");
    const config = window.OAP_SMI_UI || {};
    if (!menu || !strip || !config.thirdEyeStatusUrl || !config.thirdEyeEarthquakesUrl) return;

    const menuButton = document.createElement("button");
    menuButton.id = "smi-third-eye-menu-button";
    menuButton.type = "button";
    menuButton.className = "attach-option";
    menuButton.textContent = "🌍 Third Eye · Earth Intelligence";
    const anchor = document.getElementById("faceup-menu-button");
    if (anchor && anchor.parentNode === menu) anchor.insertAdjacentElement("afterend", menuButton);
    else menu.appendChild(menuButton);

    const drawer = document.createElement("section");
    drawer.id = "smi-third-eye-panel";
    drawer.className = "smi-faceup-drawer";
    drawer.setAttribute("aria-label", "SMI Third Eye Earth Intelligence");
    drawer.hidden = true;
    drawer.innerHTML = `
      <div class="smi-faceup-head">
        <div><strong>🌍 SMI Third Eye</strong><small>Earth Intelligence · Founder-private · Real source evidence</small></div>
        <button type="button" class="smi-faceup-close" id="smi-third-eye-close" aria-label="Close Third Eye">×</button>
      </div>
      <p class="smi-faceup-truth">Observed Earth data only. The aircraft, public cameras, satellites and 3D globe are not yet connected here. SMI Face Up remains the existing permission-controlled phone-camera view.</p>
      <div class="smi-faceup-controls">
        <button type="button" class="tool-btn" id="smi-third-eye-refresh">Check Earth observations</button>
        <a class="tool-btn smi-third-eye-map-link" href="/on-any-place">Existing OAP map</a>
      </div>
      <div class="smi-faceup-status" id="smi-third-eye-status" role="status" aria-live="polite">Source not checked.</div>
      <ol class="smi-third-eye-events" id="smi-third-eye-events" aria-label="USGS earthquake observations"></ol>
      <p class="smi-faceup-truth">No automatic recording, tracking or periodic polling. Data are public USGS reports, not live camera images or direct physical observation.</p>
    `;
    strip.insertAdjacentElement("afterend", drawer);

    const status = drawer.querySelector("#smi-third-eye-status");
    const events = drawer.querySelector("#smi-third-eye-events");
    const refresh = drawer.querySelector("#smi-third-eye-refresh");
    const close = drawer.querySelector("#smi-third-eye-close");
    let activeRequest = null;

    const label = (value, empty = "Unknown") =>
      typeof value === "string" && value.trim() ? value.trim() : empty;

    function setStatus(message) {
      status.textContent = message;
    }

    function stopRequest() {
      if (activeRequest) activeRequest.abort();
      activeRequest = null;
      refresh.disabled = false;
    }

    async function readJson(url, signal) {
      const response = await fetch(url, {
        method: "GET",
        credentials: "same-origin",
        cache: "no-store",
        referrerPolicy: "no-referrer",
        signal
      });
      if (!response.ok) throw new Error("unavailable");
      return response.json();
    }

    async function open() {
      drawer.hidden = false;
      menu.classList.remove("show");
      document.getElementById("plus-button")?.setAttribute("aria-expanded", "false");
      setStatus("Checking source availability…");
      const controller = new AbortController();
      activeRequest = controller;
      try {
        const state = await readJson(config.thirdEyeStatusUrl, controller.signal);
        if (drawer.hidden || activeRequest !== controller) return;
        const earthquake = state?.sources?.earthquakes;
        const cameras = state?.sources?.public_cameras;
        if (state?.founder_private_only !== true || cameras?.live_feed_proven !== false) {
          setStatus("Privacy or source state cannot be verified. Third Eye unavailable.");
          refresh.disabled = true;
          return;
        }
        setStatus("USGS · " + label(earthquake?.state, "unchecked") + " · Cameras and 3D globe not connected.");
      } catch (error) {
        if (error?.name !== "AbortError") setStatus("Third Eye status unavailable. No source is verified.");
      } finally {
        if (activeRequest === controller) activeRequest = null;
      }
    }

    async function checkEarth() {
      stopRequest();
      events.replaceChildren();
      refresh.disabled = true;
      setStatus("Checking USGS public observations…");
      const controller = new AbortController();
      activeRequest = controller;
      try {
        const data = await readJson(config.thirdEyeEarthquakesUrl, controller.signal);
        if (drawer.hidden || activeRequest !== controller) return;
        if (data?.feed_verified !== true || !["fresh", "stale"].includes(data?.freshness)) {
          setStatus("USGS feed unavailable · no live claim.");
          return;
        }
        const stamp = label(data.observed_feed_generated_at);
        setStatus("USGS · " + data.freshness + " · feed timestamp " + stamp + " · not live video.");
        const list = Array.isArray(data.events) ? data.events.slice(0, 12) : [];
        for (const item of list) {
          if (item?.source !== "USGS") continue;
          const li = document.createElement("li");
          const mag = typeof item.magnitude === "number" ? "M " + item.magnitude.toFixed(1) : "Magnitude unknown";
          li.textContent = mag + " · " + label(item.place) + " · " + label(item.observed_at);
          events.appendChild(li);
        }
        if (!events.childElementCount) {
          const li = document.createElement("li");
          li.textContent = "No valid observations in the returned sample.";
          events.appendChild(li);
        }
      } catch (error) {
        if (error?.name !== "AbortError") setStatus("Earth observations unavailable. No data or live claim inferred.");
      } finally {
        if (activeRequest === controller) {
          activeRequest = null;
          refresh.disabled = false;
        }
      }
    }

    menuButton.addEventListener("click", open);
    refresh.addEventListener("click", checkEarth);
    close.addEventListener("click", () => {
      stopRequest();
      drawer.hidden = true;
    });
    window.addEventListener("pagehide", stopRequest, {once: true});
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, {once: true});
  else boot();
})();
