"use strict";

const assert = require("node:assert/strict");
const state = require("../mission_control/static/smi_live_character_state.js");

const EVENTS = [
  "LIVE_ON",
  "LIVE_OFF",
  "LISTEN_START",
  "LISTEN_END",
  "THINK_START",
  "THINK_END",
  "SPEAK_START",
  "SPEAK_END",
  "PAUSE",
  "RESUME",
  "STOP",
  "RESUME_FROM_STOP",
];

function step(runtime, event) {
  return state.transition(runtime, {type: event});
}

function assertInvariants(runtime) {
  assert.equal(Boolean(runtime.listening && runtime.speaking), false, "cannot listen and speak together");
  assert.equal(Boolean(runtime.listening && runtime.thinking), false, "cannot listen and think together");
  assert.equal(Boolean(runtime.stopped && runtime.live), false, "STOP must disable Live");
  if (runtime.stopped) {
    assert.equal(runtime.state, "stopped");
    assert.equal(runtime.listening, false);
    assert.equal(runtime.thinking, false);
    assert.equal(runtime.speaking, false);
  }
  if (runtime.paused) assert.equal(runtime.state, "paused");
  if (state.canAutoSubmitFinal(runtime, "final words", true)) {
    assert.equal(runtime.live, true);
    assert.equal(runtime.stopped, false);
    assert.equal(runtime.paused, false);
    assert.equal(runtime.listening, false);
    assert.equal(runtime.thinking, false);
    assert.equal(runtime.speaking, false);
  }
}

let exploredTransitions = 0;

function walk(runtime, depth, maxDepth, seen) {
  assertInvariants(runtime);
  if (depth >= maxDepth) return;
  for (const event of EVENTS) {
    exploredTransitions += 1;
    const next = step(runtime, event);
    const key = JSON.stringify([depth, event, next]);
    seen.add(key);
    walk(next, depth + 1, maxDepth, seen);
  }
}

const seen = new Set();
walk(state.initialState(), 0, 5, seen);
assert.ok(exploredTransitions > 1000, "expected broad transition exploration");
assert.ok(seen.size > 100, "expected broad unique-state/event coverage");

// Explicit sticky-STOP adversarial sequence.
let runtime = state.initialState();
runtime = step(runtime, "LIVE_ON");
runtime = step(runtime, "LISTEN_START");
const beforeStop = state.token(runtime);
runtime = step(runtime, "STOP");
for (const late of ["LISTEN_END", "SPEAK_END", "THINK_END", "LIVE_ON", "PAUSE", "RESUME"]) {
  const after = step(runtime, late);
  assert.equal(after.stopped, true, `late ${late} must not escape STOP`);
  assert.equal(after.state, "stopped");
  runtime = after;
}
assert.equal(state.tokenIsCurrent(runtime, beforeStop), false);
assert.equal(state.canAutoSubmitFinal(runtime, "final words", true), false);

// Pause safety: final speech cannot auto-submit while paused.
runtime = state.initialState();
runtime = step(runtime, "LIVE_ON");
runtime = step(runtime, "PAUSE");
assert.equal(state.canAutoSubmitFinal(runtime, "final words", true), false);

// Live Off safety: final speech cannot auto-submit once Live is disabled.
runtime = step(runtime, "RESUME");
runtime = step(runtime, "LIVE_OFF");
assert.equal(state.canAutoSubmitFinal(runtime, "final words", true), false);

// Thinking/speaking deny mic entry.
runtime = state.initialState();
runtime = step(runtime, "THINK_START");
assert.equal(state.canListen(runtime), false);
runtime = step(runtime, "THINK_END");
runtime = step(runtime, "SPEAK_START");
assert.equal(state.canListen(runtime), false);

console.log(`SMI_LIVE_EXHAUSTIVE_V1_PASS explored=${exploredTransitions} unique=${seen.size}`);
