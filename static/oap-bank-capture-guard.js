(() => {
  "use strict";

  const root = document.documentElement;
  const sensitive = document.querySelector("[data-oap-bank-sensitive]");
  if (!sensitive) return;

  const shield = document.createElement("div");
  shield.id = "oap-bank-privacy-shield";
  shield.setAttribute("aria-hidden", "true");
  shield.innerHTML = "<div><strong>OAP BANK</strong><span>Private banking screen protected</span></div>";
  document.body.appendChild(shield);

  const watermark = document.createElement("div");
  watermark.id = "oap-bank-capture-watermark";
  watermark.setAttribute("aria-hidden", "true");
  watermark.textContent = "OAP BANK • PRIVATE";
  document.body.appendChild(watermark);

  const setShield = (enabled) => {
    root.toggleAttribute("data-oap-bank-shielded", Boolean(enabled));
  };

  document.addEventListener("visibilitychange", () => {
    setShield(document.visibilityState !== "visible");
  });
  window.addEventListener("pagehide", () => setShield(true));
  window.addEventListener("pageshow", () => setShield(false));
  window.addEventListener("blur", () => setShield(true));
  window.addEventListener("focus", () => setShield(false));

  // Browsers do not reliably expose OS screenshots/screen recording events.
  // PrintScreen is only a weak signal on some desktop browsers, never proof.
  window.addEventListener("keyup", (event) => {
    if (event.key === "PrintScreen") {
      root.setAttribute("data-oap-bank-capture-risk", "printscreen-key");
      window.setTimeout(() => root.removeAttribute("data-oap-bank-capture-risk"), 1800);
    }
  });

  window.OAP_BANK_CAPTURE_GUARD = Object.freeze({
    webScreenshotDetectionReliable: false,
    webScreenshotBlockingReliable: false,
    privacyShieldOnBackground: true,
    sensitiveWatermark: true,
    printScreenKeyIsWeakSignalOnly: true,
    nativeAndroidFlagSecureRecommended: true
  });
})();