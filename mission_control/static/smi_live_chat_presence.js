/* One governed visual state, shared with the existing Founder Command Centre.
   No transcript, recording, tokens, permissions or operational verdicts cross
   the iframe boundary. The parent verifies same-origin + exact frame source. */
(() => {
  "use strict";
  const allowed = new Set(["ready", "listening", "thinking", "speaking", "paused", "stopped"]);
  const apply = state => {
    const phase = allowed.has(state) ? state : "ready";
    document.body.dataset.smiPresence = phase;
    // The chat remains authoritative for state. This sends display state only.
    if (window.parent !== window) {
      window.parent.postMessage({type: "oap-smi-visual-state-v1", state: phase}, window.location.origin);
    }
  };
  apply(document.getElementById("smi-character")?.dataset.state || "ready");
  window.addEventListener("oap-smi-character-state", event => apply(event.detail?.state));
})();
