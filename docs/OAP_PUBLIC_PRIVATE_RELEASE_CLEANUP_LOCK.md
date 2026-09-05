# OAP Public / Private Release Cleanup Lock

Status: ACTIVE
Date: 2026-09-05

## Public OAP World rule

Public OAP World must not display private command wording. Public pages show only public products, public routes, public install surfaces and public-safe status.

Public surfaces may show:

- OAP World
- The Spot
- The Link
- Link Up
- Pulse
- Signal
- OAP Atlas
- OAP Direct
- Movement
- Market
- OAP OS install
- 21 public signal legend

Public surfaces must not expose:

- SMI command internals
- Living Kernel internals
- Guardian/Aegis internals
- HRM internal records
- War Room internals
- private route names
- private debug output
- provider secrets
- production database details

## OAP Atlas live-ready rule

OAP Atlas is the public place surface for continent-to-postcode navigation, attractions, weather signals, movement and OAP Direct request entry.

Atlas may show live place and weather data only when the configured source returns data. It must not claim live map, live route, live traffic, confirmed booking or supplier confirmation without timestamped source evidence.

## OAP Direct rule

OAP Direct may be live for listings, attractions, stays, offers, quote requests and Direct requests. Confirmed reservation claims, payment capture and supplier confirmations remain locked until certified supplier proof and HRM receipts exist.

## SMI chat rule

SMI chat remains a private command/intelligence workspace. It can support messages, voice input, file/media attachment, code mode, stop control, copy actions, history and safe debug output. It must not leak private state to public OAP World.

## War Room completion rule

War Room can be complete as an operational command surface when it can organise evidence, score signals, expose proof lanes, prepare command packs, show hard locks and route to Founder approval. It still cannot silently deploy, spend, migrate, dispatch, confirm bookings or publish unsupported claims.

## Install rule

OAP OS is a public installable shell using the web manifest, service worker and install controller. It must cache only public assets and must not cache private command routes.
