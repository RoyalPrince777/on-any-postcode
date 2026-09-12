# Map Intelligence consolidation

- Renamed the public maps/weather/travel capability to **Map Intelligence**.
- Folded Movement, OAP Direct/booking and Delivery into its product contract.
- Removed the duplicate `Movement & Delivery` / `movement-delivery` public capability from the canonical registry.
- Preserved consequential backend boundaries and truth locks.
- Added regression gates for the single public surface.

This branch does not deploy production and does not modify Founder recovery PR #217.
