(() => {
  "use strict";

  const csrfToken = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const statusNode = document.querySelector("[data-oap-voice-status]");
  const recordControls = Array.from(document.querySelectorAll("[data-oap-voice-control]"));
  const stopControls = Array.from(document.querySelectorAll("[data-oap-voice-stop]"));
  const pttControls = Array.from(document.querySelectorAll("[data-oap-ptt-control]"));
  const lists = Array.from(document.querySelectorAll("[data-oap-voice-list]"));

  if (!recordControls.length && !pttControls.length && !lists.length) {
    return;
  }

  const state = {
    ready: false,
    maxBytes: 5 * 1024 * 1024,
    maxDurationMs: 120000,
    current: null,
    autoStopTimer: null,
    pttPress: null,
    capturePending: false,
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
    return selector ? document.querySelector(selector)?.value || "" : "";
  };

  const preferredMime = () => {
    if (typeof window.MediaRecorder !== "function") {
      return "";
    }
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/ogg;codecs=opus",
      "audio/webm",
      "audio/mp4",
    ];
    return candidates.find((mime) => MediaRecorder.isTypeSupported(mime)) || "";
  };

  const browserReady = () =>
    Boolean(navigator.mediaDevices?.getUserMedia) &&
    typeof window.MediaRecorder === "function" &&
    Boolean(preferredMime());

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

  const uploadVoice = async (peerId, blob, durationMs) => {
    if (blob.size > state.maxBytes) {
      throw new Error("voice_too_large");
    }
    const form = new FormData();
    form.append("recipient_id", peerId);
    form.append("duration_ms", String(Math.min(durationMs, state.maxDurationMs)));
    form.append("voice", blob, "voice");
    const response = await fetch("/linkup/voice", {
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
      error.code = payload?.error?.code || "voice_upload_failed";
      error.status = response.status;
      throw error;
    }
    return payload;
  };

  const controlsForPeer = (peerId) =>
    [...recordControls, ...stopControls].filter((control) => recipientFor(control) === peerId);

  const refreshControls = () => {
  recordControls.forEach((control) => {
      const peerId = recipientFor(control);
      control.disabled = !state.ready || !browserReady() || !peerId || Boolean(state.current) || Boolean(state.pttPress) || state.capturePending;
      const marker = control.querySelector("small");
      if (marker) {
        marker.textContent = control.disabled ? "locked" : "ready";
      }
    });
    pttControls.forEach((control) => {
      const active = state.pttPress?.control === control;
      control.disabled = !active && (!state.ready || !browserReady() || !recipientFor(control) || Boolean(state.current) || Boolean(state.pttPress) || state.capturePending));
      control.setAttribute("aria-pressed", String(active));
    });
    stopControls.forEach((control) => {
      const peerId = recipientFor(control);
      const active = Boolean(state.current && state.current.peerId === peerId);
      control.hidden = !active;
      control.disabled = !active;
    });
  };

  const stopTracks = (stream) => {
    stream?.getTracks().forEach((track) => track.stop());
  };

  const clearAutoStop = () => {
    if (state.autoStopTimer) {
      window.clearTimeout(state.autoStopTimer);
      state.autoStopTimer = null;
    }
  };

  const voiceListFor = (peerId) =>
    lists.find((node) => node.dataset.recipientId === peerId) || null;

  const renderVoiceList = async (peerId) => {
    const container = voiceListFor(peerId);
    if (!container) {
      return;
    }
    try {
      const result = await apiJson(`/linkup/voice?peer_id=${encodeURIComponent(peerId)}`);
      container.replaceChildren();
      for (const voice of result.voices || []) {
        const item = document.createElement("div");
        item.className = "oap-voice-note";

        const label = document.createElement("p");
        label.className = "mc-eyebrow";
        label.textContent = `${voice.direction === "sent" ? "OUT" : "IN"} · Voice · ${voice.created_at}`;
        item.appendChild(label);

        const audio = document.createElement("audio");
        audio.controls = true;
        audio.preload = "none";
        audio.src = `/linkup/voice/${encodeURIComponent(voice.voice_id)}/media?peer_id=${encodeURIComponent(peerId)}`;
        item.appendChild(audio);

        if (voice.direction === "sent") {
          const remove = document.createElement("button");
          remove.type = "button";
          remove.className = "mc-secondary";
          remove.textContent = "Delete Voice";
          remove.addEventListener("click", async () => {
            remove.disabled = true;
            try {
              await apiJson(`/linkup/voice/${encodeURIComponent(voice.voice_id)}`, {
                method: "DELETE",
                body: "{}",
              });
              await renderVoiceList(peerId);
              setStatus("Voice deleted.");
            } catch (_error) {
              remove.disabled = false;
              setStatus("Voice could not be deleted.");
            }
          });
          item.appendChild(remove);
        }
        container.appendChild(item);
      }
      if (!container.childNodes.length) {
        const empty = document.createElement("p");
        empty.textContent = "No Voice yet.";
        container.appendChild(empty);
      }
    } catch (_error) {
      container.replaceChildren();
      const unavailable = document.createElement("p");
      unavailable.textContent = "Voice is unavailable for this Link.";
      container.appendChild(unavailable);
    }
  };

  const finishRecording = () => {
    if (!state.current) {
      return;
    }
    const recorder = state.current.recorder;
    if (recorder.state !== "inactive") {
      recorder.stop();
    }
  };

  const startRecording = async (control, pttPress = null) => {
    if (!state.ready || state.current || state.capturePending || !browserReady() || (!pttPress && state.pttPress)) {
      return;
    }
    const peerId = recipientFor(control);
    if (!peerId) {
      setStatus("Choose a Certified Link first.");
      return;
    }

    state.capturePending = true;
    refreshControls();
    let stream = null;
    try {
      const mimeType = preferredMime();
      stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      state.capturePending = false;
      // A release/cancel may happen while the browser permission prompt is open.
      if (pttPress && (state.pttPress !== pttPress || pttPress.cancelled)) {
        stopTracks(stream);
        if (state.pttPress === pttPress) state.pttPress = null;
        refreshControls();
        return;
      }
      const recorder = new MediaRecorder(stream, { mimeType });
      const chunks = [];
      const startedAt = Date.now();

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data?.size) {
          chunks.push(event.data);
        }
      });

      recorder.addEventListener("stop", async () => {
        clearAutoStop();
        stopTracks(stream);
        const current = state.current;
        state.current = null;
        if (pttPress && state.pttPress === pttPress) state.pttPress = null;
        refreshControls();
        if (!current || current.cancelled) {
          setStatus("Voice cancelled.");
          return;
        }
        const durationMs = Math.min(Date.now() - startedAt, state.maxDurationMs);
        const blob = new Blob(chunks, { type: recorder.mimeType || mimeType });
        if (!blob.size) {
          setStatus("No Voice was captured.");
          return;
        }
        try {
          setStatus("Voice landing…");
          await uploadVoice(peerId, blob, durationMs);
          await renderVoiceList(peerId);
          setStatus("Voice landed.");
        } catch (error) {
          setStatus(
            error.code === "voice_too_large"
              ? "Voice is too large. Nothing was stored."
              : "Voice could not land. Nothing unsafe was stored.",
          );
        }
      });

      state.current = { peerId, recorder, stream, chunks, startedAt, cancelled: false };
      recorder.start(1000);
      state.autoStopTimer = window.setTimeout(finishRecording, state.maxDurationMs);
      setStatus(pttPress ? "PTT recording… release to send." : "Voice recording… tap Stop when finished.");
      if (pttPress?.released) finishRecording();
      refreshControls();
    } catch (error) {
      state.capturePending = false;
      stopTracks(stream);
      state.current = null;
      if (pttPress && state.pttPress === pttPress) state.pttPress = null;
      refreshControls();
      setStatus(
        error?.name === "NotAllowedError"
          ? "Microphone permission was not granted."
          : "Voice could not start.",
      );
    }
  };

    // PTT deliberately reuses the governed Voice upload; it is not a live audio stream.
  // Keep pending capture tokens until permissions resolve to prevent release-before-capture leaks.
  const beginPtt = (control) => {
    if (state.pttPress || state.current || state.capturePending || control.disabled || !state.ready || !browserReady()) return;
    const press = { control, released: false, cancelled: false };
    state.pttPress = press;
    refreshControls();
    startRecording(control, press);
  };

  const endPtt = (cancel = false) => {
    const press = state.pttPress;
    if (!press) return;
    press.released = true;
    if (cancel) press.cancelled = true;
    if (state.current) {
      if (cancel) state.current.cancelled = true;
      finishRecording();
    } else if (cancel) {
      state.pttPress = null;
    }
    refreshControls();
  };

  pttControls.forEach((control) => {
    control.addEventListener("pointerdown", (event) => {
      if (event.button !== 0 || control.disabled) return;
      event.preventDefault();
      beginPtt(control);
    });
    control.addEventListener("keydown", (event) => {
      if ((event.key === " " || event.key === "Enter") && !event.repeat) {
        event.preventDefault();
        beginPtt(control);
      }
    });
    control.addEventListener("keyup", (event) => {
      if (event.key === " " || event.key === "Enter") {
        event.preventDefault();
        if (state.pttPress?.control === control) endPtt();
      }
    });
    control.addEventListener("blur", () => {
      if (state.pttPress?.control === control) endPtt(true);
    });
  });
  window.addEventListener("pointerup", () => endPtt());
  window.addEventListener("pointercancel", () => endPtt(true));
  window.addEventListener("blur", () => endPtt(true));
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) endPtt(true);
  });

  recordControls.forEach((control) => {
    control.addEventListener("click", () => startRecording(control));
  });

  stopControls.forEach((control) => {
    control.addEventListener("click", () => {
      if (!state.current || state.current.peerId !== recipientFor(control)) {
        return;
      }
      finishRecording();
    });
  });

  document.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", refreshControls);
  });

  window.addEventListener("pagehide", () => {
    endPtt(true);
    clearAutoStop();
    if (state.current) {
      state.current.cancelled = true;
      stopTracks(state.current.stream);
      if (state.current.recorder.state !== "inactive") {
        state.current.recorder.stop();
      }
    }
  });

  apiJson("/linkup/voice/status")
    .then((status) => {
      state.ready = status.ready === true && status.first_party === true;
      state.maxBytes = Number(status.max_voice_bytes) || state.maxBytes;
      state.maxDurationMs = Number(status.max_voice_duration_ms) || state.maxDurationMs;
      setStatus(
        state.ready && browserReady()
          ? "Voice is ready. Microphone stays off until you tap Voice."
          : "Voice remains locked until OAP Data Voice and browser recording are ready.",
      );
      refreshControls();
      lists.forEach((node) => {
        const peerId = node.dataset.recipientId || "";
        if (peerId) {
          renderVoiceList(peerId);
        }
      });
    })
    .catch(() => {
      state.ready = false;
      setStatus("Voice is unavailable. Microphone remains off.");
      refreshControls();
    });
})();

(() => {
  "use strict";
  if (document.querySelector('script[data-oap-share-loader]')) {
    return;
  }
  const script = document.createElement("script");
  script.src = "/static/linkup_share.js";
  script.defer = true;
  script.dataset.oapShareLoader = "";
  document.head.appendChild(script);
})();

(() => {
  "use strict";
  if (document.querySelector('script[data-oap-message-loader]')) {
    return;
  }
  const script = document.createElement("script");
  script.src = "/static/linkup_messages.js";
  script.defer = true;
  script.dataset.oapMessageLoader = "";
  document.head.appendChild(script);
})();
