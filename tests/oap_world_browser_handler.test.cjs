"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const html = fs.readFileSync(path.join(__dirname, "../templates/world.html"), "utf8");
const match = html.match(/<script>\s*([\s\S]*?)\s*<\/script>/);
assert.ok(match, "OAP World inline browser handler must exist");

function runAddress(value, approve = true) {
  let submit;
  const input = {value};
  const note = {textContent: ""};
  const destinations = [];
  const confirmations = [];
  const form = {addEventListener(name, callback) {
    assert.equal(name, "submit");
    submit = callback;
  }};
  const elements = {"world-search": form, "world-query": input, "world-search-note": note};
  const context = {
    document: {getElementById(id) {return elements[id];}},
    window: {
      confirm(message) {confirmations.push(message); return approve;},
      location: {assign(url) {destinations.push(url);}}
    },
    URL
  };
  vm.runInNewContext(match[1], context, {timeout: 1000});
  let prevented = false;
  submit({preventDefault() {prevented = true;}});
  return {prevented, note: note.textContent, destinations, confirmations};
}

test("opens HTTPS host after explicit OPEN WEB confirmation", () => {
  const result = runAddress("example.org/path");
  assert.equal(result.prevented, true);
  assert.deepEqual(result.destinations, ["https://example.org/path"]);
  assert.match(result.confirmations[0], /OPEN WEB.*example\.org/);
});

test("does not leave OAP World if user cancels", () => {
  const result = runAddress("https://example.org", false);
  assert.deepEqual(result.destinations, []);
  assert.match(result.note, /Stayed in OAP World/);
});

test("rejects embedded credentials and non-web schemes", () => {
  for (const value of ["https://user:secret@example.org", "javascript:alert(1)", "file:///etc/passwd", "http://localhost"]) {
    const result = runAddress(value);
    assert.deepEqual(result.destinations, [], value);
    assert.deepEqual(result.confirmations, [], value);
  }
});

test("rejects whitespace and empty input without leaving", () => {
  for (const value of ["", "hello world"]) {
    const result = runAddress(value);
    assert.deepEqual(result.destinations, []);
    assert.deepEqual(result.confirmations, []);
    assert.ok(result.note);
  }
});

test("Agent Smith: malformed and hostile addresses never bypass consent", () => {
  const rejected = [
    "data:text/html,<script>alert(1)</script>",
    "vbscript:msgbox(1)",
    "https://user@example.org",
    "https://user:pass@example.org",
    "https://example.org\nattacker.org",
    "https://example.org/path with spaces",
    "https://127.0.0.1",
    "https://[::1]",
    "http://intranet",
    "https://example.org:invalid"
  ];
  for (const value of rejected) {
    const result = runAddress(value);
    assert.deepEqual(result.destinations, [], value);
    assert.deepEqual(result.confirmations, [], value);
  }
});

test("Shere Khan: confirmation must precede navigation on every valid attempt", () => {
  for (const value of ["https://example.org", "http://example.org/path?q=1", "example.org"]) {
    const rejected = runAddress(value, false);
    assert.equal(rejected.confirmations.length, 1, value);
    assert.deepEqual(rejected.destinations, [], value);
    const approved = runAddress(value, true);
    assert.equal(approved.confirmations.length, 1, value);
    assert.equal(approved.destinations.length, 1, value);
  }
});

test("The Twins: cancellation and retry preserve a safe navigation outcome", () => {
  const cancelled = runAddress("example.org/recovery", false);
  assert.deepEqual(cancelled.destinations, []);
  assert.match(cancelled.note, /Stayed in OAP World/);
  const retry = runAddress("example.org/recovery", true);
  assert.deepEqual(retry.destinations, ["https://example.org/recovery"]);
});
