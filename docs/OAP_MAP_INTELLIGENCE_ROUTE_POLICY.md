# Map Intelligence route policy

Public product routing follows one rule: one capability, one canonical front door, one visible route family.

Canonical public surface: `maps-weather-travel` presented as **Map Intelligence**.

Retired public surface: `movement-delivery`.

Private or operational endpoints are not duplicate products. Routes for movement matching, bookings, consent, tracking, payments or dispatch may remain separate behind Map Intelligence when required by security, performance or governance.

Compatibility must not create a second implementation. Any future legacy-route handling should converge on the canonical Map Intelligence surface.
