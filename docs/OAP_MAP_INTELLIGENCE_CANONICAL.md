# OAP Map Intelligence — Canonical Surface

Status: governed product contract.

## One front door

Map Intelligence is the single user-facing OAP surface for:

- Maps and Atlas context
- Routes and route planning
- Weather and local-condition signals
- Travel choices
- Movement
- OAP Direct and booking requests
- Delivery awareness

The existing `maps-weather-travel` slug remains the canonical compatibility URL during this cleanup. `movement-delivery` is retired as a public capability and must not become a second product/front door.

## Internal separation remains

This product consolidation does not collapse protected backend boundaries. Movement matching, bookings, tracking consent, tracking points, payments and dispatch may remain separate Engine/API routes where security, performance, consent or governance requires it.

## Truth lock

Do not claim first-party turn-by-turn routing, confirmed supplier bookings, payments, automatic dispatch, live tracking or other consequential operations until their source, consent, identity, operational and Human Authority proof gates pass.

Law: One World. One Front Door. Many Systems Inside.
