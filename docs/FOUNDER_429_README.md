# Founder 429 recovery branch

Goal: restore reliable Founder access without weakening the Founder-only boundary.

This branch is intentionally diagnostic first. A 429 generated before Flask cannot be repaired safely by deleting or relaxing application authentication. The evidence gate identifies which boundary owns the rejection before a production fix is selected.
