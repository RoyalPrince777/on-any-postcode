(() => {
  "use strict";

  const csrfToken = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const pingControls = Array.from(document.querySelectorAll("[data-oap-ping-control]"));
  const muteControls = Array.from(document.querySelectorAll("[data-oap-ping-mute]"));
  const incomingNode = document.querySelector("[data-oap-incoming-pings]");

  if (!pingControls.length && !muteControls.length && !incomingNode) return;

  const state = { ready: false, busy: new Set(), timer: null };

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
      throw error;
    }
    return payload;
  };

  const refresh = () => {
    pingControls.forEach((control) => {
      const peer = control.dataset.recipientId || "";
      control.disabled = !state.ready || !peer || state.busy.has(peer);
    });
    muteControls.forEach((control) => {
      const peer = control.dataset.recipientId || "";
      control.disabled = !state.ready || !peer || state.busy.has(peer);
    });
  };

  const flash = (control) => {
    control.animate(
      [
        { transform: "scale(1)", opacity: 1 },
        { transform: "scale(.84)", opacity: .72 },
        { transform: "scale(1.18)", opacity: 1 },
        { transform: "scale(1)", opacity: 1 },
      ],
      { duration: 420, easing: "ease-out" },
    );
  };

  pingControls.forEach((control) => {
    control.addEventListener("click", async () => {
      const recipientId = control.dataset.recipientId || "";
      if (!recipientId || !state.ready || state.busy.has(recipientId)) return;
      state.busy.add(recipientId);
      refresh();
      try {
        await api("/linkup/ping", {
          method: "POST",
          body: JSON.stringify({
            recipient_id: recipientId,
            intensity: control.dataset.intensity || "normal",
          }),
        });
        flash(control);
        const previous = control.textContent;
        control.textContent = control.dataset.intensity === "double" ? "⚡⚡ Landed" : "⚡ Landed";
        window.setTimeout(() => { control.textContent = previous; }, 1100);
      } catch (error) {
        const previous = control.textContent;
        control.textContent =
          error.code === "ping_muted" ? "🔕 Muted" :
          error.code === "ping_rate_limited" ? "⏳ Slow down" :
          "⚡ Locked";
        window.setTimeout(() => { control.textContent = previous; }, 1600);
      } finally {
        state.busy.delete(recipientId);
        refresh();
      }
    });
  });

  muteControls.forEach((control) => {
    let muted = false;
    control.addEventListener("click", async () => {
      const peerId = control.dataset.recipientId || "";
      if (!peerId || !state.ready || state.busy.has(peerId)) return;
      state.busy.add(peerId);
      refresh();
      try {
        muted = !muted;
        await api("/linkup/ping/mute", {
          method: "POST",
          body: JSON.stringify({ peer_id: peerId, muted }),
        });
        control.textContent = muted ? "🔕 Ping Muted" : "🔔 Mute Ping";
      } catch (_error) {
        muted = !muted;
      } finally {
        state.busy.delete(peerId);
        refresh();
      }
    });
  });

  const markSeen = async (pingId) => {
    await api(`/linkup/ping/${encodeURIComponent(pingId)}/seen`, {
      method: "POST",
      body: "{}",
    });
  };

  const renderIncoming = (pings) => {
    if (!incomingNode) return;
    incomingNode.replaceChildren();
    const unseen = (pings || []).filter((ping) => !ping.seen);
    incomingNode.hidden = unseen.length === 0;
    unseen.slice(0, 5).forEach((ping) => {
      const card = document.createElement("div");
      const text = document.createElement("p");
      const icon = ping.intensity === "double" ? "⚡⚡" : ping.intensity === "priority" ? "🔥" : "⚡";
      text.textContent = `${icon} ${ping.sender_name} Pinged Up`;
      const seen = document.createElement("button");
      seen.type = "button";
      seen.className = "mc-secondary";
      seen.textContent = "Seen";
      seen.addEventListener("click", async () => {
        try {
          await markSeen(ping.ping_id);
          card.remove();
          if (!incomingNode.children.length) incomingNode.hidden = true;
        } catch (_error) {
          seen.textContent = "Try again";
        }
      });
      card.append(text, seen);
      incomingNode.append(card);
    });
  };

  const poll = async () => {
    state.timer = null;
    if (!state.ready) return;
    try {
      const result = await api("/linkup/ping/incoming");
      renderIncoming(result.pings || []);
    } catch (_error) {
      if (incomingNode) incomingNode.hidden = true;
    }
    state.timer = window.setTimeout(poll, 5000);
  };

  api("/linkup/ping/status")
    .then((status) => {
      state.ready = status.ready === true;
      refresh();
      if (state.ready) poll();
    })
    .catch(() => {
      state.ready = false;
      refresh();
    });

  window.addEventListener("pagehide", () => {
    if (state.timer) window.clearTimeout(state.timer);
  });
})();
