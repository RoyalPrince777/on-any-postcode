(() => {
  "use strict";

  // One entry under existing SMI Tools, seven internal Third Eye views.
  // No background polling, inferred live feeds or automatic sensor capture.
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
    menuButton.textContent = "👁️ Third Eye";
    const anchor = document.getElementById("faceup-menu-button");
    if (anchor && anchor.parentNode === menu) anchor.insertAdjacentElement("afterend", menuButton);
    else menu.appendChild(menuButton);

    const views = [
      {id: "earth", icon: "🌍", name: "Earth Vision", state: "3D not connected"},
      {id: "ground", icon: "📷", name: "Ground Vision", state: "London TfL stills · source check required"},
      {id: "air", icon: "✈️", name: "Air Vision", state: "Not connected"},
      {id: "space", icon: "🛰️", name: "Space Vision", state: "Not connected"},
      {id: "environment", icon: "🌦️", name: "Earth Intelligence", state: "USGS check available"},
      {id: "analysis", icon: "🧠", name: "SMI Analysis", state: "Source evidence"},
      {id: "controls", icon: "🔐", name: "Controls", state: "Founder private"}
    ];

    const drawer = document.createElement("section");
    drawer.id = "smi-third-eye-panel";
    drawer.className = "smi-faceup-drawer";
    drawer.setAttribute("aria-label", "SMI Third Eye internal menu");
    drawer.hidden = true;
    drawer.innerHTML = [
      '<header class="smi-third-eye-header">',
      '<div class="smi-third-eye-header-copy"><small class="smi-third-eye-eyebrow">SMI / EARTH INTELLIGENCE</small><strong>👁️ THIRD EYE</strong><span>One world · Seven views · Real evidence</span></div>',
      '<button type="button" class="smi-faceup-close" id="smi-third-eye-close" aria-label="Close Third Eye">×</button>',
      '</header>',
      '<div class="smi-third-eye-boundary" aria-label="Privacy and evidence"><span>🔐 Founder private</span><span>● Truth Mode</span><span>Public feeds only</span></div>',
      '<div id="smi-third-eye-home" class="smi-third-eye-home">',
      '<div class="smi-third-eye-home-title"><strong>Explore the real world</strong><small>Choose a view. Sources appear only when verified.</small></div>',
      '<nav id="smi-third-eye-internal-menu" class="smi-third-eye-menu" aria-label="Inside Third Eye"></nav>',
      '</div>',
      '<section id="smi-third-eye-detail" class="smi-third-eye-detail" hidden aria-labelledby="smi-third-eye-detail-title">',
      '<div class="smi-third-eye-detail-nav"><button type="button" class="tool-btn smi-third-eye-back" id="smi-third-eye-back">← All views</button><small>THIRD EYE / <span id="smi-third-eye-crumb"></span></small></div>',
      '<div class="smi-third-eye-detail-header"><small id="smi-third-eye-detail-state" class="smi-third-eye-detail-state"></small><h3 id="smi-third-eye-detail-title"></h3><p id="smi-third-eye-detail-copy"></p></div>',
      '<div class="smi-third-eye-detail-actions" id="smi-third-eye-detail-actions"></div>',
      '<div id="smi-third-eye-status" class="smi-third-eye-status" role="status" aria-live="polite">Source not checked.</div>',
      '<ol id="smi-third-eye-events" class="smi-third-eye-events" aria-label="Earth observations"></ol>',
      '<div id="smi-third-eye-camera-list" class="smi-third-eye-camera-list" aria-label="TfL London traffic camera selection"></div>',
      '<figure id="smi-third-eye-camera-frame" class="smi-third-eye-camera-frame" hidden><img id="smi-third-eye-camera-image" alt="Selected TfL public traffic camera still" loading="lazy" decoding="async"><figcaption id="smi-third-eye-camera-caption"></figcaption></figure>',
      '</section>',
      '<footer class="smi-third-eye-foot">No hidden tracking · No automatic recording · Founder Final</footer>'
    ].join("");
    strip.insertAdjacentElement("afterend", drawer);

    const home = drawer.querySelector("#smi-third-eye-home");
    const internalMenu = drawer.querySelector("#smi-third-eye-internal-menu");
    const detail = drawer.querySelector("#smi-third-eye-detail");
    const title = drawer.querySelector("#smi-third-eye-detail-title");
    const crumb = drawer.querySelector("#smi-third-eye-crumb");
    const viewState = drawer.querySelector("#smi-third-eye-detail-state");
    const description = drawer.querySelector("#smi-third-eye-detail-copy");
    const actions = drawer.querySelector("#smi-third-eye-detail-actions");
    const status = drawer.querySelector("#smi-third-eye-status");
    const events = drawer.querySelector("#smi-third-eye-events");
    const cameraList = drawer.querySelector("#smi-third-eye-camera-list");
    const cameraFrame = drawer.querySelector("#smi-third-eye-camera-frame");
    const cameraImage = drawer.querySelector("#smi-third-eye-camera-image");
    const cameraCaption = drawer.querySelector("#smi-third-eye-camera-caption");
    let activeRequest = null;
    let requestKind = null;
    let verifiedStatus = false;
    let lastEvidence = null;
    let currentView = null;

    const label = (value, empty = "Unknown") =>
      typeof value === "string" && value.trim() ? value.trim() : empty;

    for (const view of views) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "smi-third-eye-menu-item";
      button.dataset.thirdEyeView = view.id;
      button.setAttribute("aria-label", view.name + ": " + view.state);
      button.setAttribute("aria-haspopup", "false");
      const emoji = document.createElement("span");
      emoji.className = "smi-third-eye-icon";
      emoji.textContent = view.icon;
      const name = document.createElement("strong");
      name.textContent = view.name;
      const state = document.createElement("small");
      state.textContent = view.state;
      const arrow = document.createElement("span");
      arrow.className = "smi-third-eye-menu-arrow";
      arrow.setAttribute("aria-hidden", "true");
      arrow.textContent = "›";
      button.append(emoji, name, state, arrow);
      button.addEventListener("click", () => selectView(view.id));
      internalMenu.appendChild(button);
    }

    function setStatus(message) {
      status.textContent = message;
    }

    function stopRequest(keepStatus = false) {
      if (keepStatus && requestKind === "status") return;
      if (activeRequest) activeRequest.abort();
      activeRequest = null;
      requestKind = null;
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

    function actionButton(text, handler) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "tool-btn smi-third-eye-action";
      button.textContent = text;
      button.addEventListener("click", handler);
      actions.appendChild(button);
      return button;
    }

    function actionLink(text, href) {
      const link = document.createElement("a");
      link.className = "tool-btn smi-third-eye-map-link smi-third-eye-action";
      link.textContent = text;
      link.href = href;
      actions.appendChild(link);
    }

    function selectView(id) {
      stopRequest(true);
      currentView = id;
      const view = views.find(item => item.id === id);
      if (!view) return;
      home.hidden = true;
      detail.hidden = false;
      crumb.textContent = view.name;
      viewState.textContent = view.state;
      viewState.dataset.state = (id === "environment" || id === "ground") ? "partial" : "pending";
      title.textContent = view.icon + " " + view.name;
      description.textContent = "";
      actions.replaceChildren();
      events.replaceChildren();
      cameraList.replaceChildren();
      cameraFrame.hidden = true;
      cameraImage.removeAttribute("src");
      status.hidden = false;
      setStatus(view.state);
      drawer.scrollTop = 0;

      if (id === "earth") {
        description.textContent = "Use the existing On Any Place map. Third Eye does not yet have a verified 3D globe.";
        actionLink("Open existing OAP map", "/on-any-place");
        const refresh = actionButton("Check global earthquakes", checkEarth);
        refresh.id = "smi-third-eye-refresh";
        refresh.disabled = !verifiedStatus;
      } else if (id === "ground") {
        description.textContent = "View London public TfL traffic-camera stills inside SMI or use Face Up for your own phone camera. TfL images generally update every few minutes; this is not continuous video.";
        if (config.thirdEyeLondonCamerasUrl && config.thirdEyeLondonFrameUrl) {
          const search = document.createElement("input");
          search.type = "search";
          search.id = "smi-third-eye-london-place";
          search.className = "smi-third-eye-place";
          search.maxLength = 80;
          search.autocomplete = "off";
          search.placeholder = "Area e.g. Mitcham (blank = central)";
          search.setAttribute("aria-label", "Search TfL public London camera locations");
          actions.appendChild(search);
          const find = actionButton("View London cameras", () => loadLondonCameras(search.value));
          find.disabled = !verifiedStatus;
        }
        actionButton("Open existing Face Up", () => {
          const existing = document.getElementById("faceup-button");
          if (!existing) {
            setStatus("Face Up is unavailable here.");
            return;
          }
          closeDrawer();
          existing.click();
        });
      } else if (id === "air") {
        description.textContent = "No verified aircraft location source is connected to Third Eye.";
      } else if (id === "space") {
        description.textContent = "No orbital source or verified satellite observation is connected to Third Eye.";
      } else if (id === "environment") {
        description.textContent = "Request real public Earth observations. Earthquakes use USGS; weather reuses OAP Ecosystem Intelligence. Neither is a camera or a live satellite image.";
        const refresh = actionButton("Check USGS earthquakes", checkEarth);
        refresh.id = "smi-third-eye-refresh";
        refresh.disabled = !verifiedStatus;
        if (!verifiedStatus) setStatus("Authorised Third Eye status not verified. Observations unavailable.");
        else if (lastEvidence) setStatus(lastEvidence);
        else setStatus("USGS source not yet checked.");
        if (config.thirdEyeWeatherUrl) {
          const placeInput = document.createElement("input");
          placeInput.type = "text";
          placeInput.id = "smi-third-eye-place";
          placeInput.className = "smi-third-eye-place";
          placeInput.value = "London";
          placeInput.maxLength = 70;
          placeInput.autocomplete = "off";
          placeInput.placeholder = "City or postcode";
          placeInput.setAttribute("aria-label", "Choose a place for live weather");
          const weather = actionButton("Check actual weather", () => checkWeather(placeInput.value));
          weather.id = "smi-third-eye-weather";
          weather.disabled = !verifiedStatus;
          actions.insertBefore(placeInput, weather);
        }
      } else if (id === "analysis") {
        description.textContent = "Truth Mode identifies sources, age of observations and what remains unverified. Automated scene analysis is not connected.";
        setStatus(lastEvidence || "No verified Earth observation checked in this session.");
      } else {
        description.textContent = "Founder-only access via existing SMI authentication. No automatic location tracking, camera recording, permission changes or public release.";
        setStatus(verifiedStatus ? "Founder-private source status verified in this session." : "Access/source check not verified.");
      }
    }

    async function open() {
      stopRequest();
      verifiedStatus = false;
      lastEvidence = null;
      currentView = null;
      drawer.hidden = false;
      home.hidden = false;
      detail.hidden = true;
      menu.classList.remove("show");
      document.getElementById("plus-button")?.setAttribute("aria-expanded", "false");
      const controller = new AbortController();
      activeRequest = controller;
      requestKind = "status";
      menuButton.setAttribute("aria-expanded", "true");
      drawer.querySelector("#smi-third-eye-close").focus();
      try {
        const state = await readJson(config.thirdEyeStatusUrl, controller.signal);
        if (drawer.hidden || activeRequest !== controller) return;
        verifiedStatus = state?.founder_private_only === true &&
          state?.sources?.public_cameras?.live_feed_proven === false &&
          state?.sources?.earthquakes?.feed_proven === false;
        if (currentView === "environment" || currentView === "ground") selectView(currentView);
      } catch (error) {
        if (error?.name !== "AbortError") verifiedStatus = false;
      } finally {
        if (activeRequest === controller) {
          activeRequest = null;
          requestKind = null;
        }
      }
    }

    async function checkEarth() {
      if (!verifiedStatus || !["earth", "environment"].includes(currentView)) return;
      stopRequest();
      events.replaceChildren();
      const refresh = drawer.querySelector("#smi-third-eye-refresh");
      if (refresh) refresh.disabled = true;
      setStatus("Checking USGS public observations…");
      const controller = new AbortController();
      activeRequest = controller;
      requestKind = "earth";
      try {
        const data = await readJson(config.thirdEyeEarthquakesUrl, controller.signal);
        if (drawer.hidden || activeRequest !== controller || !["earth", "environment"].includes(currentView)) return;
        if (data?.feed_verified !== true || !["fresh", "stale"].includes(data?.freshness)) {
          setStatus("USGS feed unavailable · no live claim.");
          lastEvidence = null;
          return;
        }
        const stamp = label(data.observed_feed_generated_at);
        lastEvidence = "USGS · " + data.freshness + " · feed timestamp " + stamp + " · not live video.";
        setStatus(lastEvidence);
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
        if (error?.name !== "AbortError") {
          lastEvidence = null;
          setStatus("Earth observations unavailable. No data or live claim inferred.");
        }
      } finally {
        if (activeRequest === controller) {
          activeRequest = null;
          requestKind = null;
          if (refresh) refresh.disabled = false;
        }
      }
    }


    async function checkWeather(rawPlace) {
      if (!verifiedStatus || currentView !== "environment" || !config.thirdEyeWeatherUrl) return;
      const place = label(rawPlace, "").slice(0, 70);
      if (place.length < 2) {
        setStatus("Enter a valid city or postcode to check weather.");
        return;
      }
      stopRequest();
      events.replaceChildren();
      const button = drawer.querySelector("#smi-third-eye-weather");
      if (button) button.disabled = true;
      setStatus("Checking OAP Ecosystem Intelligence weather for " + place + "…");
      const controller = new AbortController();
      activeRequest = controller;
      requestKind = "weather";
      try {
        const url = new URL(config.thirdEyeWeatherUrl, window.location.origin);
        if (url.origin !== window.location.origin) throw new Error("cross_origin_blocked");
        url.searchParams.set("location", place);
        const data = await readJson(url.toString(), controller.signal);
        if (drawer.hidden || currentView !== "environment" || activeRequest !== controller) return;
        const signal = Array.isArray(data?.analysis?.signals)
          ? data.analysis.signals.find(item => item?.source === "oap_weather_live_source" && item?.domain === "nature")
          : null;
        const observation = signal?.observation;
        if (data?.weather_environment_proven !== true || !observation?.observed_at) {
          lastEvidence = null;
          setStatus("Weather source not verified. No live claim.");
          return;
        }
        const freshness = label(observation.freshness_state, "unknown");
        const live = observation.live_claim_allowed === true && freshness === "fresh";
        const source = label(observation.source, "OAP weather provider");
        const at = label(observation.observed_at);
        const placeName = label(data.location_query, place);
        lastEvidence = (live ? "Observed" : "Not currently live") +
          " · " + source.slice(0, 70) + " · " + placeName.slice(0, 70) +
          " · " + freshness + " · observed " + at;
        setStatus(lastEvidence);
        const li = document.createElement("li");
        li.textContent = label(signal.summary, "Weather details unavailable").slice(0, 220);
        events.appendChild(li);
      } catch (error) {
        if (error?.name !== "AbortError") {
          lastEvidence = null;
          setStatus("Weather provider unavailable. No live claim.");
        }
      } finally {
        if (activeRequest === controller) {
          activeRequest = null;
          requestKind = null;
          if (button) button.disabled = false;
        }
      }
    }


    async function loadLondonCameras(rawSearch) {
      if (!verifiedStatus || currentView !== "ground" || !config.thirdEyeLondonCamerasUrl) return;
      stopRequest();
      cameraList.replaceChildren();
      cameraFrame.hidden = true;
      cameraImage.removeAttribute("src");
      const query = label(rawSearch, "").slice(0, 80);
      const controller = new AbortController();
      activeRequest = controller;
      requestKind = "london";
      try {
        const url = new URL(config.thirdEyeLondonCamerasUrl, window.location.origin);
        if (url.origin !== window.location.origin) throw new Error("cross_origin_blocked");
        if (query) url.searchParams.set("q", query);
        setStatus("Checking public TfL London road cameras…");
        const data = await readJson(url.toString(), controller.signal);
        if (drawer.hidden || currentView !== "ground" || activeRequest !== controller) return;
        if (data?.source_verified !== true || data?.provider !== "Transport for London (TfL)") {
          setStatus("TfL camera catalogue unavailable. No live camera claim.");
          return;
        }
        const list = Array.isArray(data.cameras) ? data.cameras.slice(0, 12) : [];
        for (const cam of list) {
          if (!/^\d{5}\.\d{5}$/.test(cam?.id) || typeof cam?.name !== "string") continue;
          const button = document.createElement("button");
          button.type = "button";
          button.className = "smi-third-eye-camera-button";
          button.textContent = "📷 " + cam.name.slice(0, 100);
          button.addEventListener("click", () => showLondonCamera(cam));
          cameraList.appendChild(button);
        }
        setStatus(cameraList.childElementCount
          ? "TfL camera locations received. Choose a public road camera to request its latest still."
          : "No available TfL cameras match that London area.");
        const attribution = document.createElement("a");
        attribution.textContent = "Powered by TfL Open Data · Terms";
        attribution.href = "https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service";
        attribution.target = "_blank";
        attribution.rel = "noopener noreferrer";
        attribution.className = "smi-third-eye-attribution";
        cameraList.appendChild(attribution);
      } catch (error) {
        if (error?.name !== "AbortError") {
          setStatus("TfL source unavailable. Live London camera images not verified.");
        }
      } finally {
        if (activeRequest === controller) {
          activeRequest = null;
          requestKind = null;
        }
      }
    }

    function showLondonCamera(camera) {
      if (currentView !== "ground" || drawer.hidden || !config.thirdEyeLondonFrameUrl) return;
      const id = String(camera.id || "");
      if (!/^\d{5}\.\d{5}$/.test(id)) return;
      const base = new URL(
        config.thirdEyeLondonFrameUrl.replace("__CAMERA_ID__", encodeURIComponent(id)),
        window.location.origin
      );
      if (base.origin !== window.location.origin) return;
      base.searchParams.set("requested_at", String(Date.now()));
      cameraFrame.hidden = false;
      cameraCaption.textContent = camera.name.slice(0, 100) + " · Powered by TfL Open Data · Capture time not supplied";
      setStatus("Loading selected TfL camera still through SMI…");
      cameraImage.onload = () => {
        if (!drawer.hidden && currentView === "ground") {
          setStatus("TfL road camera image received. Exact capture time unknown; not continuous live video.");
        }
      };
      cameraImage.onerror = () => {
        if (!drawer.hidden && currentView === "ground") {
          setStatus("Camera image currently unavailable. No live claim.");
        }
      };
      cameraImage.src = base.toString();
      cameraFrame.scrollIntoView({block: "nearest", behavior: "auto"});
    }

    function closeDrawer() {
      stopRequest();
      drawer.hidden = true;
      menuButton.setAttribute("aria-expanded", "false");
      menuButton.focus();
    }

    drawer.querySelector("#smi-third-eye-back").addEventListener("click", () => {
      stopRequest(true);
      currentView = null;
      detail.hidden = true;
      home.hidden = false;
      drawer.scrollTop = 0;
      internalMenu.querySelector("button")?.focus();
    });
    drawer.addEventListener("keydown", event => {
      if (event.key === "Escape" && !drawer.hidden) {
        event.preventDefault();
        closeDrawer();
      }
    });
    drawer.querySelector("#smi-third-eye-close").addEventListener("click", closeDrawer);
    menuButton.setAttribute("aria-controls", "smi-third-eye-panel");
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.addEventListener("click", open);
    window.addEventListener("pagehide", stopRequest, {once: true});
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, {once: true});
  else boot();
})();
