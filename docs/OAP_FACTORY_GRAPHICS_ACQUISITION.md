# Factory Studio graphics capability acquisition — draft

One canonical Studio, existing Founder provider catalogue and preflight. No new renderer, queue, provider payment, upload or deployment. Source links are discovery, not installed dependencies. No source or weights copied by this change.

## First-party acquisition order
1. Babylon.js and local glTF Transform/meshoptimizer: keep existing TDA engine; review pinned revisions, licences and notices, validate output and local decoders.
2. Blender as isolated worker for mesh cleanup, UVs, rigging and PBR texture baking; review GPL integration/distribution.
3. TripoSR and TRELLIS: approved GPU worker, pinned code/weights, dependency and licence review; record asset origin, output hash, duration, worker identity and errors.
4. Audio2Face or Rhubarb: approved owned voice and rig, separate SDK/model terms, map output to morph targets. No biometric identification or external upload.
5. Codex CLI: open agent harness, separate inference backend and network policy. Claude, Meshy, Tripo API and Substance: optional licensed tools; no automatic spending or egress. Unreal: reference only.

## Handoff
Existing Studio -> existing Organiser/worker registry -> approved asset store -> GLB + manifest -> existing TDA Babylon.js loader (port 5052). Do not start a parallel engine. No implementation of this handoff is claimed by this catalogue patch.

Redmi A5 acceptance target (not measured): stable 30 FPS gameplay in Mitcham, lower resolution/LOD/texture sizes on thermal or frame-budget pressure; optional 60 FPS only where measured sustainable. Offline load after assets are installed, no missing decoder or external fetch. Record exact device, browser, commit, asset hash, p50/p95 frame time, crash and memory/thermal observations. Verify visual quality, gameplay controls and rollback. Independent Guardian/HRM and Founder Final required. No Green for code, catalogue or CI alone.

## Local asset inspection implementation
`studio_local_media.inspect_owned_glb` is a bounded read-only helper for authenticated owner-scoped callers. Checks container layout, strict self-contained URI policy, buffer length and SHA-256; not full glTF validation, rendering, dispatch, optimization or native worker evidence. No route or queue added. Tests cover malformed, external and traversal inputs. Runtime wiring requires existing authenticated worker and asset ownership proof.

## Native optimization source acquired
MIT meshoptimizer v1.0 vertex cache/fetch subset is vendored in `third_party/meshoptimizer` at upstream commit `73583c335e541c139821d0de2bf5f12960a04941`. Unmodified upstream files and full MIT notice retained, with blob provenance in UPSTREAM.json. Native C++ compile/run acceptance checks triangle preservation and vertex remapping. This is source acquisition, not full meshoptimizer, GLB rewrite, GPU performance, Studio dispatch or TDA runtime proof. No new permission or executor. Build only in the existing authorized engineering environment; do not promote on CI alone.

## glTF library integration candidate
The local byte-only Node helper in `mission_control/studio_geometry` uses exact direct versions of glTF Transform core 4.2.1 (MIT, source revision e3b4db4c61a9b84162b8ab41ce5bd93ea343ad54) and Khronos glTF Validator 2.0.0-dev.3.10 (Apache-2.0, source revision bcd52cc4ba5f333b2999a58f67cc05ddf28b4fb1). property-graph 3.0.0 is explicitly pinned. The existing CI installs dependencies with lifecycle scripts disabled and runs actual in-memory triangle round-trip and rejection tests. Dependency artefact hashes and lockfile, complete notices and supply-chain audit are still required before runtime installation. This is a dependency integration candidate, not vendored upstream source. No live worker integration or optimization claim. Strict initial profile rejects extensions and all URI-bearing assets, including data URIs. Schema validation is not a renderer or performance proof. Existing private worker must authenticate asset ownership, isolate the process and enforce time/memory limits before runtime use. No public route or authority expansion.
