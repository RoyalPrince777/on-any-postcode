"""Versioned local world state; reads are free, writes require approval."""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from oap.audit import append_event
from oap.contracts import ActionPlan, BuilderContext, utc_now

_STATE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class WorldEngine:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def snapshot(self) -> dict[str, Any]:
        rows = self.connection.execute(
            "SELECT state_key, value_json FROM smi_world_state "
            "ORDER BY state_key"
        ).fetchall()
        return {str(row["state_key"]): json.loads(row["value_json"]) for row in rows}

    @staticmethod
    def plan_update(request_id: str, key: str, value: Any) -> ActionPlan:
        """Create the exact world-state plan Human Authority must review."""

        if not _STATE_KEY.fullmatch(key):
            raise ValueError("World-state key is invalid")
        value_json = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        if len(value_json.encode("utf-8")) > 100_000:
            raise ValueError("World-state value exceeds the safe limit")
        return ActionPlan(
            request_id=request_id,
            action_type="update_world_state",
            payload={"key": key, "value": value},
            requires_human_approval=True,
        )

    def apply_builder_update(
        self,
        payload: dict[str, Any],
        context: BuilderContext,
    ) -> None:
        """Apply an update only as a registered Builder handler."""

        if set(payload) != {"key", "value"}:
            raise ValueError("World-state Builder payload is invalid")
        key = payload["key"]
        if not isinstance(key, str):
            raise TypeError("World-state key must be text")
        value = payload["value"]
        self.plan_update(context.request_id, key, value)
        started_transaction = not self.connection.in_transaction
        if started_transaction:
            self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute(
                "SELECT version FROM smi_world_state WHERE state_key = ?",
                (key,),
            ).fetchone()
            version = int(row["version"]) + 1 if row else 1
            self.connection.execute(
                "INSERT INTO smi_world_state ("
                "state_key, value_json, version, approval_receipt_id, updated_at"
                ") VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(state_key) DO UPDATE SET "
                "value_json = excluded.value_json, version = excluded.version, "
                "approval_receipt_id = excluded.approval_receipt_id, "
                "updated_at = excluded.updated_at",
                (
                    key,
                    json.dumps(
                        value,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        allow_nan=False,
                    ),
                    version,
                    context.receipt_id,
                    utc_now().isoformat(),
                ),
            )
            append_event(
                self.connection,
                actor=context.identity_id,
                actor_type="human_authority",
                authority_level=context.authority_level,
                action="WORLD_STATE_UPDATED",
                target=key,
                reason="Verified Human-approved world-state update",
                metadata={
                    "version": version,
                    "approval_receipt_id": context.receipt_id,
                },
                correlation_id=context.request_id,
            )
            if started_transaction:
                self.connection.execute("COMMIT")
        except Exception:
            if started_transaction:
                self.connection.execute("ROLLBACK")
            raise

    def status(self) -> dict[str, object]:
        try:
            count = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM smi_world_state"
                ).fetchone()[0]
            )
        except sqlite3.Error:
            return {"component": "World Engine", "ready": False, "records": 0}
        return {"component": "World Engine", "ready": True, "records": count}
