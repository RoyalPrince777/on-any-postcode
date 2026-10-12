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
