# OAP War Room Runtime v1 Lock

Status: LOCKED
Owner: Human Authority / Founder
Scope: Command Center, SMI Command, War Room, Signals Command, Function Health, Green Gate, HRM, Guardian / Aegis, Movement / Map, ISAC, Connected Systems

## Master purpose

War Room Runtime v1 is the private Founder-controlled decision chamber that turns OAP from labelled readiness into evidenced readiness.

It must never be a public spectacle, fake control panel, autonomous authority, military command surface, or emergency-service authority surface.

War Room reviews. Guardian protects. Green Gate certifies. HRM remembers. Founder decides.

## Placement

Command Center -> SMI Command -> War Room.

War Room receives signals from:

- Active Signal Engine
- Function Health
- Green Gate
- Guardian / Aegis
- HRM Memory
- Movement Intelligence
- Map Intelligence
- ISAC
- Connected Systems
- Render / GitHub / Neon status surfaces
- Local Device / Home Node proof

War Room outputs:

- read-only mission status
- evidence summary
- risk state
- alignment result
- Aegis / Guardian result
- Green Gate recommendation
- HRM receipt requirement
- Founder approval requirement
- safe public brief only when explicitly approved

## Required private routes

All routes are Founder-only. POST routes must be CSRF protected and fail closed.

- GET /mission/war-room
- GET /mission/war-room/status
- GET /mission/war-room/missions
- GET /mission/war-room/missions/<mission_id>
- POST /mission/war-room/start
- POST /mission/war-room/evidence/add
- POST /mission/war-room/alignment-check
- POST /mission/war-room/aegis-check
- POST /mission/war-room/guardian-check
- POST /mission/war-room/function-health
- POST /mission/war-room/green-gate
- POST /mission/war-room/hrm-record
- POST /mission/war-room/approval/request
- POST /mission/war-room/export-safe-brief

If a route is not implemented yet, the dashboard must show BUILDING or LOCKED with reason. It must not show LIVE.

## Required dashboard panels

- Live Mission
- Evidence Board
- Signal Board
- Risk Board
- Alignment Check
- Aegis / Guardian Check
- Function Health
- Green Gate
- HRM Receipts
- Agent / Organ Voices
- Founder Approval
- Fresh Logs
- Still Needed
- Safe Export Brief

## Required buttons

Every button must be one of: WORKING, BUILDING, LOCKED, BLOCKED, or PRIVATE.

- Start War Room
- Load Mission
- Add Evidence
- Run Alignment Check
- Run Aegis Check
- Run Guardian Check
- Run Function Health
- Run Green Gate
- Check Fresh Logs
- Check Routes
- Check Buttons
- Check Public / Private Boundary
- Check Founder Access
- Check HRM Write
- Ask SMI
- Ask Guardian
- Ask Challenger
- Ask Nirmata
- Send to Movement Intelligence
- Send to Map Intelligence
- Send to ISAC
- Record Decision to HRM
- Request Founder Approval
- Mark LIVE
- Mark BUILDING
- Mark LOCKED
- Mark BLOCKED
- Export Safe Brief
- Close Mission

No dead buttons. No pretend buttons. No fake green controls.

## Mission record shape

A War Room mission record must contain:

- mission_id
- title
- objective
- owner
- scope
- affected systems
- public/private scope
- state
- risk level
- evidence list
- signal summary
- alignment result
- Aegis / Guardian result
- Green Gate result
- HRM receipt state
- Founder approval state
- blocked items
- next safe step
- rollback/correction path
- created timestamp
- updated timestamp

## Evidence types

- GitHub commit
- Render deploy state
- fresh log scan
- route 200 / 302 / 403 / intentional 404 result
- no 500s after testing
- button click result
- database status
- Neon migration/checksum result
- HRM receipt
- Guardian block
- Aegis pass/block
- source health result
- local device terminal proof
- Founder approval receipt

No evidence = no green.

## Alignment check

War Room must check:

