# OAP Engine + OAP Android roadmap

Status: **Generation 1 foundations started; not standards-complete and not a custom ROM**

## OAP Engine

OAP Engine is the first-party rendering engine programme beneath OAP Browser.

The v0 repository slice now owns a deterministic path:

HTML text -> OAP parser -> OAP layout -> OAP display list

This is intentionally a small safe subset. It does not yet implement the CSS
cascade, JavaScript, DOM mutation, forms, media, accessibility, networking,
storage, compositing, GPU rasterisation, service workers, WebRTC, WebGL/WebGPU,
or the modern standards surface required for arbitrary-web compatibility.

Therefore:

- **OAP Engine v0 exists as first-party source code.**
- **OAP Browser does not yet use OAP Engine for general websites.**
- **Android System WebView remains the active general-web renderer.**
- **No claim is made that OAP Engine is a Chromium/WebKit/Gecko replacement yet.**

### Engine graduation path

1. DOM and HTML tree.
2. CSS parser, cascade and computed style.
3. block/inline/flex/grid layout.
4. paint/display list and clipping.
5. raster/compositor abstraction.
6. networking, URL, cache and cookie jars.
7. JavaScript VM integration or first-party JS runtime programme.
8. forms/input/accessibility.
9. media/images/fonts.
10. sandbox/site isolation.
11. WPT-driven standards compatibility.
12. Android renderer embedding.
13. make OAP Engine default for supported pages.
14. progressively remove WebView dependency only when compatibility/security proof exists.

## OAP Android

OAP Android is the first-party mobile OS/distribution programme for OAP.

It must remain technically accurate: Android's open-source platform, the Linux
kernel and device/vendor components are upstream foundations until OAP replaces
specific layers. Building an OAP-branded distribution from AOSP-compatible
sources is valid; claiming every driver, modem firmware or kernel component as
OAP-authored is not.

### Generation model

**Generation 0 — current**
- stock Android/Linux host;
- OAP World application;
- OAP Browser shell;
- System WebView for general web rendering.

**Generation 1 — OAP Android distribution**
- OAP-controlled system build configuration;
- OAP launcher/front door;
- Guardian-first privacy defaults;
- OAP Browser built in;
- My Card, Link Up, Face Up, OAP World, SIKA and SMI integration;
- OAP-owned update/recovery policy;
- signed system images for explicitly supported devices.

**Generation 2 — OAP device platform**
- verified boot ownership;
- signed OTA infrastructure;
- recovery image;
- hardware compatibility programme;
- controlled kernel configuration where legally/licence permitted;
- reduced vendor dependency through selected supported hardware;
- optional future OAP silicon/reference platform.

## Non-negotiable truth gates

A custom Android distribution becomes Green only after a real system image can
be built reproducibly, signed, booted on a named supported device, updated,
recovered and tested without weakening security.

An OAP browser engine becomes Green for the open web only after standards,
security, compatibility and fuzzing evidence show that it can safely render the
target web surface.

Names and architecture do not satisfy either gate.


## Implemented since the initial v0 slice

OAP Engine now also contains:

- a first-party DOM tree with parent/child ownership, ids, classes and text-content traversal;
- hidden executable/style/template content excluded from user text projection;
- a bounded CSS parser;
- tag, class and id selector matching;
- deterministic specificity/order cascade;
- inline-style precedence for the supported property allow-list; and
- regression tests for malformed HTML recovery, cascade precedence and unsupported-selector rejection.

This materially advances the source foundation, but it still does not make OAP
Engine standards-complete or the default renderer for arbitrary websites.


## Engine v1 main render path

The main OAP Engine renderer now consumes the OAP-owned DOM and CSS modules directly:

HTML → OAP DOM → OAP CSS cascade → bounded layout → deterministic display list.

Implemented layout effects include:
- display:none suppression;
- block/inline selection;
- integer/px margin and padding;
- inherited font-size, font-weight, color and text-align;
- font-size-driven line geometry and wrapping;
- left/center/right text alignment;
- nested link href propagation;
- stylesheet collection from document style nodes.

This is still a bounded subset. It does not claim full CSS box layout, flexbox, grid, floats, positioning, transforms, generated content, JavaScript, raster/compositor ownership, accessibility, media, networking, cookies/storage, sandboxing, or standards completeness.


## Android native OAP Engine bridge v1

Android now contains a first-party OAP Engine display-list surface. The Python engine emits a versioned contract (`engine = OAP_ENGINE`, `contract_version = 1`) and Android validates that contract before drawing it natively.

Bridge properties:
- native Canvas-based OAP display-list rendering surface;
- strict document and item count/geometry limits;
- text and link item allow-list;
- HTTP/HTTPS-only link handoff;
- no JavaScript interface or privileged WebView bridge;
- explicit WebView fallback remains available;
- the native surface is not yet the default general-web renderer.

This closes the first Android embedding foundation only. It does not yet provide a transport that automatically supplies arbitrary supported pages to the native surface, and it does not make OAP Engine standards-complete. System WebView remains the general-web renderer until compatibility, security and page-support evidence justifies changing that boundary.


## Automatic supported-page routing v1

Android now attempts the native OAP Engine path automatically for same-origin OAP navigation. The server is the certification owner: only the allow-listed public paths `/`, `/world`, and `/search` currently return native OAP Engine documents. Unsupported paths return an explicit WebView fallback signal.

Routing boundary:
- same-origin OAP navigation asks `/api/oap-engine/document` first;
- the endpoint renders the actual current public OAP HTML through the canonical OAP Engine rather than maintaining duplicate native-page copy;
- relative page links are normalized to safe absolute HTTP/HTTPS URLs;
- Android fetches the versioned contract on a background executor with connection/read/document-size bounds;
- a missing, unsupported, invalid or failed engine document falls back automatically to WebView;
- external web addresses bypass the engine endpoint and stay on the WebView path;
- the general web renderer remains Android System WebView.

This makes the native engine automatic for the certified supported OAP slice only. It is not a claim that all OAP routes or arbitrary websites are OAP Engine compatible.


## Engine security/runtime foundations v1

The first-party engine now includes additional bounded software foundations:
- normalized HTTP/HTTPS origin identity and same-origin checks;
- safe URL resolution that fails closed outside web schemes;
- per-origin in-process storage with key/value/count/quota limits;
- accessibility projection for landmarks, headings, links, lists and common controls;
- bounded form/control modelling with GET/POST method normalization, action resolution, same-origin classification, required/disabled state and password-value suppression;
- hard HTML input, DOM node/depth, CSS input/rule/declaration ceilings;
- deterministic malformed-HTML stress coverage;
- the canonical RenderDocument contract now carries paint items, accessibility metadata and form models together.

Truth boundary: storage is not yet durable browser storage; forms are modelled but are not submitted by OAP Engine; Android does not yet expose a full native accessibility virtual-view tree; these foundations do not constitute a JavaScript VM, GPU compositor, media stack, arbitrary-web sandbox or standards-complete engine.
