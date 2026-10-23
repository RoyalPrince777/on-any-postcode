(() => {
  "use strict";
  const talk = document.querySelector("[data-oap-ptt-control]");
  const stop = document.querySelector("[data-oap-ptt-stop]");
  if (!talk || !stop) return;
  const csrf = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const status = talk.parentElement.querySelector('[role="status"]');
  const setStatus = (message) => { if (status) status.textContent = message; };
  let pc = null;
  let stream = null;
  let remote = null;
  let timer = null;
  let running = false;
  let holding = false;
  let starting = false;
  let pendingCandidates = [];
  let generation = 0;
  const endpoint = "/ptt/live";
  const signal = async (kind, payload) => {
    const response = await fetch(endpoint + "/signal", {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: JSON.stringify({ kind, payload }),
    });
    if (!response.ok) throw new Error("Signalling unavailable");
  };
  const release = () => {
    holding = false;
    if (stream) stream.getAudioTracks().forEach((track) => { track.enabled = false; });
    talk.setAttribute("aria-pressed", "false");
    if (running) setStatus(pc?.connectionState === "connected" ? "Listening · hold to talk" : "Connecting…");
  };
  const close = (message) => {
    generation += 1;
    running = false;
    release();
    if (timer) clearTimeout(timer);
    timer = null;
    if (pc) { pc.onicecandidate = null; pc.ontrack = null; pc.close(); }
    pc = null;
    pendingCandidates = [];
    if (stream) stream.getTracks().forEach((track) => track.stop());
    stream = null;
    if (remote) { remote.pause(); remote.srcObject = null; remote.remove(); }
    remote = null;
    talk.disabled = true;
    stop.hidden = true;
    setStatus(message);
  };
  const applySignal = async (item) => {
    if (!pc) return;
    if (item.kind === "hangup") { close("Other phone disconnected"); return; }
    if (item.kind === "offer") {
      if (pc.signalingState !== "stable") return;
      await pc.setRemoteDescription(item.payload);
      for (const candidate of pendingCandidates.splice(0)) await pc.addIceCandidate(candidate);
      await pc.setLocalDescription(await pc.createAnswer());
      await signal("answer", { type: pc.localDescription.type, sdp: pc.localDescription.sdp });
    } else if (item.kind === "answer" && pc.signalingState === "have-local-offer") {
      await pc.setRemoteDescription(item.payload);
      for (const candidate of pendingCandidates.splice(0)) await pc.addIceCandidate(candidate);
    } else if (item.kind === "candidate") {
      if (pc.remoteDescription) await pc.addIceCandidate(item.payload);
      else pendingCandidates.push(item.payload);
    }
  };
  const poll = async (token) => {
    if (!running || token !== generation) return;
    try {
      const response = await fetch(endpoint + "/signals", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error("Pair expired or signalling unavailable");
      const data = await response.json();
      for (const item of data.signals || []) {
        if (!running || token !== generation) break;
        await applySignal(item);
      }
    } catch (_error) { close("Connection interrupted · reconnect manually"); return; }
    if (running && token === generation) timer = setTimeout(() => poll(token), 1200);
  };
  const start = async () => {
    if (starting || running) return;
    starting = true;
    const token = ++generation;
    try {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia || !window.RTCPeerConnection)
        throw new Error("Secure browser with WebRTC required");
      setStatus("Requesting microphone permission…");
      const local = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      if (token !== generation) { local.getTracks().forEach((track) => track.stop()); return; }
      stream = local;
      release();
      pc = new RTCPeerConnection({ iceServers: [] });
      stream.getAudioTracks().forEach((track) => pc.addTrack(track, stream));
      remote = document.createElement("audio");
      remote.autoplay = true;
      remote.setAttribute("playsinline", "");
      remote.setAttribute("aria-label", "Live incoming audio");
      talk.parentElement.appendChild(remote);
      pc.ontrack = (event) => { remote.srcObject = event.streams[0]; remote.play().catch(() => setStatus("Tap to allow incoming audio")); };
      pc.onicecandidate = (event) => {
        if (event.candidate && running) signal("candidate", event.candidate.toJSON()).catch(() => close("Signalling failed"));
      };
      pc.onconnectionstatechange = () => {
        if (pc?.connectionState === "connected") { talk.disabled = false; setStatus("Listening · hold to talk"); }
        if (["failed", "closed", "disconnected"].includes(pc?.connectionState)) close("Connection lost · reconnect manually");
      };
      running = true;
      stop.hidden = false;
      setStatus("Connecting…");
      // Deterministic initiator selection requires the server to expose local identity.
      const localId = document.body.dataset.oapPttIdentity;
      const peerId = document.querySelector("#ptt-guest-peer")?.value;
      if (!localId || !peerId) throw new Error("Pair identity unavailable");
      if (localId < peerId) {
        await pc.setLocalDescription(await pc.createOffer());
        await signal("offer", { type: pc.localDescription.type, sdp: pc.localDescription.sdp });
      }
      poll(token);
    } catch (error) { close(error.message || "Connection unavailable"); }
    finally { starting = false; }
  };
  talk.addEventListener("pointerdown", (event) => {
    if (!running || talk.disabled || pc?.connectionState !== "connected") return;
    event.preventDefault();
    holding = true;
    stream?.getAudioTracks().forEach((track) => { track.enabled = true; });
    talk.setAttribute("aria-pressed", "true");
    talk.setPointerCapture(event.pointerId);
    setStatus("Transmitting · release to listen");
  });
  ["pointerup", "pointercancel", "lostpointercapture", "pointerleave"].forEach((name) => talk.addEventListener(name, release));
  window.addEventListener("blur", release);
  document.addEventListener("visibilitychange", () => { if (document.hidden) release(); });
  stop.addEventListener("click", () => {
    const wasRunning = running;
    close("Disconnected");
    if (wasRunning) signal("hangup", {}).catch(() => {});
  });
  window.addEventListener("pagehide", () => close("Disconnected"));
  const connect = document.createElement("button");
  connect.type = "button";
  connect.textContent = "Connect live audio";
  connect.addEventListener("click", start);
  talk.before(connect);
})();
