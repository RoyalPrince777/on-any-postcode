(() => {
  "use strict";

  const codeNode = document.querySelector("[data-oap-ptt-code]");
  const copyButton = document.querySelector("[data-oap-ptt-copy-code]");
  const pairStatus = document.querySelector("[data-oap-ptt-pair-status]");

  if (copyButton && codeNode) {
    copyButton.addEventListener("click", async () => {
      const code = (codeNode.textContent || "").trim();
      if (!code) return;
      try {
        await navigator.clipboard.writeText(code);
        copyButton.textContent = "Copied";
      } catch (_error) {
        copyButton.textContent = code;
      }
    });
  }

  if (!codeNode || !pairStatus) return;

  let stopped = false;
  const poll = async () => {
    if (stopped) return;
    try {
      const response = await fetch("/ptt/pair/status", {
        credentials: "same-origin",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      const payload = await response.json().catch(() => ({}));
      if (response.ok && payload.active === true && payload.peer_id) {
        stopped = true;
        pairStatus.textContent = "Connected. Opening PTT…";
        window.location.reload();
        return;
      }
      pairStatus.textContent = "Waiting for the other phone to join…";
    } catch (_error) {
      pairStatus.textContent = "Connection check unavailable. Pairing code remains active for a short time.";
    }
    window.setTimeout(poll, 2000);
  };

  poll();
})();
