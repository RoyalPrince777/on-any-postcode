(() => {
  "use strict";

  const composers = document.querySelectorAll("[data-oap-link-composer]");

  composers.forEach((composer) => {
    const plus = composer.querySelector("[data-oap-plus]");
    const tray = composer.querySelector("[data-oap-tray]");
    const textarea = composer.querySelector("textarea");

    if (plus && tray) {
      plus.addEventListener("click", () => {
        const nextOpen = tray.getAttribute("data-open") !== "true";
        tray.setAttribute("data-open", String(nextOpen));
        plus.setAttribute("aria-expanded", String(nextOpen));
      });
    }

    const emojiPicker = composer.querySelector("[data-oap-emoji-picker]");
    emojiPicker?.querySelectorAll("[data-oap-emoji]").forEach((button) => {
      button.addEventListener("click", () => {
        if (!textarea || textarea.disabled || textarea.readOnly) return;
        const emoji = button.dataset.oapEmoji || "";
        if (!emoji) return;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const next = textarea.value.slice(0, start) + emoji + textarea.value.slice(end);
        if (next.length > textarea.maxLength && textarea.maxLength >= 0) return;
        textarea.setRangeText(emoji, start, end, "end");
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
        emojiPicker.open = false;
        textarea.focus();
      });
    });

    if (textarea) {
      textarea.addEventListener("input", () => {
        textarea.style.height = "auto";
        const boundedHeight = Math.min(textarea.scrollHeight, 144);
        textarea.style.height = `${boundedHeight}px`;
      });
    }
  });

  document.querySelectorAll("[data-runtime-locked]").forEach((control) => {
    control.addEventListener("click", (event) => {
      event.preventDefault();
    });
  });

  const callControls = Array.from(document.querySelectorAll("[data-oap-call-control]"));
  if (!callControls.length) {
    return;
  }

  const csrfToken = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const statusNode = document.querySelector("[data-oap-call-status]");
  const incomingNode = document.querySelector("[data-oap-incoming-calls]");
  const stage = document.querySelector("[data-oap-call-stage]");
  const stageLabel = document.querySelector("[data-oap-call-stage-label]");
  const localVideo = document.querySelector("[data-oap-local-video]");
  const remoteVideo = document.querySelector("[data-oap-remote-video]");
  const remoteAudio = document.querySelector("[data-oap-remote-audio]");
  const hangupButton = document.querySelector("[data-oap-hangup]");
  const pttHoldButton = document.querySelector("[data-oap-live-ptt-hold]");
  const pttStopButton = document.querySelector("[data-oap-live-ptt-stop]");

  const state = {
    ready: false,
    pttReady: false,
    pttHold: null,
    busy: false,
    current: null,
    peer: null,
    mode: null,
    role: null,
    answered: false,
    pc: null,
    localStream: null,
    pendingIce: [],
    signalTimer: null,
    incomingTimer: null,
  };

  const browserReady = () =>
    typeof window.RTCPeerConnection === "function" &&
    Boolean(navigator.mediaDevices?.getUserMedia);

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
    if (!selector) {
      return "";
    }
    return document.querySelector(selector)?.value || "";
  };

  const refreshControls = () => {
    callControls.forEach((control) => {
      const canUse =
        state.ready && (control.dataset.callMode !== "ptt" || state.pttReady) &&
        !state.busy && !state.current && Boolean(recipientFor(control));
      control.disabled = !canUse;
      const marker = control.querySelector("small");
      if (marker) {
        marker.textContent = canUse ? "ready" : "locked";
      }
    });
  };

  const resetMediaElements = () => {
    [localVideo, remoteVideo, remoteAudio].forEach((element) => {
      if (!element) {
        return;
      }
      element.srcObject = null;
      element.hidden = true;
    });
  };

  const stopLocalMedia = () => {
    if (state.localStream) {
      state.localStream.getTracks().forEach((track) => track.stop());
    }
    state.localStream = null;
  };

  const clearSignalTimer = () => {
    if (state.signalTimer) {
      window.clearTimeout(state.signalTimer);
      state.signalTimer = null;
    }
  };

  // The server grants an expiring speaking lease; the local WebRTC track is
  // disabled by default and immediately muted on release, failed renewal or STOP.
  // The signalling server does not intercept malicious peer-to-peer media.
  const pttFloor = (sessionId, action) =>
    api(`/linkup/calls/${encodeURIComponent(sessionId)}/ptt/floor`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });

  const pttMute = () => {
    if (state.mode === "ptt") {
      state.localStream?.getAudioTracks().forEach((track) => { track.enabled = false; });
    }
    pttHoldButton?.setAttribute("aria-pressed", "false");
  };

  const silencePtt = () => {
    const hold = state.pttHold;
    state.pttHold = null;
    pttMute();
    if (!hold) return;
    hold.released = true;
    for (const timer of [hold.deadline, hold.renewTimer, hold.pollTimer]) {
      if (timer) window.clearTimeout(timer);
    }
    // A pending acquisition is released when its response arrives.
    if (hold.granted) {
      pttFloor(hold.sessionId, "release").catch(() => {});
    }
  };

  const pttDeadline = (hold) => {
    if (hold.deadline) window.clearTimeout(hold.deadline);
    // Shorter than the eight-second server lease: never rely on an expired grant.
    hold.deadline = window.setTimeout(() => {
      if (state.pttHold === hold) {
        silencePtt();
        setStatus("PTT lease expired. Microphone muted.");
      }
    }, 6000);
  };

  const pollPttFloor = async (hold) => {
    if (state.pttHold !== hold || hold.released) return;
    try {
      const value = await api(`/linkup/calls/${encodeURIComponent(hold.sessionId)}/ptt/floor`);
      if (state.pttHold !== hold || hold.released) return;
      if (value.holder_id !== hold.holderId) {
        silencePtt();
        setStatus("PTT floor revoked. Microphone muted.");
        return;
      }
    } catch (_error) {
      if (state.pttHold === hold) {
        silencePtt();
        setStatus("PTT floor unavailable. Microphone muted.");
      }
      return;
    }
    hold.pollTimer = window.setTimeout(() => pollPttFloor(hold), 1000);
  };

  const renewPttFloor = async (hold) => {
    if (state.pttHold !== hold || hold.released) return;
    try {
      const value = await pttFloor(hold.sessionId, "acquire");
      if (state.pttHold !== hold || hold.released) {
        if (value.granted) pttFloor(hold.sessionId, "release").catch(() => {});
        return;
      }
      if (!value.granted || value.holder_id !== hold.holderId) throw new Error("ptt_floor_revoked");
      pttDeadline(hold);
      hold.renewTimer = window.setTimeout(() => renewPttFloor(hold), 2500);
    } catch (_error) {
      if (state.pttHold === hold) {
        silencePtt();
        setStatus("PTT renewal failed. Microphone muted.");
      }
    }
  };

  const beginLivePtt = async (source, pointerId = null) => {
    if (state.mode !== "ptt" || !state.current || !state.answered ||
        state.pc?.connectionState !== "connected" || state.pttHold || !pttHoldButton ||
        pttHoldButton.disabled) return;
    const hold = { sessionId: state.current, released: false, granted: false, pointerId, source };
    state.pttHold = hold;
    pttMute();
    setStatus("Requesting private PTT floor…");
    try {
      const value = await pttFloor(hold.sessionId, "acquire");
      if (state.pttHold !== hold || hold.released || state.current !== hold.sessionId) {
        if (value.granted) pttFloor(hold.sessionId, "release").catch(() => {});
        return;
      }
      if (!value.granted || !value.holder_id || value.lease_seconds !== 8) throw new Error("ptt_floor_denied");
      hold.granted = true;
      hold.holderId = value.holder_id;
      pttDeadline(hold);
      state.localStream?.getAudioTracks().forEach((track) => { track.enabled = true; });
      pttHoldButton.setAttribute("aria-pressed", "true");
      setStatus("PTT speaking. Release to mute.");
      hold.renewTimer = window.setTimeout(() => renewPttFloor(hold), 2500);
      hold.pollTimer = window.setTimeout(() => pollPttFloor(hold), 1000);
    } catch (_error) {
      if (state.pttHold === hold) {
        silencePtt();
        setStatus("PTT floor denied. Microphone muted.");
      }
    }
  };

  const endLivePtt = (source, pointerId = null) => {
    const hold = state.pttHold;
    if (!hold || hold.source !== source) return;
    if (source === "pointer" && hold.pointerId !== pointerId) return;
    silencePtt();
    setStatus("PTT microphone muted.");
  };

  pttHoldButton?.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 || pttHoldButton.disabled) return;
    event.preventDefault();
    beginLivePtt("pointer", event.pointerId);
  });
  window.addEventListener("pointerup", (event) => endLivePtt("pointer", event.pointerId));
  window.addEventListener("pointercancel", () => silencePtt());
  pttHoldButton?.addEventListener("keydown", (event) => {
    if ((event.key === " " || event.key === "Enter") && !event.repeat) {
      event.preventDefault();
      beginLivePtt("keyboard");
    }
  });
  pttHoldButton?.addEventListener("keyup", (event) => {
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      endLivePtt("keyboard");
    }
  });
  pttHoldButton?.addEventListener("blur", silencePtt);
  window.addEventListener("blur", silencePtt);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) silencePtt();
  });
  pttStopButton?.addEventListener("click", async () => {
    if (state.mode !== "ptt" || !state.current) return;
    const sessionId = state.current;
    silencePtt();
    try {
      const stopped = await pttFloor(sessionId, "stop");
      if (!stopped.stopped) throw new Error("ptt_stop_not_confirmed");
      if (pttHoldButton) pttHoldButton.disabled = true;
      if (pttStopButton) pttStopButton.disabled = true;
      setStatus("Private PTT floor stopped for this call.");
    } catch (_error) {
      setStatus("PTT STOP could not be confirmed. Local microphone muted.");
    }
  });

  const resetCurrent = () => {
    silencePtt();
    clearSignalTimer();
    if (state.pc) {
      state.pc.onicecandidate = null;
      state.pc.ontrack = null;
      state.pc.onconnectionstatechange = null;
      state.pc.close();
    }
    state.pc = null;
    stopLocalMedia();
    resetMediaElements();
    state.busy = false;
    state.current = null;
    state.peer = null;
    state.mode = null;
    state.role = null;
    state.answered = false;
    state.pendingIce = [];
    if (stage) {
      stage.hidden = true;
    }
    refreshControls();
  };

  const sendSignalFor = (sessionId, peerId, eventType, payload = {}) =>
    api("/linkup/signalling/events", {
      method: "POST",
      body: JSON.stringify({
        recipient_id: peerId,
        session_id: sessionId,
        event_type: eventType,
        payload,
      }),
    });

  const finishServerSession = async (sessionId, outcome) => {
    try {
      await api(`/linkup/calls/${encodeURIComponent(sessionId)}/finish`, {
        method: "POST",
        body: JSON.stringify({ outcome }),
      });
    } catch (error) {
      if (error.status !== 404) {
        throw error;
      }
    }
  };

  const finishCurrent = async ({ remote = false, failed = false } = {}) => {
    silencePtt();
    const sessionId = state.current;
    const peerId = state.peer;
    const role = state.role;
    const answered = state.answered;
    if (!sessionId) {
      return;
    }

    if (!remote && peerId) {
      try {
        await sendSignalFor(sessionId, peerId, "hangup", {
          reason: failed ? "failed" : "ended",
        });
      } catch (_error) {
        // Session teardown must continue even if signalling has already closed.
      }
    }

    if (!remote) {
      const outcome = failed
        ? "failed"
        : answered
          ? "completed"
          : role === "caller"
            ? "cancelled"
            : "failed";
      try {
        await finishServerSession(sessionId, outcome);
      } catch (_error) {
        // Local media cleanup is mandatory even if the audit endpoint is unavailable.
      }
    }

    resetCurrent();
    setStatus(remote ? "The other person ended the Link session." : "Link session ended.");
    scheduleIncomingPoll(800);
  };

  const flushPendingIce = async () => {
    if (!state.pc?.remoteDescription) {
      return;
    }
    const candidates = state.pendingIce.splice(0);
    for (const candidate of candidates) {
      await state.pc.addIceCandidate(candidate);
    }
  };

  const handleSignal = async (event) => {
    if (!state.pc || !state.current || event.sender_id !== state.peer) {
      return;
    }
    const payload = event.payload || {};
    if (event.event_type === "offer" && state.role === "callee") {
      if (!state.pc.remoteDescription) {
        await state.pc.setRemoteDescription(payload);
        await flushPendingIce();
        const answer = await state.pc.createAnswer();
        await state.pc.setLocalDescription(answer);
        state.answered = true;
        await sendSignalFor(state.current, state.peer, "answer", {
          type: state.pc.localDescription.type,
          sdp: state.pc.localDescription.sdp,
        });
      }
      return;
    }
    if (event.event_type === "answer" && state.role === "caller") {
      if (!state.pc.remoteDescription) {
        await state.pc.setRemoteDescription(payload);
        state.answered = true;
        await flushPendingIce();
      }
      return;
    }
    if (event.event_type === "ice") {
      if (state.pc.remoteDescription) {
        await state.pc.addIceCandidate(payload);
      } else {
        state.pendingIce.push(payload);
      }
      return;
    }
    if (event.event_type === "hangup") {
      await finishCurrent({ remote: true });
    }
  };

  const acknowledgeSignal = async (eventId) => {
    try {
      await api(`/linkup/signalling/events/${encodeURIComponent(eventId)}/ack`, {
        method: "POST",
        body: "{}",
      });
    } catch (_error) {
      // Expiry or a concurrent acknowledgement is harmless.
    }
  };

  const pollSignals = async () => {
    if (!state.current) {
      return;
    }
    const sessionId = state.current;
    try {
      const result = await api(
        `/linkup/signalling/events?session_id=${encodeURIComponent(sessionId)}&limit=100`,
      );
      for (const event of result.events || []) {
        await handleSignal(event);
        if (event.event_id) {
          await acknowledgeSignal(event.event_id);
        }
        if (!state.current) {
          return;
        }
      }
    } catch (error) {
      if (
        error.code === "active_call_session_required" ||
        error.code === "accepted_link_required" ||
        error.code === "link_blocked"
      ) {
        await finishCurrent({ remote: true });
        return;
      }
      setStatus("Call signalling is temporarily unavailable.");
    }
    if (state.current) {
      state.signalTimer = window.setTimeout(pollSignals, 1000);
    }
  };

  const attachRemoteTrack = (event) => {
    const stream = event.streams?.[0] || new MediaStream([event.track]);
    if (state.mode === "face_up" && remoteVideo) {
      remoteVideo.srcObject = stream;
      remoteVideo.hidden = false;
      return;
    }
    if (remoteAudio) {
      remoteAudio.srcObject = stream;
      remoteAudio.hidden = false;
    }
  };

  const openPeerSession = async ({ sessionId, peerId, mode, role }) => {
    const credentials = await api("/linkup/turn/credentials", {
      method: "POST",
      body: JSON.stringify({ recipient_id: peerId }),
    });
    if (!credentials.relay_verified || !Array.isArray(credentials.ice_servers)) {
      throw new Error("turn_relay_not_verified");
    }

    const localStream = await navigator.mediaDevices.getUserMedia({
      audio: true,
      video: mode === "face_up",
    });
    // A PTT call begins silent, before a peer connection or offer exists.
    if (mode === "ptt") localStream.getAudioTracks().forEach((track) => { track.enabled = false; });
    let pc;
    try {
      pc = new RTCPeerConnection({ iceServers: credentials.ice_servers });
    } catch (error) {
      // Capture succeeded but peer setup failed: never leave a microphone or camera live.
      localStream.getTracks().forEach((track) => track.stop());
      throw error;
    }

    state.current = sessionId;
    state.peer = peerId;
    state.mode = mode;
    state.role = role;
    state.answered = role === "callee";
    state.localStream = localStream;
    state.pc = pc;
    state.pendingIce = [];
    state.busy = false;

    localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));
    pc.ontrack = attachRemoteTrack;
    pc.onicecandidate = (event) => {
      if (!event.candidate || !state.current || !state.peer) {
        return;
      }
      sendSignalFor(state.current, state.peer, "ice", event.candidate.toJSON()).catch(() => {
        setStatus("A private network candidate could not be exchanged.");
      });
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === "connected") {
        state.answered = true;
        setStatus(mode === "face_up" ? "Link Call connected." : mode === "ptt" ? "Private PTT connected. Hold to speak." : "Call connected.");
      } else if (pc.connectionState === "failed") {
        finishCurrent({ failed: true });
      }
    };

    if (stage) {
      stage.hidden = false;
    }
    if (stageLabel) {
      stageLabel.textContent = mode === "face_up" ? "Private Link Call" : mode === "ptt" ? "Private Live PTT" : "Private Call";
    }
    if (pttHoldButton) {
      pttHoldButton.hidden = mode !== "ptt";
      pttHoldButton.disabled = mode !== "ptt";
      pttHoldButton.setAttribute("aria-pressed", "false");
    }
    if (pttStopButton) {
      pttStopButton.hidden = mode !== "ptt";
      pttStopButton.disabled = mode !== "ptt";
    }
    if (mode === "face_up" && localVideo) {
      localVideo.srcObject = localStream;
      localVideo.hidden = false;
    }
    refreshControls();
    clearSignalTimer();
    state.signalTimer = window.setTimeout(pollSignals, 50);

    if (role === "caller") {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await sendSignalFor(sessionId, peerId, "offer", {
        type: pc.localDescription.type,
        sdp: pc.localDescription.sdp,
      });
      setStatus(mode === "face_up" ? "Link Call is ringing…" : mode === "ptt" ? "Private PTT is ringing…" : "Call is ringing…");
    } else {
      setStatus(mode === "face_up" ? "Opening private Link Call…" : mode === "ptt" ? "Opening private PTT…" : "Opening private Call…");
    }
  };

  const startOutgoing = async (control) => {
    if (!state.ready || state.busy || state.current) {
      return;
    }
    const peerId = recipientFor(control);
    const mode = control.dataset.callMode === "face_up" ? "face_up" : control.dataset.callMode === "ptt" ? "ptt" : "call";
    if (!peerId) {
      setStatus("Choose a Certified member first.");
      return;
    }
    state.busy = true;
    refreshControls();
    if (incomingNode) {
      incomingNode.hidden = true;
    }
    setStatus(mode === "face_up" ? "Starting Link Call…" : mode === "ptt" ? "Starting private PTT…" : "Starting Call…");
    let sessionId = null;
    try {
      if (mode === "ptt") {
        const floor = await api("/linkup/ptt/status");
        if (!floor.ready || floor.server_controls_media !== false) throw new Error("ptt_floor_unavailable");
      }
      const created = await api("/linkup/calls", {
        method: "POST",
        body: JSON.stringify({ recipient_id: peerId, mode }),
      });
      sessionId = created.session_id;
      await openPeerSession({ sessionId, peerId, mode, role: "caller" });
    } catch (error) {
      if (sessionId) {
        try {
          await finishServerSession(sessionId, "failed");
        } catch (_finishError) {
          // The call remains fail-closed even if audit cleanup is temporarily unavailable.
        }
      }
      resetCurrent();
      setStatus(
        error.name === "NotAllowedError"
          ? "Camera or microphone permission was not granted."
          : "Call could not start. Every runtime gate remains fail-closed.",
      );
    }
  };

  const declineIncoming = async (session) => {
    if (state.busy || state.current) {
      return;
    }
    state.busy = true;
    refreshControls();
    if (incomingNode) {
      incomingNode.hidden = true;
    }
    try {
      await sendSignalFor(session.session_id, session.peer_id, "hangup", { reason: "declined" });
    } catch (_error) {
      // The audit state still closes the ringing session if signalling is unavailable.
    }
    try {
      await finishServerSession(session.session_id, "declined");
    } catch (_error) {
      setStatus("Incoming Call could not be closed cleanly.");
    }
    state.busy = false;
    refreshControls();
    scheduleIncomingPoll(250);
  };

  const answerIncoming = async (session) => {
    if (state.busy || state.current) {
      return;
    }
    state.busy = true;
    refreshControls();
    if (incomingNode) {
      incomingNode.hidden = true;
    }
    setStatus(session.mode === "face_up" ? "Answering Link Call…" : session.mode === "ptt" ? "Answering private PTT…" : "Answering Call…");
    try {
      if (session.mode === "ptt") {
        const floor = await api("/linkup/ptt/status");
        if (!floor.ready || floor.server_controls_media !== false) throw new Error("ptt_floor_unavailable");
      }
      await api(`/linkup/calls/${encodeURIComponent(session.session_id)}/answer`, {
        method: "POST",
        body: "{}",
      });
      await openPeerSession({
        sessionId: session.session_id,
        peerId: session.peer_id,
        mode: session.mode,
        role: "callee",
      });
    } catch (error) {
      try {
        await finishServerSession(session.session_id, "failed");
      } catch (_finishError) {
        // Keep local cleanup deterministic.
      }
      resetCurrent();
      setStatus(
        error.name === "NotAllowedError"
          ? "Camera or microphone permission was not granted."
          : "Incoming Call could not be opened.",
      );
    }
  };

  const renderIncoming = (sessions) => {
    if (!incomingNode) {
      return;
    }
    incomingNode.replaceChildren();
    const incoming = sessions.filter(
      (session) => session.direction === "incoming" && session.state === "ringing",
    );
    incomingNode.hidden = incoming.length === 0;
    incoming.forEach((session) => {
      const card = document.createElement("div");
      const label = document.createElement("p");
      label.textContent = session.mode === "face_up" ? "Incoming Link Call" : session.mode === "ptt" ? "Incoming private PTT" : "Incoming Call";
      const answer = document.createElement("button");
      answer.type = "button";
      answer.className = "mc-primary";
      answer.textContent = "Answer";
      answer.addEventListener("click", () => answerIncoming(session));
      const decline = document.createElement("button");
      decline.type = "button";
      decline.className = "mc-secondary";
      decline.textContent = "Decline";
      decline.addEventListener("click", () => declineIncoming(session));
      card.append(label, answer, decline);
      incomingNode.append(card);
    });
  };

  const pollIncoming = async () => {
    state.incomingTimer = null;
    if (!state.ready || state.busy || state.current) {
      return;
    }
    try {
      const result = await api("/linkup/calls/active");
      renderIncoming(result.sessions || []);
    } catch (_error) {
      if (incomingNode) {
        incomingNode.hidden = true;
      }
    }
    scheduleIncomingPoll(3000);
  };

  function scheduleIncomingPoll(delay = 3000) {
    if (state.incomingTimer) {
      window.clearTimeout(state.incomingTimer);
    }
    if (state.ready && !state.busy && !state.current) {
      state.incomingTimer = window.setTimeout(pollIncoming, delay);
    }
  }

  const loadReadiness = async () => {
    if (!csrfToken || !browserReady()) {
      state.ready = false;
      refreshControls();
      setStatus("This browser cannot open Certified Call or Link Call sessions.");
      return;
    }
    try {
      const [calls, signalling, turn] = await Promise.all([
        api("/linkup/calls/status"),
        api("/linkup/signalling/status"),
        api("/linkup/turn/status"),
      ]);
      state.ready = Boolean(
        calls.ready &&
          calls.records_media === false &&
          signalling.ready &&
          turn.ready &&
          turn.owned &&
          turn.relay_verified,
      );
    } catch (_error) {
      state.ready = false;
    }
    if (state.ready) {
      try {
        const ptt = await api("/linkup/ptt/status");
        state.pttReady = ptt.ready === true && ptt.server_controls_media === false;
      } catch (_error) {
        state.pttReady = false;
      }
    } else {
      state.pttReady = false;
    }
    refreshControls();
    if (state.ready) {
      setStatus("Call and Link Call runtime gates are Certified and ready.");
      scheduleIncomingPoll(250);
    } else {
      setStatus("Call and Link Call stay locked until every first-party runtime gate is ready.");
    }
  };

  callControls.forEach((control) => {
    control.addEventListener("click", () => startOutgoing(control));
    const selector = control.dataset.recipientSource;
    if (selector) {
      document.querySelector(selector)?.addEventListener("change", refreshControls);
    }
  });

  hangupButton?.addEventListener("click", () => finishCurrent());
  window.addEventListener("pagehide", () => {
    silencePtt();
    clearSignalTimer();
    if (state.incomingTimer) {
      window.clearTimeout(state.incomingTimer);
    }
    stopLocalMedia();
    if (state.pc) {
      state.pc.close();
    }
  });

  refreshControls();
  loadReadiness();
})();
