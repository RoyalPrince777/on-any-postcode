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
      {id: "air", icon: "✈️", name: "Air Vision", state: "Public ADS-B check · unverified"},
      {id: "space", icon: "🛰️", name: "Space Vision", state: "NASA imagery · ISS sources · unverified"},
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
      '<figure id="smi-third-eye-camera-frame" class="smi-third-eye-camera-frame" hidden><img id="smi-third-eye-camera-image" alt="Selected TfL public traffic camera still" loading="lazy" decoding="async"><video id="smi-third-eye-camera-video" controls playsinline preload="none" hidden aria-label="TfL rolling London traffic video clip"></video><button type="button" class="tool-btn smi-third-eye-play" id="smi-third-eye-play" hidden>▶ Play TfL rolling clip</button><figcaption id="smi-third-eye-camera-caption"></figcaption></figure>',
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
    const cameraVideo = drawer.querySelector("#smi-third-eye-camera-video");
    const cameraPlay = drawer.querySelector("#smi-third-eye-play");
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

    function clearCameraMedia() {
      cameraImage.onload = null;
      cameraImage.onerror = null;
      cameraImage.removeAttribute("src");
      cameraImage.hidden = false;
      cameraVideo.pause();
      cameraVideo.removeAttribute("src");
      cameraVideo.load();
      cameraVideo.hidden = true;
      cameraPlay.hidden = true;
      cameraPlay.onclick = null;
    }

    function selectView(id) {
      stopRequest(true);
      clearCameraMedia();
      currentView = id;
      const view = views.find(item => item.id === id);
      if (!view) return;
      home.hidden = true;
      detail.hidden = false;
      crumb.textContent = view.name;
      viewState.textContent = view.state;
      viewState.dataset.state = ["environment", "ground", "air", "space"].includes(id) ? "partial" : "pending";
      title.textContent = view.icon + " " + view.name;
      description.textContent = "";
      actions.replaceChildren();
      events.replaceChildren();
      cameraList.replaceChildren();
      cameraFrame.hidden = true;
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
        description.textContent = "Start at CR4 · Mitcham, view nearby public TfL road cameras first, then explore every available TfL London camera. Still images and short clips are periodically updated, not continuous live video.";
        if (config.thirdEyeLondonCamerasUrl && config.thirdEyeLondonFrameUrl) {
          const search = document.createElement("input");
          search.type = "search";
          search.id = "smi-third-eye-london-place";
          search.className = "smi-third-eye-place";
          search.maxLength = 80;
          search.autocomplete = "off";
          search.placeholder = "CR4 first · search a road or area";
          search.value = "CR4";
          search.setAttribute("aria-label", "Search TfL public London camera locations");
          actions.appendChild(search);
          const radius = document.createElement("select");
          radius.id = "smi-third-eye-london-radius";
          radius.className = "smi-third-eye-place";
          radius.setAttribute("aria-label", "Choose CR4 vicinity or whole London");
          for (const [value, text] of [
            ["0", "All London · nearest CR4 first"],
            ["5", "Within 5 km of CR4"],
            ["15", "Within 15 km of CR4"],
            ["30", "Within 30 km of CR4"]
          ]) {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = text;
            radius.appendChild(option);
          }
          actions.appendChild(radius);
          const browse = (page = 1) => loadLondonCameras(search.value, page, Number(radius.value));
          const find = actionButton("View London cameras", () => browse());
          find.disabled = !verifiedStatus;
          radius.addEventListener("change", () => browse());
          search.addEventListener("keydown", event => {
            if (event.key === "Enter") browse();
          });
          if (verifiedStatus) browse();
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
        description.textContent = "Check public ADS-B aircraft reports for the London/CR4 area on demand. Position timestamps, coverage limits and provider credit shown. This is not a camera.";
        if (config.thirdEyeAirLondonUrl) {
          const check = actionButton("Check London aircraft reports", checkLondonAir);
          check.disabled = !verifiedStatus;
        }
        setStatus(verifiedStatus ? "Aircraft source not checked in this session." : "Founder status not verified.");
      } else if (id === "space") {
        description.textContent = "NASA daily London imagery, reported ISS position and CelesTrak orbital elements are separate on-demand sources. Imagery is not live video or guaranteed current-day capture.";
        if (config.thirdEyeSpaceIssUrl) {
          const iss = actionButton("Check ISS position", () => checkSpaceSource("iss"));
          iss.disabled = !verifiedStatus;
        }
        if (config.thirdEyeSpaceOrbitUrl) {
          const orbit = actionButton("Check ISS orbit elements", () => checkSpaceSource("orbit"));
          orbit.disabled = !verifiedStatus;
        }
        if (config.thirdEyeSpaceImageryUrl) {
          const dayInput = document.createElement("input");
          dayInput.id = "smi-third-eye-nasa-date";
          dayInput.className = "smi-third-eye-place";
          dayInput.type = "date";
          dayInput.setAttribute("aria-label", "Select a past day for NASA London imagery");
          const utcDay = new Date(Date.now() - 2 * 86400000).toISOString().slice(0, 10);
          dayInput.value = utcDay;
          dayInput.max = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
          dayInput.min = "2000-01-01";
          actions.appendChild(dayInput);
          const image = actionButton("Request NASA London imagery", () => showNasaLondonImage(dayInput.value));
          image.disabled = !verifiedStatus;
        }
        setStatus(verifiedStatus ? "No orbital or imagery source checked yet." : "Founder status not verified.");
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
        if (["environment", "ground", "air", "space"].includes(currentView)) selectView(currentView);
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


    function appendTruthRow(value) {
      const row = document.createElement("li");
      row.textContent = String(value).slice(0, 360);
      events.appendChild(row);
    }

    async function checkLondonAir() {
      if (!verifiedStatus || currentView !== "air" || !config.thirdEyeAirLondonUrl) return;
      stopRequest();
      events.replaceChildren();
      setStatus("Requesting public ADS-B London source…");
      const controller = new AbortController();
      activeRequest = controller;
      requestKind = "air";
      try {
        const data = await readJson(config.thirdEyeAirLondonUrl, controller.signal);
        if (drawer.hidden || activeRequest !== controller || currentView !== "air") return;
        if (data?.provider !== "adsb.lol" || !Array.isArray(data.positions) || !["fresh", "stale"].includes(data.freshness)) {
          setStatus("London ADS-B source unavailable. Aircraft positions unverified.");
          return;
        }
        const fresh = data.live_claim_allowed === true && data.freshness === "fresh";
        lastEvidence = "adsb.lol · " + (fresh ? "fresh reports" : "stale/unverified") +
          " · source " + label(data.provider_timestamp) +
          " · public receiver coverage incomplete · ODbL 1.0";
        setStatus(lastEvidence);
        for (const plane of data.positions.slice(0, 20)) {
          if (!Number.isFinite(plane?.latitude) || !Number.isFinite(plane?.longitude)) continue;
          appendTruthRow(
            label(plane.callsign, "Unlabelled aircraft") +
            " · " + plane.latitude.toFixed(4) + ", " + plane.longitude.toFixed(4) +
            " · observed " + label(plane.observed_at) +
            " · altitude " + label(plane.altitude, "unknown")
          );
        }
        if (!events.childElementCount) appendTruthRow("No recent public ADS-B positions in this sample. This does not prove no aircraft are present.");
        appendTruthRow("Aircraft data © adsb.lol contributors (ODbL 1.0). Not a complete radar picture.");
      } catch (error) {
        if (error?.name !== "AbortError") setStatus("Aircraft source unavailable. No inferred aircraft positions.");
      } finally {
        if (activeRequest === controller) {
          activeRequest = null;
          requestKind = null;
        }
      }
    }

    async function checkSpaceSource(kind) {
      if (!verifiedStatus || currentView !== "space") return;
      const url = kind === "iss" ? config.thirdEyeSpaceIssUrl :
        kind === "orbit" ? config.thirdEyeSpaceOrbitUrl : null;
      if (!url) return;
      stopRequest();
      events.replaceChildren();
      cameraFrame.hidden = true;
      clearCameraMedia();
      setStatus("Checking " + (kind === "iss" ? "ISS position" : "CelesTrak orbit elements") + "…");
      const controller = new AbortController();
      activeRequest = controller;
      requestKind = kind;
      try {
        const data = await readJson(url, controller.signal);
        if (drawer.hidden || activeRequest !== controller || currentView !== "space") return;
        if (kind === "iss") {
          if (data?.provider !== "Where the ISS at" ||
              !Number.isFinite(data.latitude) || !Number.isFinite(data.longitude) ||
              !["fresh", "stale"].includes(data.freshness)) {
            setStatus("ISS position source unavailable. No coordinates claimed.");
            return;
          }
          lastEvidence = "ISS · " + data.freshness + " · position observed " + label(data.observed_at);
          setStatus(lastEvidence);
          appendTruthRow("ISS · " + data.latitude.toFixed(4) + ", " + data.longitude.toFixed(4) +
            " · altitude " + (Number.isFinite(data.altitude_km) ? data.altitude_km + " km" : "unknown"));
          appendTruthRow("Calculated position from external orbit source. This does not mean the ISS is above London or visible.");
        } else {
          if (data?.provider !== "CelesTrak" || data?.position_propagated !== false ||
              !data?.element_epoch || !data?.elements) {
            setStatus("CelesTrak orbital elements unavailable. No orbital position inferred.");
            return;
          }
          lastEvidence = "CelesTrak · published element epoch " + label(data.element_epoch) +
            " · no local orbit propagation";
          setStatus(lastEvidence);
          const e = data.elements;
          appendTruthRow("ISS elements · inclination " + String(e.inclination) +
            "° · eccentricity " + String(e.eccentricity) +
            " · mean motion " + String(e.mean_motion) + " rev/day");
          appendTruthRow("Orbit elements are not live coordinates. Source minimum refresh interval: 2 hours.");
        }
      } catch (error) {
        if (error?.name !== "AbortError") setStatus("Satellite source unavailable. No orbital data inferred.");
      } finally {
        if (activeRequest === controller) {
          activeRequest = null;
          requestKind = null;
        }
      }
    }

    function showNasaLondonImage(day) {
      if (!verifiedStatus || currentView !== "space" || !config.thirdEyeSpaceImageryUrl ||
          !/^\d{4}-\d{2}-\d{2}$/.test(day)) return;
      const url = new URL(config.thirdEyeSpaceImageryUrl, window.location.origin);
      if (url.origin !== window.location.origin) return;
      url.searchParams.set("day", day);
      url.searchParams.set("requested_at", String(Date.now()));
      clearCameraMedia();
      events.replaceChildren();
      cameraFrame.hidden = false;
      cameraImage.alt = "NASA GIBS MODIS Terra true-colour layer requested for London on " + day;
      cameraCaption.textContent = "NASA GIBS · MODIS Terra · requested imagery day " + day +
        " · actual acquisition/scene coverage unverified · not live satellite video";
      setStatus("Requesting NASA GIBS London imagery layer for " + day + "…");
      cameraImage.onload = () => {
        if (!drawer.hidden && currentView === "space") {
          lastEvidence = "NASA GIBS raster received for requested date " + day +
            ". Actual capture day and coverage not independently verified.";
          setStatus(lastEvidence);
        }
      };
      cameraImage.onerror = () => {
        if (!drawer.hidden && currentView === "space") {
          setStatus("NASA image unavailable. No imagery or acquisition claim.");
          cameraFrame.hidden = true;
        }
      };
      cameraImage.src = url.toString();
    }

    async function loadLondonCameras(rawSearch = "", page = 1, radiusKm = 0) {
      if (!verifiedStatus || currentView !== "ground" || !config.thirdEyeLondonCamerasUrl) return;
      stopRequest();
      cameraList.replaceChildren();
      cameraFrame.hidden = true;
      clearCameraMedia();
      const query = label(rawSearch, "").slice(0, 80);
      const controller = new AbortController();
      activeRequest = controller;
      requestKind = "london";
      try {
        const url = new URL(config.thirdEyeLondonCamerasUrl, window.location.origin);
        if (url.origin !== window.location.origin) throw new Error("cross_origin_blocked");
        if (query) url.searchParams.set("q", query);
        url.searchParams.set("page", String(page));
        url.searchParams.set("radius_km", String(radiusKm));
        setStatus("Loading public TfL cameras · nearest CR4 first…");
        const data = await readJson(url.toString(), controller.signal);
        if (drawer.hidden || currentView !== "ground" || activeRequest !== controller) return;
        if (data?.source_verified !== true || data?.provider !== "Transport for London (TfL)" ||
            data?.sort !== "distance_from_cr4_nearest_first" ||
            data?.origin?.label !== "CR4 / Mitcham district" ||
            !Number.isInteger(data?.total_matching) || !Number.isInteger(data?.page)) {
          setStatus("TfL London catalogue or CR4 source evidence unavailable. No live claim.");
          return;
        }
        const list = Array.isArray(data.cameras) ? data.cameras : [];
        for (const cam of list) {
          if (!/^\d{5}\.\d{5}$/.test(cam?.id) || typeof cam?.name !== "string") continue;
          const button = document.createElement("button");
          button.type = "button";
          button.className = "smi-third-eye-camera-button";
          const distance = typeof cam.distance_km === "number" && Number.isFinite(cam.distance_km)
            ? " · " + cam.distance_km.toFixed(1) + " km from CR4"
            : "";
          button.textContent = "📷 " + cam.name.slice(0, 100) + distance;
          button.addEventListener("click", () => showLondonCamera(cam));
          cameraList.appendChild(button);
        }
        const count = cameraList.querySelectorAll("button").length;
        const start = count ? (data.page - 1) * data.page_size + 1 : 0;
        const end = start + count - (count ? 1 : 0);
        const area = radiusKm ? "within " + radiusKm + " km of CR4" : "across London";
        setStatus(count
          ? "Showing " + start + "–" + end + " of " + data.total_matching +
            " available public TfL cameras " + area + " · nearest CR4 first."
          : "No public TfL cameras matched " + area +
            ". Try a larger radius or All London; private cameras are not accessible.");
        if (data.has_previous === true || data.has_more === true) {
          const pages = document.createElement("div");
          pages.className = "smi-third-eye-pages";
          if (data.has_previous === true) {
            const previous = document.createElement("button");
            previous.type = "button";
            previous.className = "tool-btn";
            previous.textContent = "← Previous 20";
            previous.addEventListener("click", () => loadLondonCameras(query, page - 1, radiusKm));
            pages.appendChild(previous);
          }
          const position = document.createElement("span");
          position.textContent = "Page " + data.page;
          pages.appendChild(position);
          if (data.has_more === true) {
            const next = document.createElement("button");
            next.type = "button";
            next.className = "tool-btn";
            next.textContent = "Next 20 →";
            next.addEventListener("click", () => loadLondonCameras(query, page + 1, radiusKm));
            pages.appendChild(next);
          }
          cameraList.appendChild(pages);
        }
        const attribution = document.createElement("a");
        attribution.textContent = "Powered by TfL Open Data · Terms";
        attribution.href = "https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service";
        attribution.target = "_blank";
        attribution.rel = "noopener noreferrer";
        attribution.className = "smi-third-eye-attribution";
        cameraList.appendChild(attribution);
      } catch (error) {
        if (error?.name !== "AbortError") {
          setStatus("TfL source unavailable. No London camera images verified.");
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
      clearCameraMedia();
      cameraFrame.hidden = false;
      if (camera?.clip_available === true && config.thirdEyeLondonClipUrl) {
        cameraPlay.hidden = false;
        cameraPlay.onclick = () => {
          if (drawer.hidden || currentView !== "ground") return;
          const clipUrl = new URL(
            config.thirdEyeLondonClipUrl.replace("__CAMERA_ID__", encodeURIComponent(id)),
            window.location.origin
          );
          if (clipUrl.origin !== window.location.origin) return;
          clipUrl.searchParams.set("requested_at", String(Date.now()));
          cameraVideo.hidden = false;
          cameraImage.hidden = true;
          cameraVideo.src = clipUrl.toString();
          cameraCaption.textContent = camera.name.slice(0, 100) +
            " · TfL rolling clip · Actual capture time unknown · Powered by TfL Open Data";
          setStatus("Loading real TfL rolling traffic clip through SMI…");
          cameraVideo.play().catch(() => {
            setStatus("TfL clip playback unavailable. The camera may be offline.");
          });
        };
      }
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
      clearCameraMedia();
      drawer.hidden = true;
      menuButton.setAttribute("aria-expanded", "false");
      menuButton.focus();
    }

    drawer.querySelector("#smi-third-eye-back").addEventListener("click", () => {
      stopRequest(true);
      clearCameraMedia();
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
    window.addEventListener("pagehide", () => {
      stopRequest();
      clearCameraMedia();
    }, {once: true});
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, {once: true});
  else boot();
})();
