(() => {
  "use strict";

  const csrfToken = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const roomControl = document.querySelector("[data-oap-room-ptt-control]");
  const roomStop = document.querySelector("[data-oap-room-ptt-stop]");
  const roomList = document.querySelector("[data-oap-room-voice-list]");
  const roomCode = document.querySelector("[data-oap-ptt-room-code]");
  const copyRoomCode = document.querySelector("[data-oap-ptt-copy-room-code]");
  const roomStatus = document.querySelector("[data-oap-ptt-room-status]");

  if (copyRoomCode && roomCode) {
    copyRoomCode.addEventListener("click", async () => {
      const code = (roomCode.textContent || "").trim();
      if (!code) return;
      try {
        await navigator.clipboard.writeText(code);
        copyRoomCode.textContent = "Copied";
      } catch (_error) {
        copyRoomCode.textContent = code;
      }
    });
  }

  if (roomCode && roomStatus) {
    let waiting = true;
    const pollRoomJoin = async () => {
      if (!waiting) return;
      try {
        const response = await fetch("/ptt/room/status", {
          credentials: "same-origin",
          cache: "no-store",
          headers: { Accept: "application/json" },
        });
        const payload = await response.json().catch(() => ({}));
        if (response.ok && payload.active === true && Number(payload.member_count) > 1) {
          waiting = false;
          roomStatus.textContent = "Room member connected. Opening Room…";
          window.location.reload();
          return;
        }
        roomStatus.textContent = "Waiting for Room members…";
      } catch (_error) {
        roomStatus.textContent = "Room status unavailable. The code remains temporary.";
      }
      window.setTimeout(pollRoomJoin, 2000);
    };
    pollRoomJoin();
  }

  if (!roomControl || !roomList) return;

  const state = {
    ready: false,
    current: null,
    autoStopTimer: null,
    maxBytes: 5 * 1024 * 1024,
    maxDurationMs: 120000,
  };

  const preferredMime = () => {
    if (typeof window.MediaRecorder !== "function") return "";
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

  const stopTracks = (stream) => {
    stream?.getTracks().forEach((track) => track.stop());
  };

  const refresh = () => {
    roomControl.disabled = !state.ready || !browserReady() || Boolean(state.current);
    if (roomStop) {
      roomStop.hidden = !state.current;
      roomStop.disabled = !state.current;
    }
  };

  const apiJson = async (path) => {
    const response = await fetch(path, {
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload?.error?.code || `http_${response.status}`);
    return payload;
  };

  const renderHistory = async () => {
    try {
      const result = await apiJson("/ptt/room/voice");
      const voices = result.voices || [];
      const signature = voices.map((voice) => voice.voice_id).join(",");
      if (roomList.dataset.voiceSignature === signature) return;
      roomList.dataset.voiceSignature = signature;
      roomList.replaceChildren();

      let newestIncomingAudio = null;
      let newestIncomingId = "";
      for (const voice of voices) {
        const item = document.createElement("div");
        item.className = "oap-voice-note";

        const label = document.createElement("p");
        label.textContent = `${voice.direction === "received" ? "IN" : "OUT"} · ROOM PTT · ${voice.created_at}`;
        item.appendChild(label);

        const audio = document.createElement("audio");
        audio.controls = true;
        audio.preload = "none";
        audio.src = `/ptt/room/voice/${encodeURIComponent(voice.voice_id)}/media?peer_id=${encodeURIComponent(voice.peer_id)}`;
        item.appendChild(audio);

        if (!newestIncomingAudio && voice.direction === "received") {
          newestIncomingAudio = audio;
          newestIncomingId = voice.voice_id;
        }
        roomList.appendChild(item);
      }

      if (!roomList.childNodes.length) {
        const empty = document.createElement("p");
        empty.textContent = "No Room PTT received yet.";
        roomList.appendChild(empty);
      } else if (
        newestIncomingAudio &&
        newestIncomingId &&
        roomList.dataset.playedVoiceId !== newestIncomingId
      ) {
        roomList.dataset.playedVoiceId = newestIncomingId;
        newestIncomingAudio.play().catch(() => {});
      }
    } catch (_error) {
      roomList.replaceChildren();
      const unavailable = document.createElement("p");
      unavailable.textContent = "Room PTT history is temporarily unavailable.";
      roomList.appendChild(unavailable);
    }
  };

  const finish = () => {
    if (!state.current) return;
    const recorder = state.current.recorder;
    if (recorder.state !== "inactive") recorder.stop();
  };

  const start = async (event) => {
    event?.preventDefault();
    if (!state.ready || state.current || !browserReady()) return;

    let stream = null;
    try {
      const mimeType = preferredMime();
      stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      const recorder = new MediaRecorder(stream, { mimeType });
      const chunks = [];
      const startedAt = Date.now();

      recorder.addEventListener("dataavailable", (dataEvent) => {
        if (dataEvent.data?.size) chunks.push(dataEvent.data);
      });

      recorder.addEventListener("stop", async () => {
        if (state.autoStopTimer) {
          window.clearTimeout(state.autoStopTimer);
          state.autoStopTimer = null;
        }
        stopTracks(stream);
        const current = state.current;
        state.current = null;
        refresh();
        if (!current || current.cancelled) return;
        const blob = new Blob(chunks, { type: recorder.mimeType || mimeType });
        if (!blob.size || blob.size > state.maxBytes) return;
        const form = new FormData();
        form.append("duration_ms", String(Math.min(Date.now() - startedAt, state.maxDurationMs)));
        form.append("voice", blob, "room-ptt");
        const response = await fetch("/ptt/room", {
          method: "POST",
          body: form,
          headers: { "X-OAP-CSRF": csrfToken, Accept: "application/json" },
          credentials: "same-origin",
          cache: "no-store",
        });
        if (response.ok) await renderHistory();
      });

      state.current = { recorder, stream, cancelled: false };
      recorder.start(1000);
      state.autoStopTimer = window.setTimeout(finish, state.maxDurationMs);
      refresh();
    } catch (_error) {
      stopTracks(stream);
      state.current = null;
      refresh();
    }
  };

  roomControl.addEventListener("pointerdown", start);
  roomControl.addEventListener("pointerup", finish);
  roomControl.addEventListener("pointercancel", finish);
  roomControl.addEventListener("pointerleave", finish);
  roomControl.addEventListener("keydown", (event) => {
    if ((event.key === " " || event.key === "Enter") && !event.repeat) start(event);
  });
  roomControl.addEventListener("keyup", (event) => {
    if (event.key === " " || event.key === "Enter") finish();
  });
  if (roomStop) roomStop.addEventListener("click", finish);

  window.addEventListener("pagehide", () => {
    if (state.autoStopTimer) window.clearTimeout(state.autoStopTimer);
    if (state.current) {
      state.current.cancelled = true;
      stopTracks(state.current.stream);
      if (state.current.recorder.state !== "inactive") state.current.recorder.stop();
    }
  });

  Promise.all([apiJson("/ptt/status"), apiJson("/ptt/room/status")])
    .then(([transport, room]) => {
      state.ready =
        transport.transport_ready === true &&
        room.active === true &&
        Number(room.member_count) > 1;
      state.maxBytes = Number(transport.max_ptt_bytes) || state.maxBytes;
      state.maxDurationMs = Number(transport.max_ptt_duration_ms) || state.maxDurationMs;
      refresh();
      renderHistory();
      window.setInterval(renderHistory, 2000);
    })
    .catch(() => {
      state.ready = false;
      refresh();
    });
})();
