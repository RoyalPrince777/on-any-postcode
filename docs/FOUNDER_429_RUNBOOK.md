# Founder 429 recovery runbook

1. Reproduce using the anonymous handset probe.
2. Identify which layer returns 429 from response metadata.
3. If both entry paths fail identically, do not merge an alternate-path change as the incident fix.
4. Repair only the emitting layer with the narrowest auditable change.
5. Re-run the handset proof and Founder security regression checks.
6. Only then mark the incident green.
