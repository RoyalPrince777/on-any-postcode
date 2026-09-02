# The Spot UI state semantics

The priority-card labels are visitor guidance, not infrastructure health.

- **Browse** — the visitor can open the public discovery/read surface. This does not imply transactional readiness.
- **Local data** — the visitor can open the existing location/weather lookup and request bounded local context.
- **Protected** — the destination belongs behind the existing authenticated private boundary.
- **Action gated** — the public entry surface may be viewed, while operational actions remain subject to their existing safety/readiness gates.

These labels must never be converted into generic green/live claims without evidence from the underlying capability.
