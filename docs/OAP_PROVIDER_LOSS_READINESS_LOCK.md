# OAP Provider-Loss Readiness Lock

Status: BUILDING  
Owner: Human Authority / Founder  
Scope: SMI, OAP Host, GitHub connector, Render connector, Home Node, recovery evidence

## Purpose

GitHub and Render are replaceable connectors. They must not be treated as the
source of OAP authority, memory, identity, or ownership.

This lock defines the minimum proof needed before OAP may claim it can survive
loss of GitHub, Render, or both.

## 21-check gate

1. local Git history available
2. independent repository mirror available
3. release manifest preserved
4. source-integrity hashes preserved
5. provider-neutral build definition
6. provider-neutral start command
7. environment inventory preserved
8. secrets excluded from backups
9. database provider separated
10. database backup available
11. isolated database restore + readback proven
12. object-storage recovery defined
13. DNS recovery defined
14. provider-neutral health check
15. rollback artifact preserved
16. fresh-machine restore documented
17. fresh-machine restore tested
18. Home Node recovery available
19. alternate-host path defined
20. audit receipts preserved
21. Human Authority remains final

A named script, provider account, URL, architectural document, or reachable
service is not proof by itself.

## Failure scenarios

### GitHub unavailable

OAP must retain a complete local repository and an independently held mirror or
equivalent verified copy before GitHub is called replaceable.

### Render unavailable

OAP must retain provider-neutral build/start/health contracts and a proven
alternate-host recovery path before Render is called replaceable.

### GitHub and Render unavailable

All 21 checks must be backed by evidence. Even a complete evidence set does not
grant automatic failover or deployment authority.

## Boundaries

The readiness evaluator is read-only. It does not:

- copy repositories
- export secrets
- restore databases
- modify DNS
- provision infrastructure
- deploy services
- approve itself
- bypass Founder Final

No fake Green. Provider independence is an evidence claim, not an architecture
diagram.
