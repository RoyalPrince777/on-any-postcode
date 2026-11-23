"""CI-only, read-only routing-origin readiness receipt.

A missing or unapproved endpoint is UNKNOWN/LOCKED, never live Green.
An approved origin only authorises an *attempt* to measure live routing;
it does not assert capacity, availability, deployment, or production approval.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from scripts import routing_live_green_gate


def readiness() -> dict[str, object]:
    configured = False
    if not routing_live_green_gate.BASE:
        failure_type = "missing_https_origin"
    else:
        try:
            routing_live_green_gate._verified_base()
        except ValueError:
            failure_type = "invalid_or_unapproved_oap_owned_https_origin"
        else:
            configured = True
            failure_type = None

    return {
        "event": "oap_routing_ci_proof_readiness",
        "configured_for_live_probe": configured,
        "live_probe_executed": False,
        "live_geometry_proven": False,
        "bounded_capacity_proven": False,
        "production_routing_ready": False,
        "proof_state": "NOT_RUN" if configured else "UNKNOWN_LOCKED",
        "failure_type": failure_type,
        "dispatch_performed": False,
        "payment_performed": False,
        "tracking_performed": False,
    }


def main() -> None:
    receipt = readiness()
    print(json.dumps(receipt, sort_keys=True), flush=True)
    output = os.environ.get("GITHUB_OUTPUT", "").strip()
    if output:
        with open(output, "a", encoding="utf-8") as file:
            file.write(f"configured={'true' if receipt['configured_for_live_probe'] else 'false'}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write(
                "### OAP routing live proof\n"
                f"- Configuration: **{'approved for probe' if receipt['configured_for_live_probe'] else 'missing or unapproved'}**\n"
                "- Proof: **NOT VERIFIED** until the independent live probe passes.\n"
                "- Dispatch, payment and tracking: **not performed**.\n"
            )
    # Only bounded, nonsensitive status is written. This is not a credential.
    Path("/tmp/oap-routing-proof-readiness.json").write_text(
        json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
