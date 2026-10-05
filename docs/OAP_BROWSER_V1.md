# OAP Browser v1 — first-party front door to OAP and the open web

Status: **bounded Android browser-shell implementation**

## Identity

OAP Browser is not a Safari, Edge, Chrome, Brave, AOL or Internet Explorer clone.

Its product law is:

**One World → One Front Door → Many Systems Inside → Open Web When Chosen**

OAP World remains home. OAP Browser is the controlled doorway that connects the
home environment to direct web addresses without turning third-party websites
into trusted OAP surfaces.

## What v1 actually implements

The Android OAP World host now provides:

- an OAP-first omnibox;
- Back, Forward, OAP Home and Reload controls;
- direct HTTP/HTTPS navigation;
- automatic HTTPS for host-like input such as `example.com`;
- first-party OAP Search routing for ordinary words and questions;
- third-party cookies disabled in the host WebView;
- file/content URL access disabled;
- mixed-content blocking;
- Safe Browsing enabled;
- geolocation disabled at the browser-host layer;
- non-HTTP(S) schemes blocked; and
- an explicit `OAPBrowser/1.0` user-agent marker.

## What makes the model OAP-specific

The omnibox is not "search the commercial web by default."

Routing is intentional:

1. OAP paths such as `/linkup` stay inside the OAP origin.
2. Full HTTP/HTTPS URLs open as web destinations.
3. Host-like text such as `example.com` becomes HTTPS.
4. Everything else routes to OAP Search.

This keeps discovery first-party while preserving the open web.

## Security boundary

A web page opened by OAP Browser is not automatically OAP-certified, trusted,
owned, indexed, private or governed by OAP.

The browser does not grant arbitrary websites access to:

- SMI authority;
- My Card authority;
- SIKA authority;
- Link Up message bodies;
- Founder / Mission Control authority; or
- OAP server secrets.

The Android host continues to rely on Android System WebView for HTML/CSS/
JavaScript rendering. v1 therefore does **not** claim a first-party rendering
engine.

## Not yet proven / not yet built

- OAP-owned global crawler and web index;
- OAP-owned rendering engine;
- browser history/bookmark sync;
- download manager;
- per-site permission dashboard;
- reader mode;
- tracker/content-blocking engine;
- encrypted cross-device browser sync;
- production APK signing/distribution proof;
- real-device external-site compatibility matrix; or
- browser-engine security patch pipeline owned by OAP.

Those remain separate evidence gates. No feature above is Green merely because
the browser shell exists.
