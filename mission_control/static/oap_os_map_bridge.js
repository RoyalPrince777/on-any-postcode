/* OAP OS Generation 0: first-party Map Intelligence host adapter.
 * Browser/PWA on Android is NOT a native APK, replacement OS, or proof of
 * physical-device certification. Never acquires location or changes OS state.
 */
(() => {
  "use strict";
  const indicator = document.querySelector("[data-oap-os-map-runtime]");
  if (!indicator) return;
  const isAndroid = /Android/i.test(navigator.userAgent || "");
  const standalone = window.matchMedia?.("(display-mode: standalone)")?.matches === true
    || navigator.standalone === true;
  const host = isAndroid ? "Android host" : "web host";
  indicator.dataset.oapOsMapRuntime = isAndroid ? "android-web" : "web";
  indicator.dataset.installMode = standalone ? "standalone" : "browser";
  indicator.textContent = "OAP OS · Map Intelligence · " + host
    + (standalone ? " · installed web shell" : " · browser");
  const roadState = document.querySelector("#road-source-state");
  if (!roadState) return;
  const update = () => {
    const error = !roadState.hidden && /unavailable/i.test(roadState.textContent || "");
    indicator.dataset.roadSource = error ? "unavailable" : "unverified";
    // The UI never calls roads "live" merely because a local fixture rendered.
    indicator.setAttribute("aria-label", "OAP OS map runtime; road source "
      + (error ? "unavailable" : "not independently verified"));
  };
  new MutationObserver(update).observe(roadState, {
    childList: true, characterData: true, attributes: true,
    attributeFilter: ["hidden"]
  });
  update();
})();
