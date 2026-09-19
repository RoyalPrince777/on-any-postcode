"use strict";

const assert = require("node:assert/strict");
const state = require("../mission_control/static/smi_live_character_state.js");

function apply(current, type) {
  return state.transition(current, {type});
}

let runtime = state.initialState();
assert.equal(runtime.state, "ready");
assert.equal(runtime.stopped, false);

// Live listening is allowed only from an idle state.
runtime = apply(runtime, "LIVE_ON");
assert.equal(runtime.live, true);
runtime = apply(runtime, "LISTEN_START");
assert.equal(runtime.state, "listening");
assert.equal(runtime.listening, true);

// Human STOP is sticky even if stale browser callbacks arrive afterward.
const listenToken = state.token(runtime);
runtime = apply(runtime, "STOP");
assert.equal(runtime.state, "stopped");
assert.equal(runtime.live, false);
assert.equal(runtime.stopped, true);
assert.equal(state.tokenIsCurrent(runtime, listenToken), false);
runtime = apply(runtime, "LISTEN_END");
assert.equal(runtime.state, "stopped");
runtime = apply(runtime, "SPEAK_END");
assert.equal(runtime.state, "stopped");
runtime = apply(runtime, "THINK_END");
assert.equal(runtime.state, "stopped");

// Only an explicit human restart leaves STOP.
runtime = apply(runtime, "RESUME_FROM_STOP");
assert.equal(runtime.state, "ready");
assert.equal(runtime.stopped, false);

// Half-duplex: listening cannot start while thinking or speaking.
runtime = apply(runtime, "THINK_START");
assert.equal(state.canListen(runtime), false);
const duringThinking = apply(runtime, "LISTEN_START");
assert.equal(duringThinking.state, "thinking");
runtime = apply(runtime, "THINK_END");
runtime = apply(runtime, "SPEAK_START");
assert.equal(runtime.state, "speaking");
assert.equal(state.canListen(runtime), false);
const duringSpeaking = apply(runtime, "LISTEN_START");
assert.equal(duringSpeaking.state, "speaking");

// Pause/resume preserves the active speaking phase.
runtime = apply(runtime, "PAUSE");
assert.equal(runtime.state, "paused");
assert.equal(runtime.paused, true);
assert.equal(runtime.speaking, true);
runtime = apply(runtime, "RESUME");
assert.equal(runtime.state, "speaking");
assert.equal(runtime.paused, false);
runtime = apply(runtime, "SPEAK_END");
assert.equal(runtime.state, "ready");

// Live Off invalidates pending callbacks and returns to a safe idle state.
runtime = apply(runtime, "LIVE_ON");
const liveToken = state.token(runtime);
runtime = apply(runtime, "LISTEN_START");
runtime = apply(runtime, "LIVE_OFF");
assert.equal(runtime.live, false);
assert.equal(runtime.state, "ready");
assert.equal(runtime.listening, false);
assert.equal(runtime.speaking, false);
assert.equal(state.tokenIsCurrent(runtime, liveToken), false);

// Unknown events are no-ops, not implicit authority.
const beforeUnknown = runtime;
runtime = apply(runtime, "NOT_A_REAL_EVENT");
assert.deepEqual(runtime, beforeUnknown);

console.log("SMI_LIVE_CHARACTER_STATE_V2_PASS");


// Auto-submit is allowed only for a current, idle, live, unpaused final transcript.
runtime = state.initialState();
runtime = apply(runtime, "LIVE_ON");
assert.equal(state.canAutoSubmitFinal(runtime, "hello", true), true);
runtime = apply(runtime, "PAUSE");
assert.equal(state.canAutoSubmitFinal(runtime, "hello", true), false);
runtime = apply(runtime, "RESUME");
assert.equal(state.canAutoSubmitFinal(runtime, "hello", true), true);
runtime = apply(runtime, "STOP");
assert.equal(state.canAutoSubmitFinal(runtime, "hello", true), false);
runtime = apply(runtime, "RESUME_FROM_STOP");
runtime = apply(runtime, "LIVE_ON");
assert.equal(state.canAutoSubmitFinal(runtime, "hello", false), false);
runtime = apply(runtime, "LIVE_OFF");
assert.equal(state.canAutoSubmitFinal(runtime, "hello", true), false);
assert.equal(state.canAutoSubmitFinal(state.initialState(), "", true), false);
