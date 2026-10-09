# SMI Command Homepage — first-party build contract

## Scope
- Route: `/smi-home` (isolated preview; `/world` remains the live front door).
- Source direction: user-provided `3329(5).png` and `SMI Cyberpunk Command Centre.png`.
- Responsive dark command centre: OAP header, central brown-skinned SMI character, Captain ALL IN control, side navigation and evidence-only intelligence.
- Current character is a CSS illustration **not** a pixel-faithful copy of the reference. Original imagery is not committed to the repository.
- The Captain drawer is a navigation and mission-coordination entry point, **not** an autonomous running agent or assistant chat.
- Never fabricate users, live nodes, system health, agent votes or production readiness.

## Visible actions
- `Enter My World` → `/my-world`.
- `Explore OAP World` / `World Menu` → accessible in-page navigation drawer.
- `Captain ALL IN` → Captain drawer with human-authority notice and War Room link.
- `Close`, Escape or backdrop → closes drawer, restores focus and page scroll.

## Acceptance gates
1. Flask serves `/smi-home` without changing `/world`.
2. Header Captain remains visible on desktop and mobile.
3. Navigation drawer keyboard focus remains inside and Escape closes it.
4. Screen-reader labels and reduced-motion preference work.
5. Real destinations resolve, including authenticated routes with appropriate gates.
6. No invented real-time metrics, synthetic Green indicators or unauthorized controls.
7. Browser acceptance passes on mobile and desktop before considering a front-door switch.
8. Founder Final explicitly approves replacing `/world` after verification.

## Next
- Review approved first-party character image rights and prepare responsive optimized asset.
- Confirm destination routes against Flask URL map.
- Add browser screenshot and keyboard regression coverage.
- Do not treat green CI alone as production certification.
