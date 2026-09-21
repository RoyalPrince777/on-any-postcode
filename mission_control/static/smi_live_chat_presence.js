/* Reflect the governed SMI state into the full-screen artwork without claiming a rig. */
(() => {
  "use strict";
  const allowed=new Set(["ready","listening","thinking","speaking","paused","stopped"]);
  const apply=state=>{
    document.body.dataset.smiPresence=allowed.has(state)?state:"ready";
  };
  apply(document.getElementById("smi-character")?.dataset.state||"ready");
  window.addEventListener("oap-smi-character-state",event=>apply(event.detail?.state));
})();
