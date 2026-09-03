(() => {
  "use strict";

  const csrfToken = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const forms = Array.from(document.querySelectorAll("form[data-oap-link-composer]"));

  if (!forms.length) {
    return;
  }

  const state = {
    ready: false,
    activityReady: false,
    activeForm: null,
    lastTypingSentAt: 0,
    typingStopTimer: null,
    typingRefreshTimer: null,
    pollTimer: null,
  };

  const recipientFor = (form) => {
    const field = form.querySelector('[name="recipient_id"]');
    return field?.value || "";
  };

  const bodyFor = (form) => form.querySelector('textarea[name="body"]');

  const ensureStatusNode = (form, attribute, className) => {
    let node = form.querySelector(`[${attribute}]`);
    if (node) {
      return node;
    }
    node = document.createElement("p");
    node.className = className;
    node.setAttribute(attribute, "");
    node.setAttribute("role", "status");
    form.appendChild(node);
    return node;
  };

  const localStatusFor = (form) =>
    ensureStatusNode(form, "data-oap-composer-status", "oap-runtime-note");

  const typingStatusFor = (form) =>
    ensureStatusNode(form, "data-oap-typing-state", "mc-eyebrow");

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

  const updateRenderedStates = (messages) => {
    for (const message of messages || []) {
      const node = document.querySelector(
        `[data-oap-message-state][data-message-id="${CSS.escape(message.message_id)}"]`,
      );
      if (!node) {
        continue;
      }
      node.dataset.state = message.state;
      node.textContent = message.state === "seen" ? "Seen" : "Landed";
    }
  };

  const pollPeer = async () => {
    const form = state.activeForm;
    if (!form) {
      return;
    }
    const peerId = recipientFor(form);
    if (!peerId) {
      return;
    }
    try {
      const receipts = await apiJson(`/linkup/messages/state?peer_id=${encodeURIComponent(peerId)}`);
      const messages = receipts.messages || [];
      updateRenderedStates(messages);
      const local = localStatusFor(form);
      if (messages.length && !local.querySelector("button")) {
        local.textContent = `Latest Link: ${messages[0].state === "seen" ? "Seen" : "Landed"}`;
      }
    } catch (_error) {
      // Existing persisted receipts remain valid if polling is unavailable.
    }
    if (!state.activityReady) {
      return;
    }
    try {
      const activity = await apiJson(`/linkup/activity/typing?peer_id=${encodeURIComponent(peerId)}`);
      typingStatusFor(form).textContent = activity.typing ? "Typing…" : "";
    } catch (_error) {
      typingStatusFor(form).textContent = "";
    }
  };

  const startPolling = (form) => {
    state.activeForm = form;
    if (state.pollTimer) {
      window.clearInterval(state.pollTimer);
    }
    pollPeer();
    state.pollTimer = window.setInterval(pollPeer, 4000);
  };

  const typingUpdate = async (form, active) => {
    if (!state.activityReady) {
      return;
    }
    const peerId = recipientFor(form);
    if (!peerId) {
      return;
    }
    try {
      await apiJson("/linkup/activity/typing", {
        method: "POST",
        body: JSON.stringify({ peer_id: peerId, active }),
      });
      if (active) {
        state.lastTypingSentAt = Date.now();
      }
    } catch (_error) {
      // Typing is convenience-only and must never block a Link.
    }
  };

  const clearTypingTimers = () => {
    if (state.typingStopTimer) {
      window.clearTimeout(state.typingStopTimer);
      state.typingStopTimer = null;
    }
    if (state.typingRefreshTimer) {
      window.clearInterval(state.typingRefreshTimer);
      state.typingRefreshTimer = null;
    }
  };

  const startTyping = (form) => {
    if (!state.activityReady) {
      return;
    }
    const textarea = bodyFor(form);
    if (!textarea || !textarea.value.trim() || !recipientFor(form)) {
      return;
    }
    startPolling(form);
    const now = Date.now();
    if (now - state.lastTypingSentAt > 2000) {
      typingUpdate(form, true);
    }
    if (!state.typingRefreshTimer) {
      state.typingRefreshTimer = window.setInterval(() => {
        if (state.activeForm === form && textarea.value.trim()) {
          typingUpdate(form, true);
        }
      }, 4000);
    }
    if (state.typingStopTimer) {
      window.clearTimeout(state.typingStopTimer);
    }
    state.typingStopTimer = window.setTimeout(() => {
      typingUpdate(form, false);
      clearTypingTimers();
    }, 2200);
  };

  const stopTyping = (form) => {
    clearTypingTimers();
    typingUpdate(form, false);
  };

  const ensureLocalReceipt = (form, payload, messageId) => {
    const host = form.closest("article") || form.parentElement;
    if (!host) {
      return;
    }
    const item = document.createElement("div");
    item.className = "oap-link-local-receipt";

    const label = document.createElement("p");
    label.className = "mc-eyebrow";
    label.textContent = "OUT · just now";
    item.appendChild(label);

    const body = document.createElement("p");
    body.textContent = payload.body;
    item.appendChild(body);

    const receipt = document.createElement("p");
    receipt.className = "mc-eyebrow";
    receipt.dataset.oapMessageState = "";
    receipt.dataset.messageId = messageId;
    receipt.dataset.state = "landed";
    receipt.textContent = "Landed";
    item.appendChild(receipt);

    form.before(item);
  };

  const showRetry = (form, payload, message) => {
    const node = localStatusFor(form);
    node.replaceChildren();
    const text = document.createElement("span");
    text.textContent = `${message} `;
    node.appendChild(text);
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "mc-secondary";
    retry.textContent = "Retry";
    retry.addEventListener("click", () => sendLink(form, payload));
    node.appendChild(retry);
  };

  const sendLink = async (form, fixedPayload = null) => {
    if (!state.ready) {
      form.submit();
      return;
    }
    const textarea = bodyFor(form);
    const payload = fixedPayload || {
      recipient_id: recipientFor(form),
      body: textarea?.value.trim() || "",
    };
    if (!payload.recipient_id || !payload.body) {
      return;
    }
    const submit = form.querySelector('button[type="submit"]');
    const localStatus = localStatusFor(form);
    if (submit) {
      submit.disabled = true;
    }
    localStatus.textContent = "Sending…";
    stopTyping(form);
    try {
      const result = await apiJson("/linkup/messages", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (result.state !== "landed" || !result.message_id) {
        const error = new Error("missing_landed_receipt");
        error.code = "missing_landed_receipt";
        throw error;
      }
      if (textarea && !fixedPayload) {
        textarea.value = "";
      }
      localStatus.textContent = "Landed";
      ensureLocalReceipt(form, payload, result.message_id);
      startPolling(form);
    } catch (error) {
      const code = error.code || "link_not_landed";
      const message =
        code === "link_blocked"
          ? "Link blocked. Nothing landed."
          : code === "accepted_link_required"
            ? "Accepted Link required. Nothing landed."
            : "Link did not land.";
      showRetry(form, payload, message);
    } finally {
      if (submit) {
        submit.disabled = false;
      }
    }
  };

  forms.forEach((form) => {
    const textarea = bodyFor(form);
    localStatusFor(form);
    typingStatusFor(form);
    form.addEventListener("submit", (event) => {
      if (!state.ready) {
        return;
      }
      event.preventDefault();
      sendLink(form);
    });
    textarea?.addEventListener("focus", () => startPolling(form));
    textarea?.addEventListener("input", () => startTyping(form));
    textarea?.addEventListener("blur", () => stopTyping(form));
    const recipient = form.querySelector('[name="recipient_id"]');
    recipient?.addEventListener("change", () => {
      stopTyping(form);
      startPolling(form);
    });
  });

  window.addEventListener("pagehide", () => {
    if (state.activeForm) {
      stopTyping(state.activeForm);
    }
    if (state.pollTimer) {
      window.clearInterval(state.pollTimer);
    }
  });

  apiJson("/linkup/messages/status")
    .then((status) => {
      state.ready = status.ready === true && status.first_party === true;
      state.activityReady = status.activity_ready === true;
      if (state.ready) {
        forms.forEach((form) => {
          localStatusFor(form).textContent = state.activityReady
            ? "Link → Landed → Seen · private typing ready"
            : "Link → Landed → Seen";
        });
      }
    })
    .catch(() => {
      state.ready = false;
      state.activityReady = false;
    });
})();
