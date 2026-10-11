# HRM Elephant Family: governed upgrade

This document records the Founder-approved design direction, not a live deployment.

## Existing canonical passports

- **Colonel Hathi** (`JUNGLE-HATHI-001`): Operations Commander; planning, coordination and readiness review. No independent execution authority.
- **Hathi Jr** (`JUNGLE-HATHI-JR-001`): Continuity Scout; context gathering, observation and continuity analysis.
- **Hathi** is an alias of Colonel Hathi, not a separate agent.

Sources: `mission_control/agents_legacy.py`, `mission_control/war_room.py`, `mission_control/arena_agents.py`.

## Authentic character proposals

- **Winifred**: Colonel Hathi's wife and Hathi Jr's mother in Disney's 1967 adaptation. Proposed welfare and family continuity specialist; **not yet a registered OAP agent**.
- **Elephant Patrol**: proposed collective observation and coordination capability. Other patrol elephants have no reliably established individual names; do not invent agent passports.
- Kipling's Hathi and his three unnamed sons belong to a different literary continuity. Do not combine them into a fabricated single roster.

## HRM integration constraints

1. Reuse the existing Jungle Book family registry. Avoid duplicate identities, databases or command structures.
2. Apply canonical MBS 777 checks from `mission_control/hrm_agent_lifecycle.py` to each individually registered agent; the collective patrol is not an independent human authority.
3. Retrieval and memory claims must carry provenance; missing evidence remains missing.
4. Winifred and the Elephant Patrol remain proposals until separately registered and tested through the existing HRM process.
5. Guardian, permissions, privacy, audit and Founder Final remain mandatory. No automatic promotions or deployment.
6. Runtime capabilities, CI and production behaviour are **not established** by this document.
