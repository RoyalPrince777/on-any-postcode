(() => {
  "use strict";

  const csrfToken = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const statusNode = document.querySelector("[data-oap-presence-status]");
  const aroundControls = Array.from(document.querySelectorAll("[data-oap-around-control]"));
  const shareSpotControls = Array.from(document.querySelectorAll("[data-oap-share-spot-control]"));
  const liveSpotControls = Array.from(document.querySelectorAll("[data-oap-live-spot-control]"));
  const stopSpotControls = Array.from(document.querySelectorAll("[data-oap-live-spot-stop]"));
  const allControls = [...aroundControls, ...shareSpotControls, ...liveSpotControls];

  if (!allControls.length && !stopSpotControls.length) {
    return;
  }

  const state = {
    ready: false,
    busyPeers: new Set(),
    heartbeatTimer: null,
    liveWatches: new Map(),
  };

  const setStatus = (message) => {
    if (statusNode) {
      statusNode.textContent = message;
    }
  };

  const api = async (path, options = {}) => {
    const method = options.method || "GET";
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");
    if (method !== "GET") {
      headers.set("Content-Type", "application/json");
      headers.set("X-OAP-CSRF", csrfToken);
    }
    const response = await fetch(path, {
      ...options,
      method,
      headers,
      credentials: "same-origin",
      cache: "no-store",
    });
    let payload = {};
    try {
      payload = await response.json();
    } catch (_error) {
      payload = {};
    }
    if (!response.ok) {
      const error = new Error(payload?.error?.code || `http_${response.status}`);
      error.code = payload?.error?.code || "request_failed";
      error.status = response.status;
      throw error;
    }
    return payload;
  };

  const recipientFor = (control) => {
    const direct = control.dataset.recipientId || "";
    if (direct) {
      return direct;
    }
    const selector = control.dataset.recipientSource || "";
    return selector ? document.querySelector(selector)?.value || "" : "";
  };

  const controlsForPeer = (peerId) =>
    [...allControls, ...stopSpotControls].filter((control) => recipientFor(control) === peerId);

  const refreshControls = () => {
    allControls.forEach((control) => {
      const peerId = recipientFor(control);
      control.disabled = !state.ready || !peerId || state.busyPeers.has(peerId);
      const marker = control.querySelector("small");
      if (marker) {
        marker.textContent = control.disabled ? "locked" : "ready";
      }
    });
    stopSpotControls.forEach((control) => {
      const peerId = recipientFor(control);
      control.hidden = !peerId || !state.liveWatches.has(peerId);
      control.disabled = !state.ready || !peerId || state.busyPeers.has(peerId);
    });
  };

  const withBusyPeer = async (peerId, action) => {
    if (!peerId || state.busyPeers.has(peerId)) {
      return;
    }
    state.busyPeers.add(peerId);
    controlsForPeer(peerId).forEach((control) => {
      control.disabled = true;
    });
    try {
      await action();
    } finally {
      state.busyPeers.delete(peerId);
      refreshControls();
    }
  };

  const getVisibility = (peerId) =>
    api(`/linkup/presence/visibility/${encodeURIComponent(peerId)}`);

  const setVisibility = (peerId, visibility) =>
    api("/linkup/presence/visibility", {
      method: "POST",
      body: JSON.stringify({
        peer_id: peerId,
        around_now: Boolean(visibility.around_now),
        live_spot: Boolean(visibility.live_spot),
      }),
    });

  const sendHeartbeat = (aroundNow = true) =>
    api("/linkup/presence/heartbeat", {
      method: "POST",
      body: JSON.stringify({ around_now: aroundNow }),
    });

  const keepHeartbeatAlive = () => {
    if (state.heartbeatTimer) {
      return;
    }
    state.heartbeatTimer = window.setInterval(() => {
      sendHeartbeat(true).catch(() => {
        setStatus("Around Now heartbeat paused; visibility remains private.");
      });
    }, 60000);
  };

  const positionOnce = () =>
    new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("geolocation_unavailable"));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 10000,
      });
    });

  const publishPosition = (peerId, position, durationMinutes) =>
    api("/linkup/live-spot", {
      method: "POST",
      body: JSON.stringify({
        peer_id: peerId,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy_m: Number.isFinite(position.coords.accuracy) ? position.coords.accuracy : null,
        duration_minutes: durationMinutes,
      }),
    });

  const stopLiveSpot = async (peerId) => {
    const watchId = state.liveWatches.get(peerId);
    if (watchId !== undefined && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchId);
    }
    state.liveWatches.delete(peerId);
    try {
      await api(`/linkup/live-spot/${encodeURIComponent(peerId)}`, {
        method: "DELETE",
        body: "{}",
      });
    } finally {
      try {
        const visibility = await getVisibility(peerId);
        await setVisibility(peerId, { ...visibility, live_spot: false });
      } catch (_error) {
        // Deleting the active share is the privacy-critical action; visibility expires closed on reads without a row.
      }
    }
    setStatus("Live Spot stopped.");
  };

  aroundControls.forEach((control) => {
    control.addEventListener("click", () => {
      const peerId = recipientFor(control);
      withBusyPeer(peerId, async () => {
        const visibility = await getVisibility(peerId);
        const enabled = !Boolean(visibility.around_now);
        await setVisibility(peerId, { ...visibility, around_now: enabled });
        if (enabled) {
          await sendHeartbeat(true);
          keepHeartbeatAlive();
          setStatus("Around Now is visible to this Link for up to 120 seconds between heartbeats.");
        } else {
          setStatus("Around Now hidden from this Link.");
        }
        const marker = control.querySelector("small");
        if (marker) {
          marker.textContent = enabled ? "on" : "ready";
        }
      }).catch(() => {
        setStatus("Around Now could not change. Privacy remains fail-closed.");
      });
    });
  });

  shareSpotControls.forEach((control) => {
    control.addEventListener("click", () => {
      const peerId = recipientFor(control);
      withBusyPeer(peerId, async () => {
        const visibility = await getVisibility(peerId);
        await setVisibility(peerId, { ...visibility, live_spot: true });
        try {
          const position = await positionOnce();
          await publishPosition(peerId, position, 1);
          setStatus("Share My Spot landed for this Link and expires automatically.");
        } catch (error) {
          await setVisibility(peerId, { ...visibility, live_spot: false }).catch(() => {});
          throw error;
        }
      }).catch((error) => {
        setStatus(
          error?.code === 1 || error?.name === "NotAllowedError"
            ? "Location permission was not granted."
            : "Share My Spot could not start. Nothing was shared.",
        );
      });
    });
  });

  liveSpotControls.forEach((control) => {
    control.addEventListener("click", () => {
      const peerId = recipientFor(control);
      withBusyPeer(peerId, async () => {
        if (!navigator.geolocation) {
          throw new Error("geolocation_unavailable");
        }
        const visibility = await getVisibility(peerId);
        await setVisibility(peerId, { ...visibility, live_spot: true });
        try {
          const first = await positionOnce();
          await publishPosition(peerId, first, 15);
          const watchId = navigator.geolocation.watchPosition(
            (position) => {
              publishPosition(peerId, position, 15).catch(() => {
                setStatus("Live Spot update paused; the last point will expire automatically.");
              });
            },
            () => {
              setStatus("Live Spot location updates paused; the last point will expire automatically.");
            },
            { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 },
          );
          state.liveWatches.set(peerId, watchId);
          setStatus("Live Spot is active for this Link. Tap Stop Live Spot to end it now.");
        } catch (error) {
          await setVisibility(peerId, { ...visibility, live_spot: false }).catch(() => {});
          throw error;
        }
      }).catch((error) => {
        setStatus(
          error?.code === 1 || error?.name === "NotAllowedError"
            ? "Location permission was not granted."
            : "Live Spot could not start. Nothing was shared.",
        );
      });
    });
  });

  stopSpotControls.forEach((control) => {
    control.addEventListener("click", () => {
      const peerId = recipientFor(control);
      withBusyPeer(peerId, () => stopLiveSpot(peerId)).catch(() => {
        setStatus("Live Spot stop could not be confirmed. The server share remains time-bounded.");
      });
    });
  });

  document.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", refreshControls);
  });

  window.addEventListener("pagehide", () => {
    state.liveWatches.forEach((watchId) => {
      if (navigator.geolocation) {
        navigator.geolocation.clearWatch(watchId);
      }
    });
    state.liveWatches.clear();
  });

  api("/linkup/presence/status")
    .then((status) => {
      state.ready = status.ready === true;
      setStatus(
        state.ready
          ? "Around Now and Live Spot are ready. Location stays off until you choose to share it."
          : "Around Now and Live Spot remain locked until OAP Data presence is ready.",
      );
      refreshControls();
    })
    .catch(() => {
      state.ready = false;
      setStatus("Around Now and Live Spot are unavailable. Nothing is being shared.");
      refreshControls();
    });
})();
