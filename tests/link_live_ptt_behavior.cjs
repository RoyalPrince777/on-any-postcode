"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const source = fs.readFileSync(path.resolve(__dirname, "../static/linkup_realtime.js"), "utf8");
const settle = async () => {
  for (let i = 0; i < 18; i += 1) await new Promise((resolve) => setImmediate(resolve));
};
const deferred = () => {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
};
const element = (dataset = {}) => {
  const events = new Map();
  return {
    dataset, disabled: false, hidden: false, textContent: "", attributes: {}, srcObject: null,
    addEventListener(name, callback) {
      const list = events.get(name) || [];
      list.push(callback);
      events.set(name, list);
    },
    emit(name, data = {}) {
      for (const callback of events.get(name) || []) callback({
        button: 0, pointerId: 7, key: "", repeat: false,
        preventDefault() {}, ...data,
      });
    },
    setAttribute(name, value) { this.attributes[name] = value; },
    getAttribute(name) { return this.attributes[name] ?? null; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    replaceChildren() {},
    append() {},
  };
};

async function runScenario({ delayedAcquire = false, stopAfterGrant = false }) {
  const call = element({ callMode: "ptt", recipientId: "peer-1" });
  call.disabled = true;
  const hold = element();
  hold.disabled = true;
  hold.hidden = true;
  const stop = element();
  stop.disabled = true;
  stop.hidden = true;
  const status = element();
  const stage = element();
  stage.hidden = true;
  const stageLabel = element();
  const remoteAudio = element();
  const hangup = element();
  const win = element();
  const doc = element();
  doc.hidden = false;

  const audioTrack = { enabled: true, stopped: false, stop() { this.stopped = true; } };
  const stream = {
    getTracks: () => [audioTrack],
    getAudioTracks: () => [audioTrack],
  };
  let lastPc = null;
  class FakePc {
    constructor() {
      this.connectionState = "new";
      this.localDescription = null;
      this.remoteDescription = null;
      this.onconnectionstatechange = null;
      this.onicecandidate = null;
      this.ontrack = null;
      lastPc = this;
    }
    addTrack() {}
    async createOffer() { return { type: "offer", sdp: "oap-ptt-offer" }; }
    async setLocalDescription(value) { this.localDescription = value; }
    async createAnswer() { return { type: "answer", sdp: "oap-ptt-answer" }; }
    async setRemoteDescription(value) { this.remoteDescription = value; }
    async addIceCandidate() {}
    close() { this.connectionState = "closed"; }
  }

  const acquireGate = deferred();
  const actions = [];
  let floorHolder = null;
  let floorStopped = false;
  let acquireCount = 0;

  const response = (payload, ok = true, code = 200) => ({
    ok, status: code, json: async () => payload,
  });
  const fetchStub = async (url, options = {}) => {
    const method = options.method || "GET";
    if (url === "/linkup/calls/status") return response({ ready: true, records_media: false });
    if (url === "/linkup/signalling/status") return response({ ready: true });
    if (url === "/linkup/turn/status") return response({ ready: true, owned: true, relay_verified: true });
    if (url === "/linkup/ptt/status") return response({ ready: true, schema_ready: true, mode_ready: true, server_controls_media: false });
    if (url === "/linkup/calls/active") return response({ sessions: [] });
    if (url === "/linkup/calls" && method === "POST") {
      const body = JSON.parse(options.body);
      assert.equal(body.mode, "ptt");
      assert.equal(body.recipient_id, "peer-1");
      return response({ session_id: "session-1" }, true, 201);
    }
    if (url === "/linkup/turn/credentials" && method === "POST") {
      return response({ relay_verified: true, ice_servers: [{ urls: ["turn:oap.invalid"] }] });
    }
    if (url === "/linkup/signalling/events" && method === "POST") return response({});
    if (url.startsWith("/linkup/signalling/events?")) return response({ events: [] });
    if (url.includes("/ptt/floor")) {
      if (method === "GET") return response({ holder_id: floorHolder, stopped: floorStopped, lease_seconds: 8 });
      const action = JSON.parse(options.body).action;
      actions.push(action);
      if (action === "acquire") {
        acquireCount += 1;
        if (floorStopped) return response({ error: { code: "ptt_floor_stopped" } }, false, 409);
        const granted = { granted: true, holder_id: "me", lease_seconds: 8 };
        if (delayedAcquire && acquireCount === 1) return acquireGate.promise;
        floorHolder = "me";
        return response(granted);
      }
      if (action === "release") {
        floorHolder = null;
        return response({ granted: false, holder_id: null, stopped: floorStopped });
      }
      if (action === "stop") {
        floorHolder = null;
        floorStopped = true;
        return response({ granted: false, holder_id: null, stopped: true });
      }
    }
    if (url.endsWith("/finish") && method === "POST") return response({ finished: true });
    throw new Error("Unexpected fetch " + method + " " + url);
  };

  const selectorMap = new Map([
    ['meta[name="oap-csrf-token"]', { content: "csrf-token" }],
    ["[data-oap-call-status]", status],
    ["[data-oap-incoming-calls]", null],
    ["[data-oap-call-stage]", stage],
    ["[data-oap-call-stage-label]", stageLabel],
    ["[data-oap-local-video]", null],
    ["[data-oap-remote-video]", null],
    ["[data-oap-remote-audio]", remoteAudio],
    ["[data-oap-hangup]", hangup],
    ["[data-oap-live-ptt-hold]", hold],
    ["[data-oap-live-ptt-stop]", stop],
  ]);
  doc.querySelector = (selector) => selectorMap.get(selector) || null;
  doc.querySelectorAll = (selector) => {
    if (selector === "[data-oap-call-control]") return [call];
    if (selector === "[data-oap-link-composer]" || selector === "[data-runtime-locked]") return [];
    return [];
  };
  doc.createElement = () => element();

  win.RTCPeerConnection = FakePc;
  win.setTimeout = () => 1;
  win.clearTimeout = () => {};
  const context = {
    document: doc,
    window: win,
    navigator: { mediaDevices: { getUserMedia: async () => stream } },
    RTCPeerConnection: FakePc,
    MediaStream: class {},
    Headers,
    fetch: fetchStub,
    Event: class {},
    console,
    encodeURIComponent,
    JSON,
    Error,
  };
  vm.runInNewContext(source, context, { filename: "linkup_realtime.js" });
  await settle();

  assert.equal(call.disabled, false, "PTT entry must unlock only after runtime readiness");
  call.emit("click");
  await settle();
  assert.ok(lastPc, "PTT must create the existing WebRTC peer connection");
  assert.equal(audioTrack.enabled, false, "PTT audio must begin muted before connection");
  assert.equal(stageLabel.textContent, "Private Live PTT");
  assert.equal(hold.hidden, false);
  assert.equal(stop.hidden, false);

  lastPc.connectionState = "connected";
  lastPc.onconnectionstatechange();
  await settle();
  assert.match(status.textContent, /Private PTT connected/);

  hold.emit("pointerdown", { pointerId: 7 });
  if (delayedAcquire) {
    await settle();
    assert.equal(audioTrack.enabled, false, "late floor response must not open microphone before grant");
    win.emit("pointerup", { pointerId: 7 });
    await settle();
    acquireGate.resolve(response({ granted: true, holder_id: "me", lease_seconds: 8 }));
    await settle();
    assert.equal(audioTrack.enabled, false, "release-before-grant must remain muted");
    assert.deepEqual(actions.slice(0, 2), ["acquire", "release"]);
    return;
  }

  await settle();
  assert.equal(audioTrack.enabled, true, "server floor grant must open local audio track");
  assert.equal(hold.attributes["aria-pressed"], "true");

  if (stopAfterGrant) {
    stop.emit("click");
    await settle();
    assert.equal(audioTrack.enabled, false, "STOP must mute local audio immediately");
    assert.equal(floorStopped, true);
    assert.equal(hold.disabled, true);
    assert.equal(stop.disabled, true);
    assert.ok(actions.includes("stop"));
    return;
  }

  win.emit("pointerup", { pointerId: 7 });
  await settle();
  assert.equal(audioTrack.enabled, false, "release must mute local track");
  assert.equal(hold.attributes["aria-pressed"], "false");
  assert.deepEqual(actions.slice(0, 2), ["acquire", "release"]);
}

(async () => {
  await runScenario({});
  await runScenario({ delayedAcquire: true });
  await runScenario({ stopAfterGrant: true });
  process.stdout.write("Live PTT controller passed: silent start, grant-to-speak, release, late-grant revocation and STOP.\n");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
