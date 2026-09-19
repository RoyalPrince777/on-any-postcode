(() => {
  "use strict";

  const host = document.querySelector("[data-oap-incoming-unified]");
  if (!host) return;

  const state = { ready: false, timer: null };

  const apiJson = async (path) => {
    const response = await fetch(path, {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
      cache: "no-store",
    });
    let payload = {};
    try { payload = await response.json(); } catch (_error) {}
    if (!response.ok) throw new Error(payload?.error?.code || "incoming_unavailable");
    return payload;
  };

  const iconFor = (type) => ({
    link: "🔗",
    link_request: "🤝",
    voice: "🎙️",
    missed_call: "📞",
    circle_invite: "⭕",
  }[type] || "📥");

  const render = (events) => {
    host.replaceChildren();
    const visible = (events || []).slice(0, 12);
    host.hidden = visible.length === 0;
    visible.forEach((event) => {
      const item = document.createElement("div");
      item.className = "linkup-incoming-item";
      item.dataset.incomingType = event.event_type || "";

      const title = document.createElement("strong");
      title.textContent = `${iconFor(event.event_type)} ${event.title || "Incoming"} · ${event.peer_name || "OAP member"}`;
      item.appendChild(title);

      if (event.detail) {
        const detail = document.createElement("span");
        detail.textContent = event.detail;
        item.appendChild(detail);
      }

      const when = document.createElement("small");
      when.textContent = event.created_at || "";
      item.appendChild(when);

      if (event.event_type === "link" && event.peer_id) {
        item.role = "button";
        item.tabIndex = 0;
        const open = () => {
          const button = document.querySelector(
            `[data-linkup-thread="${CSS.escape(event.peer_id)}"]`,
          );
          button?.click();
        };
        item.addEventListener("click", open);
        item.addEventListener("keydown", (keyEvent) => {
          if (keyEvent.key === "Enter" || keyEvent.key === " ") open();
        });
      }

      host.appendChild(item);
    });
  };

  const poll = async () => {
    try {
      const result = await apiJson("/linkup/incoming");
      render(result.events || []);
    } catch (_error) {
      host.hidden = true;
    }
  };

  apiJson("/linkup/incoming/status")
    .then((status) => {
      state.ready = status.ready === true && status.first_party === true;
      if (!state.ready) {
        host.hidden = true;
        return;
      }
      poll();
      state.timer = window.setInterval(poll, 5000);
    })
    .catch(() => {
      state.ready = false;
      host.hidden = true;
    });

  window.addEventListener("pagehide", () => {
    if (state.timer) window.clearInterval(state.timer);
  });
})();
