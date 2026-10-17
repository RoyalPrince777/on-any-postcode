"""Read-only first-party node health evidence; no execution authority."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class NodeRecord:
    node_id: str
    kind: str
    public_key_fingerprint: str


class NodeRegistry:
    """Explicitly registered nodes; untrusted reports never create nodes."""

    def __init__(self, nodes: tuple[NodeRecord, ...] = ()) -> None:
        self._nodes = {}
        for node in nodes:
            if not node.node_id or not node.public_key_fingerprint:
                raise ValueError("node_identity_required")
            if node.node_id in self._nodes:
                raise ValueError("duplicate_node_id")
            self._nodes[node.node_id] = node

    def inspect(self, *, node_id: str, observed_at: datetime | None = None) -> dict:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError("unregistered_node")
        if observed_at is None or observed_at.tzinfo is None:
            return {"node_id": node_id, "status": "unverified"}
        age = (datetime.now(timezone.utc) - observed_at.astimezone(timezone.utc)).total_seconds()
        if age < 0 or age > 300:
            return {"node_id": node_id, "status": "stale"}
        return {"node_id": node_id, "status": "evidence_pending"}
