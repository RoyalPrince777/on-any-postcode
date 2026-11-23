"use strict";
/* Exercise the actual inline SMI chat stage helpers without browser/network. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const base = fs.readFileSync("mission_control/templates/ollama_chat_base.html", "utf8");
const controller = fs.readFileSync("mission_control/static/smi_canonical_controller.js", "utf8");
const css = fs.readFileSync("mission_control/static/smi_noise_strip.css", "utf8");

const begin = base.indexOf("function wantsWorkDetails(text){");
const end = base.indexOf("function setRunning(running){", begin);
assert.ok(begin > 0 && end > begin, "live chat details helpers must exist");

const classes = new Set();
const thinkingLog = {
  children: [],
  _text: "",
  append(node) { this.children.push(node); },
  get firstChild() {
    if (!this.children.length) return null;
    return { remove: () => this.children.shift() };
  },
  set textContent(value) {
    this._text = value;
    if (value === "") this.children = [];
  },
  get textContent() { return this._text; },
};
const thinking = {
  dataset: {},
  classList: {
    add(name) { classes.add(name); },
    remove(name) { classes.delete(name); },
    toggle(name, enabled) {
      if (enabled) classes.add(name);
      else classes.delete(name);
    },
    contains(name) { return classes.has(name); },
  },
};
const statusEl = { textContent: "Ready" };
const providerState = { textContent: "Ready" };
const thinkingTitle = { textContent: "Thinking Process" };
const ctx = {
  thinking, thinkingLog, thinkingTitle, providerState, statusEl,
  workStartedAt: 10,
  updateWorkedFor() {},
  document: { createElement: () => ({ textContent: "" }) },
};
vm.createContext(ctx);
vm.runInContext(
  base.slice(begin, end) +
  "\nthis.quietReview = { wantsWorkDetails, setWorkDetails, showStage, hideThinking };",
  ctx
);
const { wantsWorkDetails, setWorkDetails, showStage, hideThinking } = ctx.quietReview;

for (const prompt of [
  "Fix my port 5000 sign-in",
  "Check release risks silently",
  "Truth Mode and red team should be internal",
  "Does this have evidence?",
  "Don't show thinking process",
  "Please don't show work stages",
  "Do not expose evidence",
]) assert.equal(wantsWorkDetails(prompt), false, prompt);

for (const prompt of [
  "show work stages",
  "Show me the evidence",
  "Expose",
  "display review steps",
]) assert.equal(wantsWorkDetails(prompt), true, prompt);

setWorkDetails("Fix my port 5000 sign-in");
showStage("Challenge assumptions");
assert.equal(thinking.classList.contains("show"), false);
assert.equal(thinkingLog.children.length, 0, "normal chat must not log review stages");
assert.notEqual(statusEl.textContent, "Challenge assumptions");
hideThinking();
assert.equal(thinking.classList.contains("show"), false);

setWorkDetails("Show work stages");
showStage("Checking evidence");
assert.equal(thinking.classList.contains("show"), true);
assert.equal(thinkingLog.children.length, 1);
assert.equal(thinkingLog.children[0].textContent, "Checking evidence");
hideThinking();
assert.equal(thinking.classList.contains("show"), true);

setWorkDetails("Repair login");
showStage("Internal risk check");
assert.equal(thinking.classList.contains("show"), false, "one-shot request cannot leak into next");
assert.equal(thinkingLog.children.length, 0);

assert.ok(
  controller.includes("setWorkDetails(text);oapInput.value=''"),
  "canonical Android/WebView submit must set per-message review visibility before clearing input"
);
assert.ok(
  controller.includes("if(thinking.dataset.detailsRequested==='true')add("),
  "per-turn mode/time system message must be opt-in"
);
assert.ok(
  css.includes('#thinking:not([data-details-requested="true"])'),
  "default view must hide internal work panel"
);
assert.ok(
  css.includes('#thinking.show[data-details-requested="true"]'),
  "explicit safe stage detail must remain available"
);
console.log("SMI quiet internal reviews: passed (default hidden, opt-in safe details, no stale state)");
