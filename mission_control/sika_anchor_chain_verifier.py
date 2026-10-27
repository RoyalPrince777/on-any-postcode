"""Read-only verification of OAP's existing SIKA accounting integrity anchors.

This module neither posts journals nor creates balances, blocks, tokens, or payments.
An in-memory chain alone is not a deployed permissioned blockchain network.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from . import oap_blockchain_accounting_anchor as anchors

ZERO_HASH = "0" * 64


@dataclass(frozen=True)
class ChainVerification:
    valid: bool
    checked: int
    failure_index: int | None
    reason: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "checked": self.checked,
            "failure_index": self.failure_index,
            "reason": self.reason,
            "money_movement": False,
            "consensus_proven": False,
        }


def verify_chain(
    records: Sequence[anchors.AccountingAnchor],
    *,
    expected_genesis: str = ZERO_HASH,
    expected_tip: str | None = None,
) -> ChainVerification:
    """Verify record hashes, explicit order, linkage and optional trusted tip.

    The caller must obtain any trusted tip independently; an attacker able to
    replace the entire sequence can otherwise replace an internally valid chain.
    """
    if not records:
        return ChainVerification(False, 0, None, "empty_chain")
    if not isinstance(expected_genesis, str) or len(expected_genesis) != 64 or any(
        char not in "0123456789abcdef" for char in expected_genesis
    ):
        return ChainVerification(False, 0, None, "invalid_genesis")
    previous = expected_genesis
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, anchors.AccountingAnchor):
            return ChainVerification(False, index, index, "invalid_record_type")
        if record.anchor_id in seen:
            return ChainVerification(False, index, index, "duplicate_anchor_id")
        seen.add(record.anchor_id)
        if record.previous_hash != previous:
            return ChainVerification(False, index, index, "chain_link_mismatch")
        try:
            valid = anchors.verify(record)
        except (anchors.AnchorError, TypeError, ValueError):
            valid = False
        if not valid:
            return ChainVerification(False, index, index, "anchor_hash_mismatch")
        previous = record.current_hash
    if expected_tip is not None and previous != expected_tip:
        return ChainVerification(False, len(records), len(records) - 1, "trusted_tip_mismatch")
    return ChainVerification(True, len(records), None, None)


def status() -> dict[str, object]:
    return {
        "system": "SIKA Anchor Chain Verifier",
        "source_of_truth": "sika_postgresql_journal",
        "read_only": True,
        "requires_external_trusted_checkpoint_for_replacement_detection": True,
        "deployed_validator_network_proven": False,
        "consensus_proven": False,
        "payment_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
