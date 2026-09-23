"""Raffles-specific review controls; canonical audit and authority are injected.

Not a Matrix, authority, audit, entry, payment, or delivery implementation.
Callers must pass adapters to the existing OAP services. No live routes are wired.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class State(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved_for_review"
    STOPPED = "stopped"

REQUIRED = ("sponsor_authority", "prize_authority", "fulfilment",
            "promotion_terms", "jurisdiction_review", "privacy_review",
            "founder_approval")
FORBIDDEN_EXECUTION = frozenset({"open_entries", "take_payment", "select_winner",
                                 "send_marketing", "deliver_prize", "publish"})

# Adapter must persist through oap.audit.chain.append_event or the existing
# durable SMI receipt service; never replace it with a second hash chain.
AuditWriter = Callable[[str, str, str, str], Any]
# Adapter must check mission_control.authority.require_human_authority against
# an authenticated request identity and the canonical authority DB.
AuthorityChecker = Callable[[str], bool]

@dataclass
class RafflesControl:
    campaign_id: str
    audit_writer: AuditWriter | None = field(default=None, repr=False)
    authority_checker: AuthorityChecker | None = field(default=None, repr=False)
    state: State = State.DRAFT
    evidence: dict[str, str] = field(default_factory=dict)
    stopped: bool = False

    def _record(self, action: str, actor: str, outcome: str) -> dict[str, str]:
        if self.audit_writer is None:
            raise RuntimeError("canonical_audit_required")
        # A failed canonical write must not be represented as a successful action.
        receipt = self.audit_writer(self.campaign_id, action, actor, outcome)
        if receipt is None or receipt is False:
            raise RuntimeError("canonical_audit_unconfirmed")
        return {"campaign_id": self.campaign_id, "action": action, "outcome": outcome}

    def _is_authority(self, actor: str) -> bool:
        if self.authority_checker is None:
            return False
        try:
            return self.authority_checker(actor) is True
        except Exception:
            return False

    def control(self, action: str, actor: str, *,
                proof: Mapping[str, str] | None = None) -> dict[str, str]:
        if not self.campaign_id or not actor:
            raise ValueError("Campaign and authenticated actor required")
        if action == "STOP":
            result = self._record(action, actor, "STOPPED")
            self.stopped, self.state = True, State.STOPPED
            return result
        if self.stopped:
            if action != "RECOVER":
                return self._record(action, actor, "BLOCKED_STOP")
            if not self._is_authority(actor):
                return self._record(action, actor, "BLOCKED_FOUNDER_REQUIRED")
            result = self._record(action, actor, "RECOVERED_TO_REVIEW")
            self.stopped, self.state = False, State.REVIEW
            return result
        if action in FORBIDDEN_EXECUTION:
            return self._record(action, actor, "BLOCKED_RELEASE_SCOPE")
        if action == "ADD_EVIDENCE":
            if not proof or any(k not in REQUIRED or not isinstance(v, str) or not v.strip()
                                for k, v in proof.items()):
                return self._record(action, actor, "BLOCKED_INVALID_PROOF")
            result = self._record(action, actor, "RECORDED_UNVERIFIED_EVIDENCE")
            self.evidence.update(proof)
            self.state = State.REVIEW
            return result
        if action == "REVIEW":
            missing = [k for k in REQUIRED if not self.evidence.get(k)]
            return self._record(action, actor, "REQUEST_EVIDENCE:" + ",".join(missing)
                                if missing else "ESCALATE_TO_CANONICAL_MATRIX_REVIEW")
        if action == "APPROVE_FOR_REVIEW":
            if not self._is_authority(actor) or any(
                not self.evidence.get(k) for k in REQUIRED
            ):
                return self._record(action, actor, "BLOCKED_MISSING_EVIDENCE_OR_FOUNDER")
            result = self._record(action, actor, "APPROVED_FOR_REVIEW_NOT_RELEASE")
            self.state = State.APPROVED
            return result
        return self._record(action, actor, "BLOCKED_UNKNOWN_ACTION")
