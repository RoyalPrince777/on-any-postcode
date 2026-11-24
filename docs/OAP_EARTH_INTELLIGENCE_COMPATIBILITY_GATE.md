# OAP Earth Intelligence — compatibility and proof gate

Status: DESIGN ONLY — no 3D renderer, live feeds or production activation in this change.
Owner: SMI × Captain ALL IN; Founder retains final authority.

## Existing code inspected (2026-10-10)
- `templates/world.html`: OAP World front door. Keep unchanged.
- `mission_control/templates/local_map.html`: map surface uses SVG roads and route overlays, search, source status, navigation controls.
- `mission_control/static/oap_map_navigation.js`: browser navigation, heading/perspective transform, optional speech guidance. A CSS perspective transform is **not** a 3D Earth globe.
- `mission_control/global_transport_views.py`: first-party transport front door and explicitly gated live execution.
- `docs/OAP_ATLAS_MAP_INTELLIGENCE_LOCK.md`: canonical On Any Place name, hierarchy, source timestamps, stale state, privacy and no-fake-live requirements.

## Product boundary
Public entry remains **On Any Place** within OAP World. **OAP Earth Intelligence** is a capability, not a replacement homepage or competing map. Preserve /oap-map and navigation behaviour. Prefer a separately loadable Earth view behind an explicit user action; keep the current SVG map as default and fallback.

## Minimum implementation slice (not yet implemented)
1. Establish actual available renderer dependencies, bundle/licence/asset constraints and low-memory Android WebGL support. No assumption that Cesium, 3D tiles or GPU acceleration is present.
2. Add a lazy-loaded globe viewer under an existing On Any Place route, without changing current route contracts. Do not download heavyweight assets before opt-in.
3. Show an accessible non-WebGL fallback, clear loading/recovery, and no old-shell flash.
4. Earth view starts with geographic orientation only. **No** planes, ships, satellites, traffic cameras, critical infrastructure overlays, user tracking or AI live assertions by default.
5. Any later external layer requires data licence, provenance, timestamp, stale-state UI, source health, privacy review and Guardian authorization where relevant.
6. Preserve postcode → borough → region → country → continent hierarchy and current navigation. No false live status.
7. Require actual mobile browser and production-equivalent route tests before any Green claim.

## Release gates
- Existing /world and /oap-map regressions pass.
- No additional map dependency loaded for users who never open Earth view.
- Slow/no-WebGL device gets usable fallback.
- Explicit opt-in for precise location; no hidden collection.
- Asset licensing, origin/CSP and network dependencies reviewed.
- Source provenance shown for every dynamic data layer.
- Actual CI + runtime proof on exact head SHA; merge/production gates remain separate.

## Roles
SMI: architecture and truth. Captain ALL IN: continuity. Fox: data routes. Spider: dependencies. Octopus: layer coordination. Queen Bee: distributed jobs only if needed. Neo: interface. Shere Khan: adversarial proof.

## Current result
Architecture compatibility review documented. Renderer selection, implementation, tests, mobile verification and production deployment remain **unproven**.
