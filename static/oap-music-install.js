(() => {
  "use strict";

  const installButton = document.querySelector("[data-oap-music-install]");
  const status = document.querySelector("[data-oap-music-install-status]");
  let deferredInstall = null;

  const setStatus = (message) => {
    if (status) status.textContent = message;
  };

  const installed =
    window.matchMedia("(display-mode: standalone)").matches ||
    navigator.standalone === true;

  const fallbackInstruction = () => {
    const ua = navigator.userAgent || "";
    const platform = navigator.userAgentData?.platform || navigator.platform || "";
    const isIOS = /iPad|iPhone|iPod/i.test(ua) ||
      (platform === "MacIntel" && navigator.maxTouchPoints > 1);
    const isAndroid = /Android/i.test(ua);
    const isSafari = /Safari/i.test(ua) &&
      !/Chrome|Chromium|CriOS|Edg|OPR|Firefox|FxiOS/i.test(ua);

    if (isIOS) return "In Safari, tap Share, then Add to Home Screen.";
    if (isSafari) return "Use Safari’s Add to Dock or Add to Home Screen action.";
    if (isAndroid) return "Open the browser menu and choose Install app or Add to Home screen.";
    return "Use the browser install icon or menu and choose Install app.";
  };

  if (installed) {
    if (installButton) installButton.hidden = true;
    setStatus("OAP Music is installed on this device.");
  } else if (!("serviceWorker" in navigator)) {
    if (installButton) installButton.hidden = false;
    setStatus(`Install support is unavailable in this browser. ${fallbackInstruction()}`);
  } else {
    if (installButton) installButton.hidden = false;
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/service-worker.js", { scope: "/" })
        .then(() => setStatus(`OAP Music is install-ready. ${fallbackInstruction()}`))
        .catch(() => setStatus("OAP Music installation is temporarily unavailable."));
    });
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstall = event;
    if (installButton) installButton.hidden = false;
    setStatus("OAP Music is ready to install.");
  });

  installButton?.addEventListener("click", async () => {
    if (!deferredInstall) {
      setStatus(fallbackInstruction());
      return;
    }
    installButton.disabled = true;
    try {
      await deferredInstall.prompt();
      const choice = await deferredInstall.userChoice;
      setStatus(
        choice.outcome === "accepted"
          ? "OAP Music installation accepted."
          : "OAP Music was not installed; no device setting was changed."
      );
    } finally {
      deferredInstall = null;
      installButton.disabled = false;
    }
  });

  window.addEventListener("appinstalled", () => {
    deferredInstall = null;
    if (installButton) installButton.hidden = true;
    setStatus("OAP Music is installed.");
  });
})();
