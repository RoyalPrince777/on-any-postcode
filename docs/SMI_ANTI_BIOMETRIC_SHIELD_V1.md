# SMI Anti-Biometric Shield · fail-closed first-party gate

**Status:** Source change only; no device deployment, OS permission changes, or
external surveillance protection has been independently verified.

## Scope

- Existing Founder-private recognition observations now reject categories that
  represent faceprints, facial recognition, fingerprint or iris templates,
  voiceprints/speaker identification, gait and behavioural typing biometrics.
- Consensual ordinary voice communication is not automatically a voiceprint.
- A reusable permission gate denies raw biometric processing, outside-provider
  destinations, unconsented tracking, and location profiling.
- The gate must be wired into **every** real ingress and egress route before
  system-wide enforcement can be claimed. Current integration covers the
  Founder-private recognition observation path, **not all OAP services**.
- No new agent identity, dashboard or duplicate My Card is created.

## Exact scope limitations

1. A phone app cannot universally block other organisations' public CCTV,
   roadside cameras, biometric databases, or lawful external surveillance.
2. The Android OS, phone firmware, mobile network and any pre-existing third-party
   apps are outside this Python source policy.
3. No device sensor, camera, microphone or location permission is modified here.
4. Android's on-device biometric auth, where a user explicitly enables it, is
   an operating-system boundary. SMI should accept only its yes/no result;
   password or PIN must remain available.
5. Application source tests do not show that mobile traffic is first-party or
   that all storage and network egress is protected.
6. This code cannot audit external services or stop a physical camera recording.

## Evidence needed before operational claims

- Bagheera: review every route handling face, mic, location, voice and identity.
- Fox: inspect mobile network capture and egress destinations, including crash
  telemetry, remote assets and embedded SDKs.
- Octopus: verify offline behaviour and network-denied recovery.
- Gorilla: authorised adversarial tests for payload bypass and hidden storage.
- Owl: independent device permissions + code evidence, identify gaps.
- Shere Khan: challenge claims and bypass assumptions.
- Guardian/HRM: separately validate the test/receipt chain and its provenance.
- Founder Final: authorise any later rollout after exact-head CI, Redmi A5 and
  release readiness evidence exist.

`evidence_gate()` returns UNKNOWN by default and never claims production Green.
Even a full list of caller-supplied "true" checks yields REVIEW_REQUIRED; real
independent attestation is outside this policy function.

**Ports:** keep private SMI on 5000 and OAP public on 5052; this change does not
add routes, adjust auth, publish data or alter network binding.

**Law:** Research has no ceiling. Deployment has boundaries.


## Existing first-party camera / Bluetooth / microphone / pictures

Reviewed sources on main:
- `mission_control/static/smi_interaction_layer.js`: SMI Vision still capture,
  Face Up camera/mic and explicit picture-to-Vision staging; retain existing
  STOP and browser permission controls.
- `mission_control/silicon_architecture.py`: Bluetooth, local network and
  sensor fabrics are declared as **architecture**, not verified Bluetooth
  Android runtime or transfer.
- `oap/smi/providers.py`: existing external-provider privacy egress block
  now includes explicit media / nearby-device / motion tags. This is an
  actual provider-router boundary, **not** a global network firewall.

`sensor_flow_decision()` adds a reusable denial policy for consentless
camera/pictures/mic/Bluetooth/motion, external destinations, concealed
foreground capture or scan, and unauthorised first-party sharing.
It is *not yet connected* to the Android Bluetooth stack or all SMI
camera/upload/voice routes. Consensual media must remain usable;
a picture with a face is not automatically a biometric *template*.

Remaining tests: the exact head, Android 15 Redmi A5 permissions, real Bluetooth
pairing/transfer, sensitive EXIF removal on authorised share, OS mic/camera
indicators, foreground/background transitions, real first-party egress, and
Guardian/HRM readback. Preserve Founder Final and deployment lock.
