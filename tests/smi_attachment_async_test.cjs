"use strict";
// Dependency-free execution test of the actual inline SMI picker handlers.
// This is a simulated browser-event harness, NOT a live/device upload proof.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const base = fs.readFileSync("mission_control/templates/ollama_chat_base.html", "utf8");
function segment(first, after) {
  const start = base.indexOf(first);
  const end = base.indexOf(after, start);
  assert.ok(start >= 0 && end > start, first + " was not found");
  return base.slice(start, end);
}
const pending = [];
class MockFileReader {
  readAsDataURL(file) { this.file = file; pending.push(this); }
}
const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    const flags = new Set();
    elements.set(id, {
      value: "", textContent: "", src: "", disabled: false,
      classList: { add: name => flags.add(name), remove: name => flags.delete(name),
        contains: name => flags.has(name) },
    });
  }
  return elements.get(id);
}
const ctx = {
  FileReader: MockFileReader, document: { getElementById: element },
  imageInput: { files: [], value: "" }, cameraInput: { files: [], value: "" },
  mediaInput: { files: [], value: "" }, fileButton: { disabled: false },
  statusEl: { textContent: "" },
};
vm.createContext(ctx);
vm.runInContext(
  "let selectedImage='',selectedAttachment=null," +
  "imagePreparing=false,attachmentPreparing=false,imagePrepareToken=0,mediaPrepareToken=0;\n" +
  segment("function prepareImage(source)", "function readDataURL(file)") +
  "\nfunction readDataURL(file){return new Promise((resolve,reject)=>{" +
  "const reader=new FileReader();reader.onload=()=>resolve(reader.result);" +
  "reader.onerror=reject;reader.readAsDataURL(file)})}\n" +
  "async function videoFrames(){return []}\n" +
  segment("mediaInput.onchange=async", "codeButton.onclick="),
  ctx,
);
const state = () => vm.runInContext(
  "({selectedImage,selectedAttachment,imagePreparing,attachmentPreparing})", ctx,
);
const image = name => ({ name, type: "image/png", size: 25 });
const documentFile = name => ({ name, type: "text/plain", size: 25 });
(async () => {
  ctx.imageInput.files = [image("old.png")];
  ctx.imageInput.onchange();
  assert.equal(state().imagePreparing, true);
  const old = pending.shift();
  ctx.imageInput.files = [image("new.png")];
  ctx.imageInput.onchange();
  const current = pending.shift();
  old.result = "data:image/png;base64,OLD"; old.onload();
  assert.equal(state().selectedImage, "", "stale image must not restore");
  current.result = "data:image/png;base64,NEW"; current.onload();
  assert.equal(state().selectedImage, "data:image/png;base64,NEW");
  assert.equal(state().imagePreparing, false);

  ctx.cameraInput.files = [image("removed.png")];
  ctx.cameraInput.onchange();
  const removed = pending.shift();
  element("remove-image").onclick();
  removed.result = "data:image/png;base64,STALE"; removed.onload();
  assert.equal(state().selectedImage, "", "removed image must stay removed");

  ctx.mediaInput.files = [documentFile("removed.txt")];
  const removedPromise = ctx.mediaInput.onchange();
  assert.equal(state().attachmentPreparing, true);
  const oldDoc = pending.shift();
  element("remove-media").onclick();
  oldDoc.result = "data:text/plain;base64,T0xE"; oldDoc.onload();
  await removedPromise;
  assert.equal(state().selectedAttachment, null, "removed doc must stay removed");

  ctx.mediaInput.files = [documentFile("current.txt")];
  const currentPromise = ctx.mediaInput.onchange();
  assert.equal(state().attachmentPreparing, true);
  const currentDoc = pending.shift();
  currentDoc.result = "data:text/plain;base64,TkVX"; currentDoc.onload();
  await currentPromise;
  assert.equal(state().attachmentPreparing, false);
  assert.equal(state().selectedAttachment.name, "current.txt");
  assert.equal(state().selectedAttachment.data, "data:text/plain;base64,TkVX");
  assert.equal(element("media-preview").classList.contains("show"), true);
  console.log("SMI_ATTACHMENT_ASYNC_GUARD_PASS");
})().catch(error => { console.error(error); process.exitCode = 1; });