- Born Local. Built Global.
- Earth is our turf.
- One World -> One Front Door -> Many Systems Inside.
- Community before middlemen.
- Proof before execution.
- Certification before sharing.
- Audit before automation.
- Human approval before real-world action.
- No fake green.
- No duplicate systems.
- Upgrade only.

## Aegis / Guardian check

War Room must block or flag:

- hidden tracking
- covert location collection
- private dashboard leaks
- exposed secrets
- unsafe movement dispatch
- emergency-service impersonation
- military/tactical targeting
- biometric identity from ISAC/RF
- public ISAC accuracy claims without measured evidence
- SIKA bank/e-money/deposit claims
- music/platform/distribution claims without proof
- youth-risk exposure
- destructive DB actions without approval
- autonomous deploy/spend/publish/security changes

## Fresh logs panel

Fresh Logs must show:

- latest commit
- deploy status
- service status
- 5xx count
- error count
- critical count
- alert count
- emergency count
- latest tested routes
- slow route warnings
- failed route warnings
- private route access attempts
- Guardian blocks
- HRM receipt writes
- source-health failures

Green requires:

- deploy live
- public routes return 200
- private routes return Founder-only 200 or safe private block
- no 500s after route/button testing
- error/critical/alert/emergency count is 0
- Guardian blocks unsafe actions safely
- HRM writes important receipts or shows locked reason

## Still Needed panel

The dashboard must permanently show remaining blockers:

- positive route proof
- button click proof
- HRM write proof
- Guardian block proof
- public/private leak proof
- Neon DB proof
- Function Health probes
- Green Gate auto-status
- Active Signal Engine
- source health connectors
- monitoring alerts
- hardware evidence where required

## Green Gate states

- LIVE: implemented and checked
- CERTIFIED: proof, HRM record and required Human approval exist
- BUILDING: surface exists but proof/action/data incomplete
- LOCKED: intentionally unavailable until evidence, permission, compliance or approval exists
- BLOCKED: unsafe, broken or not allowed
- PRIVATE: Founder-only
- GUARDED: Guardian/Aegis active
- REMEMBERED: HRM receipt exists
- APPROVAL: Founder decision required

## A4 boundary

War Room may operate under A4 supervised workflow rules only:

- max 21 steps
- checkpoint every 3 steps
- audited
- reversible where possible
- fail-closed
- pre-approved bounded actions only

A4 cannot self-approve, deploy without approval, migrate production databases, spend, transfer value, publish publicly, change auth/security/permissions, dispatch real-world action, alter constitution or promote itself.

A5 remains locked.

## Public output boundary

A safe public War Room brief may say:

- system update completed
- public routes remain available
- private controls remain protected
- no critical runtime errors detected
- some features remain building until proof is complete

It must not expose:

- secrets
- tokens
- private logs
- private security details
- Founder identifiers
- database internals
- ISAC internals
- unreleased operational strategy
- actionable abuse details

## Runtime v1 green checklist

War Room Runtime v1 is green only when:

1. Private dashboard opens for Founder.
2. Non-Founder access fails closed.
3. Status API returns redacted read-only status.
4. Mission cards render.
5. Evidence board renders.
6. Signal board renders.
7. Risk board renders.
8. Alignment check has a real result or locked reason.
9. Aegis / Guardian check has a real result or locked reason.
10. Function Health has live probe results or locked reason.
11. Green Gate assigns true state.
12. HRM receipt action saves or returns locked reason.
13. Founder approval state is explicit.
14. Safe export brief is private and redacted.
15. Fresh logs show no 500s after route/button testing.
16. No fake green status is shown.

## Final lock

War Room is the proof chamber for the OAP organism.

It recommends only after evidence. It cannot override Founder. It cannot bypass Guardian. It cannot certify fake green. It cannot unlock physical ISAC, A5, money movement, production DB mutation or public authority claims without the required evidence and Human Authority approval.

Born Local. Built Global. Earth is our turf.
