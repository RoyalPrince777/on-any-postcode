"""Prepare bounded plans; actual execution belongs to Living Kernel and Builder."""

from __future__ import annotations

import json
import re
from typing import Any

from oap.contracts import ActionPlan, OutputState, Recommendation

_ACTION_TYPE = re.compile(r"^[a-z][a-z0-9_.:-]{0,63}$")
_MAX_PAYLOAD_BYTES = 100_000


class ActionEngine:
    def prepare(
        self,
        recommendation: Recommendation,
        *,
        action_type: str,
        payload: dict[str, Any] | None = None,
    ) -> ActionPlan:
        if recommendation.output_state not in {
            OutputState.RECOMMENDATION_READY,
            OutputState.REVIEW_REQUIRED,
        }:
            raise PermissionError("Blocked or log-only output cannot form an action plan")
        normalized_action = action_type.strip()
        if not _ACTION_TYPE.fullmatch(normalized_action):
            raise ValueError("Action type is invalid")
        safe_payload = dict(payload or {})
        try:
            serialized = json.dumps(
                safe_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (RecursionError, TypeError, ValueError) as exc:
            raise ValueError("Action payload must be valid JSON") from exc
        if len(serialized.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
            raise ValueError("Action payload exceeds the safe limit")
        return ActionPlan(
            request_id=recommendation.request_id,
            action_type=normalized_action,
            payload=safe_payload,
            requires_human_approval=True,
        )
