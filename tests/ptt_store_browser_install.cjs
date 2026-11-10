"use strict";
/* Run the actual PWA controller under browser-like DOM settings.
   PWA browser capabilities are mocked; this is not device installation proof. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const script = fs.readFileSync(
  path.join(__dirname, "..", "static", "oap-os.js"), "utf8"
);

function browser({ userAgent, pathname = "/ptt", standalone = false, serviceWorker = true }) {
  const listeners = {};
  const status = { textContent: "" };
  const button = {
    hidden: true,
    disabled: false,
    callbacks: {},
    addEventListener(name, callback) { this.callbacks[name] = callback; },
  };
  let registrations = 0;
  const navigator = {
    userAgent,
    platform: "Linux armv8l",
    standalone: false,
  };
  if (serviceWorker) navigator.serviceWorker = {
    register: async (_url, options) => {
      registrations += 1;
      assert.equal(options.scope, "/");
    },
  };
  const window = {
    matchMedia: () => ({ matches: standalone }),
    addEventListener(name, callback) { listeners[name] = callback; },
  };
  const document = {
    querySelector(selector) {
      if (selector === "[data-oap-install]") return button;
      if (selector === "[data-oap-install-status]") return status;
      return null;
    },
  };
  vm.runInNewContext(script, { document, navigator, window, location: { pathname } }, {
    filename: "oap-os.js",
  });
  return { listeners, status, button, registrations: () => registrations };
}

async function main() {
  const chromeUA = "Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36";
  const embeddedUA = "Mozilla/5.0 (Linux; Android 15; Pixel 8 Build/ABCD; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.0.0 Mobile Safari/537.36";

  // Android WebView must not misrepresent install capability.
  const embedded = browser({ userAgent: embeddedUA });
  assert.equal(embedded.button.hidden, true);
  assert.match(embedded.status.textContent, /embedded OAP Home V2 view/);
  assert.match(embedded.status.textContent, /Open this OAP PTT page in your Android browser/);
  assert.equal(embedded.registrations(), 0);
  let prevented = false;
  embedded.listeners.beforeinstallprompt({
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, false);
  assert.equal(embedded.button.hidden, true);
  await embedded.button.callbacks.click();
  assert.match(embedded.status.textContent, /browser/);

  // Normal Chrome gets user-initiated installation flow (no auto-install).
  const chrome = browser({ userAgent: chromeUA });
  assert.equal(chrome.button.hidden, false);
  await chrome.listeners.load();
  await Promise.resolve();
  assert.equal(chrome.registrations(), 1);
  assert.match(chrome.status.textContent, /Open the browser menu/);
  let prompted = 0;
  chrome.listeners.beforeinstallprompt({
    preventDefault() {},
    async prompt() { prompted += 1; },
    userChoice: Promise.resolve({ outcome: "accepted" }),
  });
  assert.match(chrome.status.textContent, /ready to install/);
  assert.equal(prompted, 0, "The app must not install without a user click");
  await chrome.button.callbacks.click();
  assert.equal(prompted, 1);
  assert.match(chrome.status.textContent, /installation accepted/);

  // A standalone window may belong to the broader OAP PWA, not dedicated PTT.
  const standaloneView = browser({ userAgent: chromeUA, standalone: true });
  assert.equal(standaloneView.button.hidden, true);
  assert.match(standaloneView.status.textContent, /standalone window/);
  assert.doesNotMatch(standaloneView.status.textContent, /is installed on/);

  console.log("PTT Store browser-install proof: embedded V2 fallback, Chrome manual install, standalone truth PASS");
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
