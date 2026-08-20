"""Signed, expiring Human Authority approval receipts."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta
from uuid import uuid4

from oap.contracts import (
    ActionPlan,
    ApprovalDecision,
    ApprovalReceipt,
    IdentityRecord,
    action_plan_digest,
    utc_now,
)
from oap.identity import IdentityEngine, IdentityValidationError


class HumanApprovalAuthority:
    """Issue and verify receipts only for active level-zero Human Authority."""

    APPROVAL_PERMISSION = "APPROVE_RECOMMENDATION"

    def __init__(self, identity: IdentityEngine, signing_key: bytes) -> None:
        if len(signing_key) < 32:
            raise ValueError("Approval signing key must be at least 32 bytes")
        self.identity = identity
        self._signing_key = bytes(signing_key)

    def issue(
        self,
        *,
        request_id: str,
        identity_id: str,
        decision: ApprovalDecision,
        plan: ActionPlan,
        ttl_seconds: int = 900,
    ) -> ApprovalReceipt:
        human = self._validate_human_authority(identity_id)
        if plan.request_id != request_id:
            raise ValueError("Approval plan does not match the request")
        if not plan.requires_human_approval:
            raise ValueError("Approval plan must preserve the Human Authority gate")
        ttl = min(max(ttl_seconds, 30), 3600)
        issued_at = utc_now()
        receipt = ApprovalReceipt(
            receipt_id=str(uuid4()),
            request_id=request_id,
            identity_id=human.identity_id,
            authority_level=human.authority_level,
            decision=decision,
            issued_at=issued_at,
            expires_at=issued_at + timedelta(seconds=ttl),
            nonce=secrets.token_urlsafe(24),
            action_digest=action_plan_digest(plan),
            signature="",
        )
        return ApprovalReceipt(
            receipt_id=receipt.receipt_id,
            request_id=receipt.request_id,
            identity_id=receipt.identity_id,
            authority_level=receipt.authority_level,
            decision=receipt.decision,
            issued_at=receipt.issued_at,
            expires_at=receipt.expires_at,
            nonce=receipt.nonce,
            action_digest=receipt.action_digest,
            signature=self._sign(receipt),
        )

    def verify(
        self,
        receipt: ApprovalReceipt,
        request_id: str,
        *,
        plan: ActionPlan | None = None,
        require_approved: bool = True,
    ) -> bool:
        try:
            human = self._validate_human_authority(receipt.identity_id)
        except IdentityValidationError:
            return False
        if human.authority_level != receipt.authority_level:
            return False
        if receipt.request_id != request_id or receipt.expires_at <= utc_now():
            return False
        if require_approved and receipt.decision != ApprovalDecision.APPROVED:
            return False
        if plan is not None:
            try:
                expected_action = action_plan_digest(plan)
            except (TypeError, ValueError):
                return False
            if not hmac.compare_digest(expected_action, receipt.action_digest):
                return False
        expected = self._sign(receipt)
        return hmac.compare_digest(expected, receipt.signature)

    def _validate_human_authority(self, identity_id: str) -> IdentityRecord:
        human = self.identity.validate(identity_id)
        if human.identity_type != "human_authority" or human.authority_level != 0:
            raise IdentityValidationError("Only Human Authority may approve")
        if self.APPROVAL_PERMISSION not in human.permissions:
            raise IdentityValidationError("Human Authority approval permission missing")
        return human

    def _sign(self, receipt: ApprovalReceipt) -> str:
        canonical = "|".join(
            (
                receipt.receipt_id,
                receipt.request_id,
                receipt.identity_id,
                str(receipt.authority_level),
                receipt.decision.value,
                receipt.issued_at.isoformat(),
                receipt.expires_at.isoformat(),
                receipt.nonce,
                receipt.action_digest,
            )
        )
        return hmac.new(
            self._signing_key,
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def status(self) -> dict[str, object]:
        return {
            "component": "Human Approval",
            "ready": True,
            "receipt_signing": "HMAC-SHA256",
            "authority_level": 0,
        }
