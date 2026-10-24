"use strict";
// Execute the shipped PTT browser script with controlled DOM/WebRTC surfaces.
// This checks actual event handlers and fetch headers; it is NOT two-phone proof.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

async function main() {
  const requests = [];
  const token = "first-party-csrf-value";
  const listeners = () => Object.create(null);
  const makeElement = () => ({
    listeners: listeners(),
    disabled: false,
    hidden: false,
    attributes: Object.create(null),
    addEventListener(name, callback) { this.listeners[name] = callback; },
    setAttribute(name, value) { this.attributes[name] = value; },
    setPointerCapture(pointerId) { this.pointerCaptured = pointerId; },
    before(sibling) { this.beforeSibling = sibling; },
    appendChild(child) { this.lastChild = child; },
    pause() { this.paused = true; },
    remove() { this.removed = true; },
    play() { return Promise.resolve(); },
  });
  const talk = makeElement();
  const stop = makeElement();
  stop.hidden = true;
  const status = { textContent: "" };
  const parent = {
    querySelector(selector) {
      assert.equal(selector, '[role="status"]');
      return status;
    },
    appendChild(child) { this.lastChild = child; },
  };
  talk.parentElement = parent;
  const documentListeners = listeners();
  const document = {
    body: { dataset: { oapPttIdentity: "00000000-0000-4000-8000-000000000001" } },
    hidden: false,
    querySelector(selector) {
      if (selector === "[data-oap-ptt-control]") return talk;
      if (selector === "[data-oap-ptt-stop]") return stop;
      if (selector === 'meta[name="oap-csrf-token"]') return { content: token };
      if (selector === "#ptt-guest-peer") return {
        value: "00000000-0000-4000-8000-000000000002",
      };
      return null;
    },
    createElement(_tag) { return makeElement(); },
    addEventListener(name, callback) { documentListeners[name] = callback; },
  };

  const track = {
    enabled: true, stopped: false,
    stop() { this.stopped = true; },
  };
  const localStream = {
    getAudioTracks() { return [track]; },
    getTracks() { return [track]; },
  };
  class FakePeer {
    static instances = [];
    constructor(config) {
      assert.deepEqual(JSON.parse(JSON.stringify(config)), { iceServers: [] });
      this.connectionState = "new";
      this.signalingState = "stable";
      this.localDescription = null;
      this.closed = false;
      FakePeer.instances.push(this);
    }
    addTrack(receivedTrack, receivedStream) {
      assert.equal(receivedTrack, track);
      assert.equal(receivedStream, localStream);
    }
    async createOffer() { return { type: "offer", sdp: "v=0\r\n" }; }
    async setLocalDescription(description) {
      this.localDescription = description;
      this.signalingState = "have-local-offer";
    }
    close() { this.closed = true; }
  }

  const sandbox = {
    document,
    navigator: { mediaDevices: { getUserMedia: async (constraints) => {
      assert.equal(constraints.audio, true);
      assert.equal(constraints.video, false);
      return localStream;
    } } },
    RTCPeerConnection: FakePeer,
    window: {
      isSecureContext: true,
      RTCPeerConnection: FakePeer,
      addEventListener() {},
    },
    fetch: async (url, opts) => {
      requests.push({ url, opts });
      if (url === "/ptt/live/signals") {
        return { ok: true, json: async () => ({ signals: [] }) };
      }
      return { ok: true, status: 202 };
    },
    setTimeout: () => 1,
    clearTimeout: () => {},
    console,
  };
  vm.runInNewContext(
    fs.readFileSync(path.join(__dirname, "..", "static", "ptt_live.js"), "utf8"),
    sandbox,
    { filename: "ptt_live.js" },
  );
  const connect = talk.beforeSibling;
  assert.equal(connect.textContent, "Connect live audio");
  assert.equal(typeof connect.listeners.click, "function");
  await connect.listeners.click();

  const sentOffer = requests.find((request) => request.url === "/ptt/live/signal");
  assert.ok(sentOffer, "Initiator must send a signalling offer");
  assert.equal(sentOffer.opts.headers["X-OAP-CSRF"], token);
  assert.equal(sentOffer.opts.headers["X-CSRF-Token"], undefined);
  assert.equal(sentOffer.opts.credentials, "same-origin");
  assert.equal(JSON.parse(sentOffer.opts.body).kind, "offer");

  const peer = FakePeer.instances[0];
  assert.ok(peer);
  assert.equal(connect.disabled, true);
  assert.equal(track.enabled, false, "Microphone must be muted before HOLD");

  peer.connectionState = "connected";
  peer.onconnectionstatechange();
  assert.equal(talk.disabled, false);
  let prevented = false;
  talk.listeners.pointerdown({
    pointerId: 7,
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, true);
  assert.equal(track.enabled, true, "HOLD must enable microphone");
  assert.equal(talk.attributes["aria-pressed"], "true");
  talk.listeners.pointerup();
  assert.equal(track.enabled, false, "Release must immediately mute");
  stop.listeners.click();
  assert.equal(track.stopped, true, "STOP must stop local microphone track");
  assert.equal(peer.closed, true, "STOP must close WebRTC peer");
  assert.equal(connect.disabled, false, "STOP must permit manual reconnect");
  assert.equal(talk.disabled, true);
  assert.equal(stop.hidden, true);
  assert.ok(
    requests.find((request) => request.url === "/ptt/live/signal" &&
      JSON.parse(request.opts.body).kind === "hangup"),
    "STOP must signal hangup",
  );
  console.log("PTT client control proof: CSRF, offer, mute, HOLD, release, STOP and reconnect PASS");
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
