"""Canonical first-party OAP Rights & Provenance decision core.

This module is deliberately conservative. It does not infer ownership,
authenticity, copyright status, licensor authority, or legal validity from
self-asserted metadata. It evaluates bounded use requests against explicit
grants and evidence references and fails closed when scope is incomplete.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

DECISIONS = ("ALLOW", "BLOCK", "REVIEW")
RIGHT_TYPES = frozenset({
    "recording", "composition", "image", "video", "text", "performance",
    "broadcast", "stream", "download", "distribution", "derivative",
})
USES = frozenset({
    "private_review", "stream", "broadcast", "download", "distribution",
    "publish", "commercial_use", "derivative", "archive",
})
GENESIS_HASH = "0" * 64
MAX_TEXT = 240


def _uuid(value: object, field: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{field}") from exc


def _text(value: object, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise TypeError(f"invalid_{field}")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > MAX_TEXT:
        raise ValueError(f"invalid_{field}")
    return cleaned


def _sha256(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"invalid_{field}")
    return value


def _instant(value: object, field: str, *, optional: bool = False) -> datetime | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise TypeError(f"invalid_{field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"invalid_{field}")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class UseRequest:
    asset_id: str
    use: str
    territory: str
    channel: str
    requested_at: datetime
    derivative: bool = False

    @classmethod
    def from_mapping(cls, value: object) -> "UseRequest":
        if not isinstance(value, Mapping):
            raise TypeError("invalid_use_request")
        use = value.get("use")
        if use not in USES:
            raise ValueError("invalid_use")
        return cls(
            asset_id=_uuid(value.get("asset_id"), "asset_id"),
            use=str(use),
            territory=_text(value.get("territory"), "territory"),
            channel=_text(value.get("channel"), "channel"),
            requested_at=_instant(value.get("requested_at"), "requested_at"),
            derivative=bool(value.get("derivative", False)),
        )


def canonical_asset(asset: object) -> dict[str, Any]:
    if not isinstance(asset, Mapping):
        raise TypeError("invalid_asset")
    asset_id = _uuid(asset.get("asset_id"), "asset_id")
    owner_identity_id = _uuid(asset.get("owner_identity_id"), "owner_identity_id")
    kind = _text(asset.get("kind"), "kind")
    content_sha256 = _sha256(asset.get("content_sha256"), "content_sha256")
    parent_asset_id = asset.get("parent_asset_id")
    source_reference = _text(asset.get("source_reference"), "source_reference", optional=True)
    return {
        "asset_id": asset_id,
        "owner_identity_id": owner_identity_id,
        "kind": kind,
        "content_sha256": content_sha256,
        "parent_asset_id": (
            _uuid(parent_asset_id, "parent_asset_id")
            if parent_asset_id is not None
            else None
        ),
        "source_reference": source_reference,
    }


def canonical_grant(grant: object) -> dict[str, Any]:
    if not isinstance(grant, Mapping):
        raise TypeError("invalid_grant")
    right_type = grant.get("right_type")
    if right_type not in RIGHT_TYPES:
        raise ValueError("invalid_right_type")
    permitted_uses = grant.get("permitted_uses")
    if not isinstance(permitted_uses, (list, tuple, set, frozenset)):
        raise TypeError("invalid_permitted_uses")
    uses = tuple(sorted({str(v) for v in permitted_uses if v in USES}))
    if not uses:
        raise ValueError("invalid_permitted_uses")
    territories = grant.get("territories")
    if not isinstance(territories, (list, tuple, set, frozenset)):
        raise TypeError("invalid_territories")
    territory_values = tuple(sorted({
        _text(v, "territory") for v in territories
    }))
    if not territory_values:
        raise ValueError("invalid_territories")
    evidence_hashes = grant.get("evidence_hashes")
    if not isinstance(evidence_hashes, (list, tuple, set, frozenset)):
        raise TypeError("invalid_evidence_hashes")
    evidence = tuple(sorted({_sha256(v, "evidence_hash") for v in evidence_hashes}))
    if not evidence:
        raise ValueError("missing_evidence")
    return {
        "grant_id": _uuid(grant.get("grant_id"), "grant_id"),
        "asset_id": _uuid(grant.get("asset_id"), "asset_id"),
        "grantor_reference": _text(grant.get("grantor_reference"), "grantor_reference"),
        "right_type": str(right_type),
        "permitted_uses": uses,
        "territories": territory_values,
        "valid_from": _instant(grant.get("valid_from"), "valid_from", optional=True),
        "valid_until": _instant(grant.get("valid_until"), "valid_until", optional=True),
        "derivatives_allowed": bool(grant.get("derivatives_allowed", False)),
        "commercial_use_allowed": bool(grant.get("commercial_use_allowed", False)),
        "attribution_required": bool(grant.get("attribution_required", False)),
        "evidence_hashes": evidence,
        "authority_verified": bool(grant.get("authority_verified", False)),
        "human_approved": bool(grant.get("human_approved", False)),
        "revoked": bool(grant.get("revoked", False)),
    }


def lineage_chain(asset_id: object, assets: object, *, limit: int = 64) -> dict[str, Any]:
    target = _uuid(asset_id, "asset_id")
    rows = assets if isinstance(assets, Iterable) and not isinstance(assets, (str, bytes, Mapping)) else []
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        try:
            item = canonical_asset(row)
        except (TypeError, ValueError):
            continue
        by_id[item["asset_id"]] = item
    chain: list[str] = []
    seen: set[str] = set()
    current = target
    while current:
        if current in seen:
            return {"lineage_valid": False, "reason": "lineage_cycle", "asset_ids": chain}
        if len(chain) >= limit:
            return {"lineage_valid": False, "reason": "lineage_limit", "asset_ids": chain}
        seen.add(current)
        chain.append(current)
        item = by_id.get(current)
        if item is None:
            return {"lineage_valid": False, "reason": "asset_missing", "asset_ids": chain}
        current = item["parent_asset_id"]
    return {"lineage_valid": True, "reason": None, "asset_ids": chain}


def _grant_matches(grant: dict[str, Any], request: UseRequest) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if grant["asset_id"] != request.asset_id:
        reasons.append("asset_mismatch")
    if request.use not in grant["permitted_uses"]:
        reasons.append("use_not_granted")
    if request.territory not in grant["territories"] and "*" not in grant["territories"]:
        reasons.append("territory_not_granted")
    if grant["revoked"]:
        reasons.append("grant_revoked")
    if grant["valid_from"] is not None and request.requested_at < grant["valid_from"]:
        reasons.append("grant_not_started")
    if grant["valid_until"] is not None and request.requested_at >= grant["valid_until"]:
        reasons.append("grant_expired")
    if request.derivative and not grant["derivatives_allowed"]:
        reasons.append("derivative_not_allowed")
    if request.use == "commercial_use" and not grant["commercial_use_allowed"]:
        reasons.append("commercial_use_not_allowed")
    return (not reasons, reasons)


def evaluate_use(
    *,
    asset: object,
    grants: object,
    request: object,
    lineage_assets: object = (),
) -> dict[str, Any]:
    """Evaluate one exact intended use.

    ALLOW requires a matching explicit grant, evidence hashes, independently
    verified grantor authority, human approval, and valid lineage when the
    asset is derivative. Ambiguity returns REVIEW. Explicit denial conditions
    such as expiry, revocation, missing territory, or missing use return BLOCK.
    """
    canonical = canonical_asset(asset)
    req = UseRequest.from_mapping(request)
    if req.asset_id != canonical["asset_id"]:
        return _decision("BLOCK", req, ["request_asset_mismatch"], [])

    rows = grants if isinstance(grants, Iterable) and not isinstance(grants, (str, bytes, Mapping)) else []
    candidates: list[dict[str, Any]] = []
    mismatch_reasons: set[str] = set()
    malformed = 0
    for row in rows:
        try:
            grant = canonical_grant(row)
        except (TypeError, ValueError):
            malformed += 1
            continue
        if grant["asset_id"] != req.asset_id:
            continue
        matched, reasons = _grant_matches(grant, req)
        if matched:
            candidates.append(grant)
        else:
            mismatch_reasons.update(reasons)

    if not candidates:
        reasons = sorted(mismatch_reasons) or ["no_applicable_grant"]
        if malformed:
            reasons.append("malformed_grant_ignored")
        return _decision("BLOCK", req, reasons, [])

    if canonical["parent_asset_id"] is not None or req.derivative:
        lineage = lineage_chain(req.asset_id, lineage_assets)
        if not lineage["lineage_valid"]:
            return _decision("BLOCK", req, [str(lineage["reason"])], candidates)
    else:
        lineage = {"lineage_valid": True, "reason": None, "asset_ids": [req.asset_id]}

    trusted = [
        g for g in candidates
        if g["authority_verified"] and g["human_approved"] and g["evidence_hashes"]
    ]
    if not trusted:
        reasons = []
        if not any(g["authority_verified"] for g in candidates):
            reasons.append("grantor_authority_unverified")
        if not any(g["human_approved"] for g in candidates):
            reasons.append("human_approval_missing")
        return _decision("REVIEW", req, reasons or ["independent_review_required"], candidates, lineage)

    attribution_required = any(g["attribution_required"] for g in trusted)
    return _decision(
        "ALLOW",
        req,
        ["explicit_scoped_grant"],
        trusted,
        lineage,
        attribution_required=attribution_required,
    )


def _decision(
    decision: str,
    request: UseRequest,
    reasons: list[str],
    grants: list[dict[str, Any]],
    lineage: dict[str, Any] | None = None,
    *,
    attribution_required: bool = False,
) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError("invalid_decision")
    evidence = sorted({
        digest for grant in grants for digest in grant.get("evidence_hashes", ())
    })
    payload = {
        "decision": decision,
        "asset_id": request.asset_id,
        "use": request.use,
        "territory": request.territory,
        "channel": request.channel,
        "requested_at": request.requested_at.isoformat(),
        "derivative": request.derivative,
        "reasons": sorted(set(reasons)),
        "evidence_hashes": evidence,
        "matching_grant_ids": sorted({g["grant_id"] for g in grants}),
        "attribution_required": attribution_required,
        "lineage": lineage or {"lineage_valid": None, "reason": None, "asset_ids": []},
        "rights_verified_by_software": False,
        "legal_advice_provided": False,
        "human_authority_final": True,
    }
    payload["decision_hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload


def status() -> dict[str, Any]:
    return {
        "component": "OAP Rights & Provenance Core",
        "canonical_asset_contract": True,
        "scoped_grant_contract": True,
        "territory_aware": True,
        "time_aware": True,
        "derivative_lineage_check": True,
        "evidence_hash_bound": True,
        "decision_states": DECISIONS,
        "rights_verified_by_software": False,
        "distribution_integration_complete": False,
        "universal_persistence_complete": False,
        "human_authority_final": True,
    }
