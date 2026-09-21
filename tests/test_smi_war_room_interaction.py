"""Headless interactive War Room smoke: real DOM-event path without deployment."""
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "mission_control/static/smi_war_room_missions.js"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js required")
def test_war_room_preserves_draft_and_requires_approval_before_preparing():
    program = r"""
const fs = require("fs");
class Node {
  constructor() {
    this.handlers = {}; this.children = []; this.dataset = {};
    this.value = ""; this.checked = false; this.textContent = "";
    this.classes = new Set();
    this.classList = {
      add: value => this.classes.add(value),
      remove: value => this.classes.delete(value),
      contains: value => this.classes.has(value)
    };
  }
  setAttribute(k, v) { this[k] = v; }
  addEventListener(k, f) { (this.handlers[k] ||= []).push(f); }
  click() { (this.handlers.click || []).forEach(f => f()); }
  change() { (this.handlers.change || []).forEach(f => f()); }
  append(...nodes) { this.children.push(...nodes); }
  after(node) { this.afterNode = node; }
  before(node) { this.beforeNode = node; }
  focus() { this.focused = true; }
  dispatchEvent(event) { this.lastEvent = event.type; }
  querySelector(q) { return this.nodes?.[q] || null; }
  querySelectorAll(q) {
    return q === 'input[type="checkbox"]'
      ? this.children.flatMap(label => label.children.filter(c => c.type === "checkbox"))
      : [];
  }
}
const centre = new Node();
const composer = new Node();
composer.maxLength = 4000;
const toggle = new Node();
const options = new Node();
const universe = new Node();
const close = new Node();
const imagePreview = new Node();
const mediaPreview = new Node();
const imageInput = new Node();
const cameraInput = new Node();
const mediaInput = new Node();
const attachments = {
  "image-preview": imagePreview, "media-preview": mediaPreview,
  "image-input": imageInput, "camera-input": cameraInput, "media-input": mediaInput
};
const map = {};
for (const key of ["feedback","depth","mode","instruction","approval","all","p0","clear","prepare","close"]) {
  map[key] = new Node();
}
map.depth.value = "21"; map.mode.value = "review";
centre.nodes = {".smi-command-universe":universe,".smi-command-close":close};
centre.querySelector = q => centre.nodes[q];
const originalCreate = global.document;
global.document = {
  body:{classList:new Node().classList},
  getElementById:id => id === "smi-command-centre" ? centre : id === "message" ? composer : (attachments[id] || null),
  querySelector:q => q === ".smi-command-toggle" ? toggle : null,
  createElement:tag => {
    const node = new Node();
    if (tag === "section") {
      node.nodes = {
        ".smi-war-options":options,
        "[data-war-feedback]":map.feedback,
        "[data-war-depth]":map.depth,
        "[data-war-mode]":map.mode,
        "[data-war-instruction]":map.instruction,
        "[data-war-approval]":map.approval,
        "[data-war-all]":map.all,
        "[data-war-p0]":map.p0,
        "[data-war-clear]":map.clear,
        "[data-war-prepare]":map.prepare,
        "[data-war-close]":map.close
      };
    }
    return node;
  },
  createTextNode:t => ({text:t})
};
global.window = {};
global.Event = class { constructor(type) { this.type = type; } };
toggle.addEventListener("click",()=>{
  const classes=document.body.classList;
  if (classes.contains("smi-command-open")) classes.remove("smi-command-open");
  else classes.add("smi-command-open");
});
eval(fs.readFileSync(process.argv[1], "utf8"));
const open = toggle.afterNode;
if (!open) throw Error("missing shared War Room opener");
open.click();
if (!centre.classList.contains("smi-war-missions-open")) throw Error("selector did not open");
if (!map.instruction.focused) throw Error("instruction not focused");
composer.value = "Unsent private draft";
map.prepare.click();
if (composer.value !== "Unsent private draft") throw Error("overwrote chat draft");
if (!map.feedback.textContent.includes("preserved")) throw Error("no preservation receipt");
composer.value = "   ";
map.prepare.click();
if (composer.value !== "   ") throw Error("whitespace draft overwritten");
composer.value = "";
imagePreview.classList.add("show");
map.prepare.click();
if (composer.value) throw Error("private image preview attached to War Room");
if (!map.feedback.textContent.includes("attachment preserved")) throw Error("no attachment preservation receipt");
imagePreview.classList.remove("show");
mediaInput.files = [{name:"private.pdf"}];
map.prepare.click();
if (composer.value) throw Error("pending document attached to War Room");
mediaInput.files = [];
map.mode.value = "build"; map.mode.change();
map.prepare.click();
if (composer.value) throw Error("unauthorised build prepared");
if (!map.feedback.textContent.includes("approval")) throw Error("approval failure hidden");
map.approval.checked = true;
map.instruction.value = "Keep canonical STOP and uploads";
map.prepare.click();
if (!composer.value.includes("Keep canonical STOP and uploads")) throw Error("Founder instruction missing");
if (!composer.value.includes("no merge or deployment")) throw Error("release guard lost");
if (composer.lastEvent !== "input") throw Error("canonical input event not fired");
if (!composer.focused) throw Error("existing composer not focused");
if (centre.classList.contains("smi-war-missions-open")) throw Error("selector not closed");
if (document.body.classList.contains("smi-command-open")) throw Error("chat not restored");
if (composer.value.length > composer.maxLength) throw Error("composer overflow");
if (originalCreate) throw Error("unexpected DOM");
console.log("war_room_interaction_passed");
"""
    run = subprocess.run(
        ["node", "-e", program, str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=12,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert "war_room_interaction_passed" in run.stdout
