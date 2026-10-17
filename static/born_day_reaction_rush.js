"use strict";
(() => {
  const pad = document.getElementById("pad");
  const result = document.getElementById("result");
  let state = "idle", timer = null, start = 0;
  function clear() { if (timer !== null) window.clearTimeout(timer); timer = null; }
  function idle(message) {
    clear(); state = "idle"; pad.className = ""; pad.textContent = "Play again";
    result.textContent = message;
  }
  function begin() {
    clear(); state = "waiting"; pad.className = "wait"; pad.textContent = "WAIT…";
    result.textContent = "Wait for the GO signal.";
    const delay = 1600 + Math.floor(Math.random() * 2400);
    timer = window.setTimeout(() => {
      timer = null;
      if (state !== "waiting" || document.hidden) return;
      start = performance.now(); state = "ready"; pad.className = "ready";
      pad.textContent = "GO! TAP NOW"; result.textContent = "GO! Tap now!";
    }, delay);
  }
  pad.addEventListener("click", () => {
    if (state === "idle") { begin(); return; }
    if (state === "waiting") { idle("False start! You tapped before GO."); return; }
    if (state === "ready") {
      const elapsed = Math.max(0, Math.round(performance.now() - start));
      idle("Your reaction: " + elapsed + " ms. Device-measured, not competition-verified.");
    }
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && state !== "idle") idle("Round cancelled because the page was interrupted.");
  });
  window.addEventListener("pagehide", clear);
})();
