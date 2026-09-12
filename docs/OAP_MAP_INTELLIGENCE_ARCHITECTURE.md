# Map Intelligence architecture

## UI
One visible Map Intelligence surface. It presents Map, Routes, Weather, Travel, Movement, OAP Direct/Booking and Delivery as tools within one product.

## API
Existing bounded endpoints may remain distinct. A public product consolidation is not permission to merge authentication, consent, booking, tracking, payment or dispatch boundaries.

## Engine
Routing, movement matching, booking persistence, weather/location resolution and future dispatch logic remain independently governable engines behind the single UI.

## Compatibility
`maps-weather-travel` remains the canonical public slug for this release. `movement-delivery` is retired from the public capability registry rather than maintained as a second implementation.

## Safety
Consequential actions remain fail-closed until their existing proof, consent, identity and Human Authority gates pass.
