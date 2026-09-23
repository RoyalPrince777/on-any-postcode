"""Isolated first-party Raffles governance kernel. No public entry or payment execution."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any

class State(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved_for_review"
    OPEN = "open"
    STOPPED = "stopped"

class Decision(str, Enum):
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    APPROVE_FOR_REVIEW = "APPROVE_FOR_REVIEW"

REQUIRED = ("sponsor_authority", "prize_authority", "fulfilment",
            "promotion_terms", "jurisdiction_review", "privacy_review",
            "founder_approval")
FORBIDDEN_EXECUTION = frozenset({"open_entries", "take_payment", "select_winner",
                                 "send_marketing", "deliver_prize", "publish"})

@dataclass
class RafflesControl:
    campaign_id: str
    state: State = State.DRAFT
    evidence: dict[str, str] = field(default_factory=dict)
    receipts: list[dict[str, Any]] = field(default_factory=list)
    stopped: bool = False
    _last_hash: str = field(default="0" * 64, repr=False)

    def _receipt(self, action: str, actor: str, outcome: str) -> dict[str, Any]:
        payload = {"campaign_id": self.campaign_id, "sequence": len(self.receipts) + 1,
                   "action": action, "actor": actor, "outcome": outcome,
                   "previous_hash": self._last_hash}
        digest = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        payload["hash"] = digest
        self._last_hash = digest
        self.receipts.append(payload)
        return payload

    def control(self, action: str, actor: str, *, proof: dict[str, str] | None = None) -> dict[str, Any]:
        if not self.campaign_id or not actor:
            raise ValueError("Campaign and actor required")
        if action == "STOP":
            self.stopped = True
            self.state = State.STOPPED
            return self._receipt(action, actor, "STOPPED")
        if self.stopped:
            if action != "RECOVER":
                return self._receipt(action, actor, "BLOCKED_STOP")
            if actor != "founder":
                return self._receipt(action, actor, "BLOCKED_FOUNDER_REQUIRED")
            self.stopped = False
            self.state = State.REVIEW
            return self._receipt(action, actor, "RECOVERED_TO_REVIEW")
        if action in FORBIDDEN_EXECUTION:
            return self._receipt(action, actor, "BLOCKED_RELEASE_SCOPE")
        if action == "ADD_EVIDENCE":
            if not proof or any(k not in REQUIRED or not isinstance(v, str) or not v.strip()
                                for k, v in proof.items()):
                return self._receipt(action, actor, "BLOCKED_INVALID_PROOF")
            self.evidence.update(proof)
            self.state = State.REVIEW
            return self._receipt(action, actor, "RECORDED_UNVERIFIED_EVIDENCE")
        if action == "REVIEW":
            missing = [k for k in REQUIRED if not self.evidence.get(k)]
            return self._receipt(action, actor, "REQUEST_EVIDENCE:" + ",".join(missing)
                                 if missing else "ESCALATE_INDEPENDENT_REVIEW")
        if action == "APPROVE_FOR_REVIEW":
            if actor != "founder" or any(not self.evidence.get(k) for k in REQUIRED):
                return self._receipt(action, actor, "BLOCKED_MISSING_EVIDENCE_OR_FOUNDER")
            self.state = State.APPROVED
            return self._receipt(action, actor, "APPROVED_FOR_REVIEW_NOT_RELEASE")
        return self._receipt(action, actor, "BLOCKED_UNKNOWN_ACTION")

    def verify_receipts(self) -> bool:
        previous = "0" * 64
        for i, receipt in enumerate(self.receipts, 1):
            item = {k: v for k, v in receipt.items() if k != "hash"}
            if item["sequence"] != i or item["previous_hash"] != previous:
                return False
            digest = sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
            if digest != receipt["hash"]:
                return False
            previous = digest
        return True
