# Original SMI artwork release gate

Approved image bytes are present in the chat but **not yet in GitHub**. Do not merge or deploy the artwork PR until both original PNGs are checked in at:

- `static/oap/smi_enter_my_world.png` (SHA-256 `114852c665388f8b3cba5c3a5f667631e4a69ac88de2af2b30a3c5f6fbaec01b`)
- `static/oap/smi_global_intelligence_command_centre.png` (SHA-256 `9417a1293108350ccb6c3751377c9530d287a628c54f0659272c7c990cda4df3`)

They are bundled as `oap_smi_artwork_upload.zip` in the conversation. In GitHub's **real-artwork branch**, add both PNGs at the exact paths (not just the zip), then confirm checksums, CI, merge and exact Render commit. The release test intentionally fails while the assets are absent.

The Founder page is only a static background for the canonical server-verified password form; the image does not receive or hold a password. It preserves CSRF, lockout, fail-closed auth, safe redirect and Founder/private separation. The dashboard uses the approved still image for the visual scene but all actions/statuses remain distinct live code; text burned into artwork is **not proof**. CSS-built character stays as fallback if the image request fails.

No fake green: image load, authenticated Founder sign-in, mobile status/21 Signals, Chat and Master Tools interaction must be verified separately. 
