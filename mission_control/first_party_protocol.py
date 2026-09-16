"""OAP first-party-only protocol.

This is the canonical sovereignty boundary for OAP/SMI product architecture.
OAP-owned or OAP-operated runtime paths are the default and required production
path. Third-party runtime dependencies, embeds, trackers, identity authorities,
automatic external distribution and silent provider fallbacks are not accepted as
OAP-owned capability.

Open standards and openly licensed/public datasets may be used as inputs only when
OAP controls the runtime/processing path and provenance/licensing is retained.
Infrastructure currently hosted by a vendor must be described truthfully as hosted
infrastructure, never as OAP-owned infrastructure.
"""
from __future__ import annotations

from typing import Final

PROTOCOL_ID: Final[str] = "oap_first_party_only"
PROTOCOL_NAME: Final[str] = "First Party Only"

LOCKS: Final[dict[str, bool]] = {
    "third_party_runtime_fallback": False,
    "third_party_identity_authority": False,
    "third_party_tracking": False,
    "third_party_advertising": False,
    "third_party_embeds": False,
    "automatic_external_distribution": False,
    "silent_external_provider": False,
    "authority_transfer": False,
}

ALLOWED_INPUTS: Final[tuple[str, ...]] = (
    "open_standards",
    "open_source_software_self_operated_by_oap",
    "open_or_public_data_with_provenance_and_licensing",
)

REQUIRED_TRUTH: Final[tuple[str, ...]] = (
    "distinguish_oap_owned_from_vendor_hosted",
    "distinguish_open_data_from_oap_data",
    "distinguish_configured_capability_from_runtime_proof",
    "fail_closed_when_first_party_path_is_unavailable",
    "human_authority_final",
)


def first_party_status() -> dict[str, object]:
    return {
        "id": PROTOCOL_ID,
        "name": PROTOCOL_NAME,
        "locked": True,
        "default": True,
        "locks": dict(LOCKS),
        "allowed_inputs": ALLOWED_INPUTS,
        "required_truth": REQUIRED_TRUTH,
        "third_party_fallback": False,
        "fail_closed": True,
        "human_authority_final": True,
    }
