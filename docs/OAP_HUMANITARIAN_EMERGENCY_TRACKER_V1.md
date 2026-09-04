# OAP International Humanitarian Emergency Tracker v1

## Purpose

Provide live, source-grounded civilian humanitarian emergency awareness to International Humanitarian Intelligence, Matrix world state and SMI without creating military, surveillance, targeting or autonomous emergency-response authority.

## Live source path

```text
GDACS disaster alerts ─┐
WHO Disease Outbreak News ─┼─> OAP source adapters
UNHCR displacement context ─┘        ↓
                              validate / bound
                                    ↓
                           deduplicate / classify
                                    ↓
                         provenance + freshness
                                    ↓
                              Guardian filter
                                    ↓
                      privacy-reduced Matrix events
                                    ↓
                    International Humanitarian Intelligence
                             ↓                 ↓
                            SMI        Founder Tracker Dashboard
```

ReliefWeb is registered but remains gated until OAP has a pre-approved `appname` as required by ReliefWeb API policy.

## Runtime behavior

- GDACS: recent Orange/Red sudden-onset hazard and disaster signals.
- WHO Disease Outbreak News: authoritative acute public-health updates. OAP does not invent a clinical severity level; events are labelled `WHO Update`.
- UNHCR Refugee Data Finder nowcasting: displacement context only, not an emergency alert and never individual-level tracking.
- ReliefWeb: inactive until a pre-approved appname is configured.
- Source failures fail closed and never become fake events.
- Live snapshots are cached briefly to reduce unnecessary source load.
- The Founder dashboard automatically refreshes from the bounded cache.
- SMI only fetches this current context when a request routes to International Humanitarian Intelligence and includes crisis/emergency intent.

## Matrix event boundary

Matrix receives only bounded emergency abstractions:

- source and source event id
- category and event name
- source-provided alert label
- countries when present
- coarse event geometry when an authoritative hazard source provides it
- observed/inferred label
- civilian-only flag

Matrix does not receive precise civilian locations, personal identities, raw displacement records, targeting information or military overlays.

## Permanent no-go boundaries

- no targeting or target lists
- no military command or operational overlays
- no weapons support
- no civilian surveillance or individual tracking
- no covert crowd tracking
- no autonomous aid dispatch
- no autonomous public warning/broadcast
- no legal adjudication
- no claim that a route is safe without separately verified OAP navigation evidence

Human Authority remains final.
