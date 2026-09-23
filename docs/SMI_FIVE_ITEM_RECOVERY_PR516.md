# SMI five-item recovery boundary — PR #516

This is an operational rollback reference, not proof of mobile controls, movement, lip-sync, Android STOP timing or independent release review.

## Exact recoverable source

- Original PR base: `8499c6b652cfa4d580e3cb0a4dc7b871b888e626`.
- Recovery guard added after head `48d6f051527d55afa8e9fdc603a2b876b0b4726b`.
- Approved unchanged character source: `static/oap/smi_live_chat_dashboard.jpg`, SHA-256 `f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b`.
- Character rig stays fail-closed: no approved separate layers, no actual frames or claimed lip-sync.
- Production and `main` are not changed by this recovery document.

## Isolated rollback — human-executed only

Before any action, re-fetch PR #516 head, its original base, `main`, and CI. Never force-push, reset `main`, or delete first-party work. If the complete PR must be abandoned, close the **draft PR** without merge and leave `main` unchanged. If only a defect in this candidate needs rollback, create a new recovery branch from current `main`, then deliberately reapply only separately reviewed SMI fixes. Do not use a broad reset or revert across unrelated humanitarian commits.

The PR's candidate changes are limited to:
- `mission_control/static/smi_canonical_controller.js`
- `mission_control/static/smi_chat_final.js`
- `mission_control/static/smi_live_chat_dashboard.css`
- `tests/test_smi_chat_ui_render_contract.py`
- `tests/test_smi_live_chat_clarity.py`

Prior to release, verify the approved image's bytes; run governed tests; independently exercise the actual Android Plus/upload, mic, STOP, send and thinking-level controls; record genuine source-derived character layers and played-audio timing; obtain physical STOP measurement and independent review. A document or green CI cannot substitute for those observations.
