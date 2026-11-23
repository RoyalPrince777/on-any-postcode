# SMI Android motion evidence gate v0.1

This offline gate evaluates a receipt from a real, Human-observed Android run.
It cannot manufacture evidence, approve production, publish assets or connect
the isolated motion candidate to the live SMI page.

Acceptance requires the exact approved source, all seven layer hashes, an
Android device identity, fresh test time, played-audio clock delta no greater
than 80 ms, STOP acknowledgement no greater than 50 ms, confirmed audio and
motion cessation, background STOP, exact-character visual integrity and
explicit Human visual approval.

An accepted receipt advances only the 75% Aegis evidence decision. The result
always keeps `productionApproved` and `humanFinalApproved` false. The separate
100% Green Gate and Founder Final remain mandatory.

## Browser timing in the existing Android Proof receipt

The canonical source-pixel renderer exposes a bounded `performanceWindow` of
the latest 600 canvas-submission intervals: measured FPS, p50/p95/max frame
interval, p95 drawing cost and intervals over 1.5 times the requested budget.
Each segment labels ambient versus live motion; these samples are never mixed.
These are observed browser timings, not display scan-out, thermal readings,
smoothness approval or proof that the browser ran on a physical Redmi A5.
The window closes on STOP, Pause, tab hiding and other state transitions;
the next rendered segment starts afresh so background gaps are excluded.
An empty window reports Unknown with null metrics. No transcript, audio,
user-agent string, external telemetry, automatic upload or new device access
is introduced. The existing Founder-initiated Android Proof submission carries
only these aggregates through its existing protected receipt endpoint.

The server rejects malformed/nonfinite timing, inconsistent FPS, unbounded
samples, extra fields and claims of thermal or smoothness approval. Older
receipts without measurements remain readable with performance unmeasured.
Persisted receipts keep anatomy, accurate lip-sync and physical smoothness
approval false, independently of their frame statistics.

Eyes and mouth now inherit the original renderer's head translation while
their blink/mouth deformation stays local. This is coordinated 2D motion,
not depth, reconstructed anatomy or a 3D skeleton. The first-party audio player
waits for actual scheduled playback, suppresses stale phoneme poses, and
reports the real AudioContext clock on completion rather than assigning an
artificially perfect final timestamp. Cue scheduling evidence is separate from
accurate lip-sync: the player, renderer and rig aggregator cannot certify
reviewed mouth geometry. Founder-approved masks/visemes, articulated 3D assets,
physical-device acceptance, independent Guardian/HRM and Founder Final remain
separate evidence requirements. This source change does not deploy the PR.
