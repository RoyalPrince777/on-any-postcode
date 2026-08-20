"""Explicit Builder handlers; no action exists until registered."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from oap.contracts import ActionPlan, BuilderContext

BuilderHandler = Callable[[dict[str, Any], BuilderContext], None]


class BuilderRegistry:
    """Bounded action handlers owned by Builder, not SMI."""

    def __init__(self) -> None:
        self._handlers: dict[str, BuilderHandler] = {}

    def register(self, action_type: str, handler: BuilderHandler) -> None:
        if not action_type or action_type in self._handlers:
            raise ValueError("Builder action type must be unique and non-empty")
        self._handlers[action_type] = handler

    def execute(self, plan: ActionPlan, context: BuilderContext) -> None:
        handler = self._handlers.get(plan.action_type)
        if handler is None:
            raise LookupError("No approved Builder handler is registered")
        if context.request_id != plan.request_id:
            raise PermissionError("Builder context does not match the action plan")
        handler(dict(plan.payload), context)

    def status(self) -> dict[str, object]:
        return {
            "component": "Builder",
            "ready": True,
            "registered_actions": tuple(sorted(self._handlers)),
            "default_actions": 0,
        }
