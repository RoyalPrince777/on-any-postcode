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
- Back and OAP World controls in the Founder-approved minimal shell;
- one omnibox and an explicit OAP WORLD / OPEN WEB trust label;
- Forward, Reload and Go are not primary visible controls in the approved minimal shell;
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

## Founder-first browser acceptance (2026-10-14 review)

The latest Founder-approved visible controls are **Back · OAP World · one omnibox · trust label**. Existing implementation may differ; this section is a requirement, not a claim of completed UI work.

The initial view must open `/world` directly, without a Market-first flash, old shell, or redundant loading stages. Open-web pages remain visibly distinct from OAP-owned pages. Preserve the existing Android WebView security fallback while the bounded first-party HTML/DOM/CSS renderer matures.

Release sequence: Founder-private install and real-device browsing evidence -> Founder acceptance -> separately authorised public deployment after security and recovery checks. No automatic public release.

### Alliance review gates

- **Gyata:** mission alignment; **Architect:** browser architecture; **Neo:** engineering lead; **Spider:** existing-code dependency review; **Octopus:** integration; **Fox:** progressive first-party independence; **Captain ALL IN:** evidence-based mission register.
- **Bagheera + Seraph:** trust and security; **Shere Khan:** adversarial review; **Tigress:** precision; **Falcon:** performance; **Owl:** independent review; **Elephant:** evidence recovery. **Queen Bee:** only for genuine distributed worker coordination.
- Agent selection is advisory, not proof that workers are running. SMI remains the intelligence brain; Guardian and HRM are systems, not agents; Founder Final controls activation.
- Reconcile the `Tigress` versus `Tygress` passport naming mismatch and Mouse's later Founder-approved restoration before asserting their runtime registration. Do not silently overwrite historical audit entries.
- A passing code test does not establish signed APK installation, real-device compatibility, production readiness or complete first-party rendering.
