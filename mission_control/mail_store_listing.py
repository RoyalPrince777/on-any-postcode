"""OAP Mail first-party Store listing preparation, not a published app or installer.

This standalone contract is intentionally not registered as an existing App Store
route or package: distribution needs an independently evidenced installer and
release approval. Never infer readiness from CI passing alone.
"""
from __future__ import annotations

APP_ID = "oap.mail"
REQUIRED_RELEASE_EVIDENCE = frozenset({
    "mail_delivery_and_receipt_verified",
    "private_mailbox_acceptance_verified",
    "encryption_and_key_handling_reviewed",
    "independent_backup_restore_readback_verified",
    "package_signature_and_provenance_verified",
    "store_install_update_rollback_verified",
    "founder_release_approval",
})


def listing(evidence: object = None) -> dict[str, object]:
    """Return honest draft listing; caller claims cannot bypass release gates."""
    supplied = evidence if isinstance(evidence, dict) else {}
    gates = {key: supplied.get(key) is True for key in sorted(REQUIRED_RELEASE_EVIDENCE)}
    ready = all(gates.values())
    return {
        "app_id": APP_ID,
        "name": "OAP Mail",
        "publisher": "ON ANY POSTCODE LTD",
        "distribution": "OAP App Store",
        "first_party": True,
        "tagline": "Your Mail. Your World. Your Control.",
        "description": "Private OAP Mail for OAP members. Release pending verification.",
        "public_release_state": "release_pending",
        "install_enabled": False,
        "publish_executed": False,
        "package_available": False,
        "mail_delivery_claimed": False,
        "end_to_end_encryption_claimed": False,
        "security_certification_claimed": False,
        "gates": gates,
        "all_evidence_supplied": ready,
        "human_authority_final": True,
    }
