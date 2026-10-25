# OAP Home V2 — Founder Royal UI/UX reference

Status: **Founder-approved visual target / bounded source implementation; physical Android acceptance outstanding**.
Owner: Founder Final. Scope: personal OAP Home V2 at `/home-v2` only.
Reference: Founder-provided 2026-10-25 black/gold Earth-screen artwork. It is a
design target, **not** evidence that a native phone OS, weather service, calendar
event, browser integration or all nine destinations operate independently.

## Fixed visual hierarchy

1. Royal crowned OAP brand over a gold-lit Earth backdrop, “ON ANY POSTCODE / HOME”
   and “Born Local. Built Global.”
2. Device-local date and clock; separate weather/calendar world-time widgets.
3. A **large first-party OAP catalogue search** with explicit scope and guarded
   access to Founder SMI. Web-wide search is **not** implemented through this field.
4. Nine illustrated route-backed app destinations in this exact order:
   OAP World, Link Up, SIKA; Maps, Mail, Market; TV, Arena, Library.
5. Personal phone dock with Phone, Messages, Internet, Camera, All Apps.
6. Existing Home/World/Store/PTT navigation remains reachable within Home V2.
   The Spot, The Link, Store and Connect 4 stay available in the existing app paths.

## First-party assets and UI contract

- `templates/home_v2.html` — server-rendered page, responsive phone layout,
  keyboard focus, safe-area dock, reduced-motion support and no invented data.
- `static/oap/home_v2_royal_earth.svg` — locally hosted gold globe backdrop.
- `static/oap/home_v2_royal_tiles.svg` — nine locally hosted vector illustrations.
- The new SVG assets recreate the layout **in the style of** the approved reference
  rather than asserting pixel-perfect identity with the original raster artwork.
- All app cards have real, explicitly routed destinations. Authentication-gated
  destinations must continue to enforce current server permission checks.
- Phone/Messages invoke platform URL intents where supported, not OAP-owned
  telephony. Camera remains blocked with explanation pending native integration.
- Internet has an explanatory control; it does not silently redirect to OAP
  World or pretend that this web page can launch the separate Android app.
- Search continues to use `GET /search?q=...` and only returns the existing
  public OAP app catalogue. No cross-site crawl, AI web answers, microphone
  recognition, access to private chat or SMI data is implied.

## Local first screen versus public World

- With the explicit `OAP_LOCAL_MODE=true` V2 test server on
  `127.0.0.1:5050`, visiting the bare `/` address now redirects to
  `/home-v2` instead of `/world`. This is the personal phone homepage.
- `/home-v2` always remains the explicit Royal Home V2 URL.
- `/world` remains a separate World route. Its default public-store
  fallback can show Local Marketplace; that is **not** the personal homepage.
- `/world?source=oap-os` remains the public OAP World front door used by
  the existing OAP OS browser/PWA manifest. Do not retarget that shared
  manifest to Home V2 or to the local marketplace.
- A browser bookmark, previously opened tab, or preinstalled PWA pointing
  at `/world` will still open `/world`. For personal Home V2, use the
  direct `/home-v2` URL or a separate bookmark. No phone system launcher
  or installed app start URL has been changed by the root redirect.

## Separate identity boundaries

- **OAP Home V2** — personal browser-based dashboard.
- **OAP Internet** — distinct Android browser app, currently named separately in
  `android/oapworld/src/main/AndroidManifest.xml` (package ID unchanged).
- **OAP Home Node** — private, supervised first-party inference/organism workers;
  does not start or stop when the V2 page loads.
- **OAP World** — public front door with its own route and trust boundary.
- **SMI Command Center** — Founder-only area requiring independent authentication.

## Actual information, not examples

- Clock and supported world-city times are rendered using the device clock
  and IANA time zones. No literal “12 October”, “19:30” or fabricated offsets.
- Weather stays “Live local weather not connected” until sourced and checked.
- Calendar stays “Calendar not connected” until consented and checked.
- Rendering a static header, app card, or source image does not prove the
  native Android camera, microphone, launcher, location or separate app handoff.
- A future source connector must fail closed, record provenance and freshness,
  and be reviewed by Guardian/Aegis if it handles private calendar/location data.

## Mission-to-100 proof gate

- **Source:** exact revision, stable template, local SVGs and route test results.
- **Device:** screenshot + HTTP status from real Redmi A5 V2 server, tile
  navigation, search submission/results/back path, scrolling, safe-area dock,
  settings/dialogs, touch targets, reduced-motion and browser console errors.
- **Native:** Android package label, install/relaunch/update, WebView/app handoff,
  permission controls and signature proof are separate from V2 browser tests.
- **Release:** never infer signed APK, deployed HTTPS, public web-wide search,
  backend readiness or Founder Final from a passing source test.
- **Recovery:** preserve the original `~/on-any-postcode` Home Node checkout;
  do V2 review work in `~/oap-v2-review`. No force reset, cleaning, uninstall or
  app replacement as part of this source-only UI alignment.
