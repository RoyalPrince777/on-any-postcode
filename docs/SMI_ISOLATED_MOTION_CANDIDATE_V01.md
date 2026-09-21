# SMI isolated motion candidate v0.1

This candidate produces bounded transform metadata for listening, thinking,
speaking and breathing only after exact-source lineage, mask registration,
Human layer review and private-isolation evidence are all supplied. It is not
loaded by the live SMI page, cannot render pixels, cannot access layer files,
and has no DOM, audio capture, storage, network or telemetry capability.

Speaking mouth movement requires a played-audio clock within 80 ms. Typed text,
predicted timings or stale audio metadata cannot open the mouth. Reduced-motion
mode emits no frames. STOP immediately ends output, increments the epoch and
rejects late callbacks until a separate explicit Human reset.

This is Aegis evidence, not production approval. Visual motion review,
occlusion, real played-audio synchronisation, physical Android testing,
accessibility and Human Authority final remain required.
