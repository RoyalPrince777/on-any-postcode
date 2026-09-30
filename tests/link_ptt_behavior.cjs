"use strict";
// Behavioural controller test: no browser hardware, network or production mutations.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const source = fs.readFileSync(path.resolve(__dirname, "../static/linkup_voice.js"), "utf8");
const settle = async () => {
  for (let i = 0; i < 12; i += 1) await new Promise((resolve) => setImmediate(resolve));
};
const deferred = () => {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
};
const element = (dataset = {}) => {
  const events = new Map();
  return {
    dataset, disabled: true, hidden: false, textContent: "", attributes: {},
    addEventListener(name, callback) {
      const list = events.get(name) || [];
      list.push(callback);
      events.set(name, list);
    },
    emit(name, data = {}) {
      for (const callback of events.get(name) || []) callback({
        button: 0, preventDefault() {}, ...data,
      });
    },
    count(name) { return (events.get(name) || []).length; },
    setAttribute(name, value) { this.attributes[name] = value; },
    querySelector() { return null; },
  };
};
async function scenario({ permissionDelay = false, action = "release", compete = false }) {
  const control = element({ recipientId: "peer-1" });
  const voice = element({ recipientId: "peer-1" });
  const status = element();
  const win = element();
  const doc = element();
  const gate = deferred();
  const tracks = [];
  const recorderInstances = [];
  let permissionRequests = 0;
  let uploads = 0;
  class Recorder {
    static isTypeSupported() { return true; }
    constructor(stream, options) {
      this.stream = stream;
      this.mimeType = options.mimeType;
      this.state = "inactive";
      this.events = new Map();
      recorderInstances.push(this);
    }
    addEventListener(name, callback) { this.events.set(name, callback); }
    start() { this.state = "recording"; }
    stop() {
      if (this.state === "inactive") return;
      this.state = "inactive";
      this.events.get("dataavailable")({ data: new Blob(["voice"]) });
      this.events.get("stop")();
    }
  }
  const stream = () => {
    const track = { stopped: false, stop() { this.stopped = true; } };
    tracks.push(track);
    return { getTracks: () => [track] };
  };
  const fetchStub = async (url, options = {}) => {
    if (url === "/linkup/voice/status") return {
      ok: true, json: async () => ({
        ready: true, first_party: true, max_voice_bytes: 5242880,
        max_voice_duration_ms: 120000,
      }),
    };
    if (url === "/linkup/voice" && options.method === "POST") {
      uploads += 1;
      assert.equal(options.credentials, "same-origin");
      assert.equal(options.headers["X-OAP-CSRF"], "token");
      return { ok: true, json: async () => ({}) };
    }
    throw Error("Unexpected request: " + url);
  };
  const docQuery = {
    '[data-oap-voice-status]': status,
    'meta[name="oap-csrf-token"]': { content: "token" },
  };
  doc.querySelector = (selector) => docQuery[selector] || null;
  doc.querySelectorAll = (selector) => ({
    "[data-oap-voice-control]": [voice],
    "[data-oap-voice-stop]": [],
    "[data-oap-ptt-control]": [control],
    "[data-oap-voice-list]": [],
    select: [],
  })[selector] || [];
  doc.head = { appendChild() {} };
  doc.createElement = () => element();
  win.MediaRecorder = Recorder;
  win.setTimeout = () => 1;
  win.clearTimeout = () => {};
  const context = {
    document: doc, window: win, navigator: {
      mediaDevices: { getUserMedia: () => {
        permissionRequests += 1;
        return permissionDelay ? gate.promise : Promise.resolve(stream());
      } },
    },
    MediaRecorder: Recorder, Headers, FormData, Blob,
    fetch: fetchStub, Date, console,
  };
  vm.runInNewContext(source, context, { filename: "linkup_voice.js" });
  await settle();
  assert.equal(control.disabled, false);
  assert.equal(control.count("pointerdown"), 1);

  control.emit("pointerdown");
  if (compete) {
    assert.equal(voice.disabled, true);
    voice.emit("click"); // the Voice path must reject even when invoked programmatically
    control.emit("pointerdown");
    assert.equal(permissionRequests, 1);
  }
  if (!permissionDelay) await settle(); // Capture is genuinely active while held.
  if (action === "cancel") win.emit("pointercancel");
  else win.emit("pointerup");
  if (permissionDelay) gate.resolve(stream());
  await settle();

  if (action === "cancel" || permissionDelay) {
    assert.equal(uploads, 0, "cancelled or already-released PTT must never upload");
    assert.equal(recorderInstances.length, permissionDelay ? 0 : 1, "late permission must never start recording");
  } else {
    assert.equal(recorderInstances.length, 1, "release must create one recorder");
    assert.equal(uploads, 1, "release must upload exactly one private Voice");
  }
  assert.ok(tracks.every((track) => track.stopped), "all microphone tracks must stop");
  assert.equal(control.count("pointerdown"), 1, "refresh must not multiply event listeners");
  assert.equal(control.attributes["aria-pressed"], "false");
  assert.equal(control.disabled, false);
}
(async () => {
  await scenario({ action: "release", compete: true });
  await scenario({ action: "cancel", permissionDelay: true, compete: true });
  await scenario({ action: "release", permissionDelay: true, compete: true });
  await scenario({ action: "cancel", compete: true });
  process.stdout.write("PTT controller behaviour passed: active release, active cancel, late permission release/cancel, capture exclusivity.\\n");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
