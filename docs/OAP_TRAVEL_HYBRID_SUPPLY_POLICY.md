# OAP Travel — Direct Supply + External Lookup Policy

## War Room decision

OAP Travel persists **OAP Direct only**.

Canonical flow:

`OAP Travel → OAP Direct → Certified Supplier → Listing → Pictures → Availability → Pricing → OAP Booking → Reservation`

Optional research flow:

`Human request → External lookup → Compare/reference → discard or re-fetch later`

## Locked rules

> No external travel service is an OAP partner by default.

> External lookup data is not imported as OAP Direct inventory.

> No external source may become indispensable to OAP Travel.

Booking.com may be queried on demand through an available lookup surface when the Founder asks. That lookup does not create a Booking.com partnership, Render integration, OAP inventory record, booking handoff or payment authority.

## Source classes

- **🟢 OAP Direct** — persisted supply through OAP's first-party marketplace.
- **👑 Certified OAP Supplier** — supplier with a direct Certified OAP relationship.
- **🔎 External Lookup** — transient reference/search evidence only; never OAP Direct supply.

## Listing media

OAP Direct listing pictures are first-party OAP media. Supported image types are JPEG, PNG and WebP. Images are attached to a real OAP listing, integrity-hashed, bounded to eight pictures per listing and served only when the associated listing and supplier are public and Certified.

OAP does not copy external provider photography into OAP Direct without an independent right to use that media.

## Authority boundary

External services do not become OAP authority, SMI, an Intelligence World, an agent, supplier authority, OAP Booking, payment execution or platform ownership. OAP Direct reservations use the OAP-owned quote, hold and reservation flow.

Payment capture, OAP Pass issuance and commission settlement remain separately governed production gates.
