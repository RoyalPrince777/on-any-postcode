(() => {
  "use strict";

  const installButton = document.querySelector("[data-oap-install]");
  const status = document.querySelector("[data-oap-install-status]");
  let deferredInstall = null;

  const setStatus = (message) => {
    if (status) status.textContent = message;
  };

  const installed = window.matchMedia("(display-mode: standalone)").matches;
  if (installed) {
    setStatus("OAP OS is installed on this device.");
  } else if (!("serviceWorker" in navigator)) {
    setStatus("This browser does not support secure OAP OS installation.");
  } else {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/service-worker.js", {scope: "/"})
        .then(() => setStatus("OAP OS is ready. Use Install when your browser offers it."))
        .catch(() => setStatus("OAP OS installation is temporarily unavailable."));
    });
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstall = event;
    if (installButton) installButton.hidden = false;
    setStatus("OAP OS is ready to install on this device.");
  });

  if (installButton) {
    installButton.addEventListener("click", async () => {
      if (!deferredInstall) {
        setStatus("Use your browser menu and choose Install app or Add to Home screen.");
        return;
      }
      installButton.disabled = true;
      await deferredInstall.prompt();
      const choice = await deferredInstall.userChoice;
      setStatus(
        choice.outcome === "accepted"
          ? "OAP OS installation accepted."
          : "OAP OS was not installed; no device setting was changed."
      );
      deferredInstall = null;
      installButton.hidden = true;
      installButton.disabled = false;
    });
  }

  window.addEventListener("appinstalled", () => {
    deferredInstall = null;
    if (installButton) installButton.hidden = true;
    setStatus("OAP OS is installed on this device.");
  });
})();
