(() => {
  "use strict";

  const installButton = document.querySelector("[data-oap-install]");
  const status = document.querySelector("[data-oap-install-status]");
  const platformLabel = document.querySelector("[data-oap-install-platform]");
  let deferredInstall = null;

  const ua = navigator.userAgent || "";
  const platform = navigator.userAgentData?.platform || navigator.platform || "";
  const isIOS = /iPad|iPhone|iPod/i.test(ua) || (platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const isAndroid = /Android/i.test(ua);
  const isWindows = /Win/i.test(platform) || /Windows/i.test(ua);
  const isMac = !isIOS && (/Mac/i.test(platform) || /Macintosh/i.test(ua));
  const isChromeOS = /CrOS/i.test(ua);
  const isLinux = !isAndroid && /Linux/i.test(platform + " " + ua);
  const isSafari = /Safari/i.test(ua) && !/Chrome|Chromium|CriOS|Edg|OPR|Firefox|FxiOS/i.test(ua);

  const platformName = isIOS
    ? "iPhone / iPad"
    : isAndroid
      ? "Android"
      : isWindows
        ? "Windows"
        : isMac
          ? "macOS"
          : isChromeOS
            ? "ChromeOS"
            : isLinux
              ? "Linux"
              : "this platform";

  const setStatus = (message) => {
    if (status) status.textContent = message;
  };

  if (platformLabel) platformLabel.textContent = platformName;

  const installed = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;

  const fallbackInstruction = () => {
    if (isIOS) return "In Safari, tap Share, then Add to Home Screen.";
    if (isMac && isSafari) return "In Safari, use File → Add to Dock. In a Chromium browser, use Install app.";
    if (isAndroid) return "Open the browser menu and choose Install app or Add to Home screen.";
    if (isWindows || isChromeOS || isLinux || isMac) return "Open the browser menu or address-bar install icon and choose Install app.";
    return "Use your browser menu and choose Install app or Add to Home screen when supported.";
  };

  if (installed) {
    if (installButton) installButton.hidden = true;
    setStatus(`OAP OS is installed on ${platformName}.`);
  } else if (!("serviceWorker" in navigator)) {
    if (installButton) installButton.hidden = false;
    setStatus(`Secure app installation is not available in this browser. ${fallbackInstruction()}`);
  } else {
    if (installButton) installButton.hidden = false;
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/service-worker.js", {scope: "/"})
        .then(() => setStatus(`OAP OS is ready on ${platformName}. ${fallbackInstruction()}`))
        .catch(() => setStatus("OAP OS installation is temporarily unavailable."));
    });
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstall = event;
    if (installButton) installButton.hidden = false;
    setStatus(`OAP OS is ready to install on ${platformName}.`);
  });

  if (installButton) {
    installButton.addEventListener("click", async () => {
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
            ? `OAP OS installation accepted on ${platformName}.`
            : "OAP OS was not installed; no device setting was changed."
        );
      } finally {
        deferredInstall = null;
        installButton.disabled = false;
      }
    });
  }

  window.addEventListener("appinstalled", () => {
    deferredInstall = null;
    if (installButton) installButton.hidden = true;
    setStatus(`OAP OS is installed on ${platformName}.`);
  });
})();
