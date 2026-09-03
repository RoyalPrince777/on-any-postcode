(() => {
  "use strict";

  if (window.__OAP_LINK_SHARE_V1__) {
    return;
  }
  window.__OAP_LINK_SHARE_V1__ = true;

  const csrfToken = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const lockedCandidates = Array.from(document.querySelectorAll("button[data-runtime-locked]"));
  const shareControls = lockedCandidates.filter((button) => {
    const label = button.textContent.replace(/\s+/g, " ").trim();
    return label === "Share" || label.startsWith("Share ");
  });

  shareControls.forEach((control) => {
    control.dataset.oapShareControl = "";
    control.removeAttribute("data-runtime-locked");
    if (!control.dataset.recipientId && !control.dataset.recipientSource && !control.closest("form")) {
      control.dataset.recipientSource = "#linkup-recipient";
    }
  });

  let statusNode = document.querySelector("[data-oap-share-status]");
  if (!statusNode && shareControls.length) {
    statusNode = document.createElement("p");
    statusNode.className = document.querySelector("[data-linkup-app]")
      ? "linkup-runtime"
      : "oap-runtime-note";
    statusNode.dataset.oapShareStatus = "";
    statusNode.setAttribute("role", "status");
    statusNode.textContent = "Share status";
    const voiceStatus = document.querySelector("[data-oap-voice-status]");
    if (voiceStatus) {
      voiceStatus.insertAdjacentElement("afterend", statusNode);
    }
  }

  const lists = [];
  const registerList = (host, peerId) => {
    if (!peerId) {
      return;
    }
    let list = host.querySelector("[data-oap-share-list]");
    if (!list) {
      list = document.createElement("div");
      list.dataset.oapShareList = "";
      list.dataset.recipientId = peerId;
      list.setAttribute("aria-label", "Shared items");
      const voiceList = host.querySelector("[data-oap-voice-list]");
      if (voiceList) {
        voiceList.insertAdjacentElement("afterend", list);
      } else {
        host.appendChild(list);
      }
    }
    lists.push(list);
  };

  document.querySelectorAll(".mc-agent-card").forEach((card) => {
    const peerInput = card.querySelector('input[name="recipient_id"]');
    registerList(card, peerInput?.value || "");
  });

  document
    .querySelectorAll('.linkup-chat-panel[data-linkup-panel]:not([data-linkup-panel="new"])')
    .forEach((panel) => registerList(panel, panel.dataset.linkupPanel || ""));

  if (!shareControls.length && !lists.length) {
    return;
  }

  const state = {
    ready: false,
    busy: false,
    maxBytes: 25 * 1024 * 1024,
    allowed: new Set(),
  };

  const setStatus = (message) => {
    if (statusNode) {
      statusNode.textContent = message;
    }
  };

  const recipientFor = (control) => {
    const direct = control.dataset.recipientId || "";
    if (direct) {
      return direct;
    }
    const selector = control.dataset.recipientSource || "";
    if (selector) {
      return document.querySelector(selector)?.value || "";
    }
    const form = control.closest("form");
    if (form) {
      return (
        form.querySelector('select[name="recipient_id"]')?.value ||
        form.querySelector('input[name="recipient_id"]')?.value ||
        ""
      );
    }
    return document.querySelector("#linkup-recipient")?.value || "";
  };

  const apiJson = async (path, options = {}) => {
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

  const uploadShare = async (peerId, file) => {
    if (!state.allowed.has(file.type)) {
      const error = new Error("unsupported_share_type");
      error.code = "unsupported_share_type";
      throw error;
    }
    if (!file.size || file.size > state.maxBytes) {
      const error = new Error("share_too_large");
      error.code = "share_too_large";
      throw error;
    }
    const form = new FormData();
    form.append("recipient_id", peerId);
    form.append("share", file, file.name || "share");
    const response = await fetch("/linkup/share", {
      method: "POST",
      body: form,
      headers: { "X-OAP-CSRF": csrfToken, Accept: "application/json" },
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
      error.code = payload?.error?.code || "share_upload_failed";
      error.status = response.status;
      throw error;
    }
    return payload;
  };

  const refreshControls = () => {
    shareControls.forEach((control) => {
      const peerId = recipientFor(control);
      control.disabled = !state.ready || state.busy || !peerId;
      control.title = state.ready ? "Share" : "Share unavailable";
    });
  };

  const shareListFor = (peerId) =>
    lists.find((node) => node.dataset.recipientId === peerId) || null;

  const mediaUrl = (share, peerId) =>
    `/linkup/share/${encodeURIComponent(share.share_id)}/media?peer_id=${encodeURIComponent(peerId)}`;

  const renderShareList = async (peerId) => {
    const container = shareListFor(peerId);
    if (!container) {
      return;
    }
    try {
      const result = await apiJson(`/linkup/share?peer_id=${encodeURIComponent(peerId)}`);
      container.replaceChildren();
      for (const share of result.shares || []) {
        const item = document.createElement("div");
        item.className = `oap-share-item ${share.direction === "sent" ? "sent" : "received"}`;

        const label = document.createElement("p");
        label.className = "mc-eyebrow";
        label.textContent = `${share.kind.toUpperCase()} · ${share.created_at}`;
        item.appendChild(label);

        const name = document.createElement("p");
        name.textContent = share.original_name;
        item.appendChild(name);

        const url = mediaUrl(share, peerId);
        if (share.kind === "photo") {
          const image = document.createElement("img");
          image.loading = "lazy";
          image.alt = share.original_name;
          image.src = url;
          item.appendChild(image);
        } else if (share.kind === "video") {
          const video = document.createElement("video");
          video.controls = true;
          video.preload = "metadata";
          video.src = url;
          item.appendChild(video);
        } else {
          const download = document.createElement("a");
          download.className = "mc-secondary-link";
          download.href = url;
          download.download = share.original_name;
          download.textContent = share.original_name;
          item.appendChild(download);
        }

        if (share.direction === "sent") {
          const remove = document.createElement("button");
          remove.type = "button";
          remove.className = "mc-secondary";
          remove.textContent = "Delete";
          remove.addEventListener("click", async () => {
            remove.disabled = true;
            try {
              await apiJson(`/linkup/share/${encodeURIComponent(share.share_id)}`, {
                method: "DELETE",
                body: "{}",
              });
              await renderShareList(peerId);
              setStatus("Deleted");
            } catch (_error) {
              remove.disabled = false;
              setStatus("Couldn’t delete");
            }
          });
          item.appendChild(remove);
        }
        container.appendChild(item);
      }
    } catch (_error) {
      container.replaceChildren();
    }
  };

  const chooseShare = (control) => {
    if (!state.ready || state.busy) {
      return;
    }
    const peerId = recipientFor(control);
    if (!peerId) {
      setStatus("Choose a person");
      return;
    }

    const picker = document.createElement("input");
    picker.type = "file";
    picker.accept = Array.from(state.allowed).join(",");
    picker.hidden = true;
    document.body.appendChild(picker);
    picker.addEventListener(
      "change",
      async () => {
        const file = picker.files?.[0] || null;
        picker.remove();
        if (!file) {
          return;
        }
        state.busy = true;
        refreshControls();
        try {
          setStatus("Sharing…");
          await uploadShare(peerId, file);
          await renderShareList(peerId);
          setStatus("Shared");
        } catch (error) {
          if (error.code === "unsupported_share_type") {
            setStatus("Unsupported file type");
          } else if (error.code === "share_too_large") {
            setStatus("File too large");
          } else {
            setStatus("Couldn’t share");
          }
        } finally {
          state.busy = false;
          refreshControls();
        }
      },
      { once: true },
    );
    picker.click();
  };

  shareControls.forEach((control) => {
    control.addEventListener("click", () => chooseShare(control));
  });

  document.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", refreshControls);
  });

  apiJson("/linkup/share/status")
    .then((status) => {
      state.ready = status.ready === true && status.first_party === true;
      state.maxBytes = Number(status.max_share_bytes) || state.maxBytes;
      state.allowed = new Set(status.allowed_mime_types || []);
      setStatus(state.ready ? "Share ready" : "Share unavailable");
      refreshControls();
      lists.forEach((node) => {
        const peerId = node.dataset.recipientId || "";
        if (peerId) {
          renderShareList(peerId);
        }
      });
    })
    .catch(() => {
      state.ready = false;
      setStatus("Share unavailable");
      refreshControls();
    });
})();
