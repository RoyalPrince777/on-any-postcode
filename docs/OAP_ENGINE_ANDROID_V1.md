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
