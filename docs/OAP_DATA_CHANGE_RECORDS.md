# OAP Data — Change Records

OAP Data is the canonical first-party record format for governed software changes.

A pull request may feed an OAP Data Change Record, but the record is not a replacement
for Git history, HRM evidence receipts, Green Gate, Guardian, runtime proof or Founder
approval. It is a bounded projection that brings those facts into one readable change
record without inventing evidence.

Required fields:

- OAP Data ID
- Mission
- System/module
- Before
- After
- Rollback point
- Shere Khan Claw Test
- Green Gate state

Evidence fields include files changed, routes/functions affected, tests, security checks,
runtime proof, merge commit, deployment digest and explicit truth boundaries.

A GREEN label alone is insufficient for certification. Certification requires test
evidence, runtime proof, rollback evidence and a merge commit. Missing proof degrades
the record rather than silently promoting it.

The model is intentionally read-only: it does not fetch GitHub, merge, approve, deploy,
change permissions or mutate production.
