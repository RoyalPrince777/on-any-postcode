"""Durable SIKA Android acceptance evidence on canonical OAP stores.

Records authenticated-owner physical-device acceptance evidence in the existing
owner-scoped SIKA workspace plus audit_events. It never fabricates device proof
and never upgrades native APK/eSIM status.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from . import postgres_db, sika_android_acceptance


class SikaAndroidEvidenceUnavailable(RuntimeError):
    pass


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_owner_uuid_required") from exc


def _digest(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _evidence_from_body(body: dict[str, object]) -> sika_android_acceptance.AndroidAcceptanceEvidence:
    return sika_android_acceptance.AndroidAcceptanceEvidence(
        device_label=str(body.get("device_label") or "").strip()[:120] or None,
        install_completed=body.get("install_completed") is True,
        launched_from_home_screen=body.get("launched_from_home_screen") is True,
        update_observed=body.get("update_observed") is True,
        recovery_after_offline_or_restart=body.get("recovery_after_offline_or_restart") is True,
        private_routes_not_cached=body.get("private_routes_not_cached") is True,
        service_worker_active=body.get("service_worker_active") is True,
        manifest_identity_matches=body.get("manifest_identity_matches") is True,
        user_confirmed=body.get("user_confirmed") is True,
        evidence_ref=str(body.get("evidence_ref") or "").strip()[:240] or None,
    )


def record_authenticated_owner(owner_id: object, body: dict[str, object]) -> dict[str, object]:
    owner = _owner(owner_id)
    evidence = _evidence_from_body(body)
    result = sika_android_acceptance.evaluate(evidence)
    receipt_id = str(uuid4())
    payload = {
        "receipt_id": receipt_id,
        "owner_id": owner,
        "device_label": evidence.device_label,
        "checks": result["checks"],
        "real_android_pwa_acceptance": result["real_android_pwa_acceptance"],
        "public_install_release_gate": result["public_install_release_gate"],
        "native_android_package_ready": False,
        "signed_native_sika_apk": False,
        "native_update_recovery_acceptance": False,
        "evidence_ref": evidence.evidence_ref,
        "founder_auth_touched": False,
    }
    item = {**payload, "digest": _digest(payload)}
    body_json = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)

    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082513,))
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'sika',%s,%s,'active')
                   RETURNING record_id""",
                (owner, f"SIKA-ANDROID-EVIDENCE:{receipt_id}", body_json),
            ).fetchone()
            record_id = str(row[0])

            connection.execute("SELECT pg_advisory_xact_lock(%s)", (25082509,))
            prior = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = str(prior[0]) if prior else "GENESIS"
            metadata = {
                "workspace_id": "sika",
                "receipt_id": receipt_id,
                "record_id": record_id,
                "owner_id": owner,
                "accepted": result["real_android_pwa_acceptance"],
                "evidence_digest": item["digest"],
                "founder_auth_touched": False,
            }
            canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
            curr_hash = sha256((prev_hash + canonical).encode()).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'AUTHENTICATED_USER',NULL,
                       'SIKA_ANDROID_ACCEPTANCE_EVIDENCE',%s,
                       'authenticated_owner_physical_android_evidence',%s,%s::jsonb
                   )""",
                (
                    prev_hash,
                    curr_hash,
                    owner,
                    f"sika_android:{receipt_id}",
                    receipt_id,
                    canonical,
                ),
            )
            connection.commit()
    except Exception as exc:
        raise SikaAndroidEvidenceUnavailable("android_evidence_write_failed") from exc

    return {
        **result,
        "receipt_id": receipt_id,
        "record_id": record_id,
        "audit_recorded": True,
        "durable": True,
        "founder_auth_touched": False,
    }


def latest(owner_id: object) -> dict[str, object]:
    owner = _owner(owner_id)
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT record_id,body,created_at
                   FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='sika'
                     AND status='active' AND title LIKE 'SIKA-ANDROID-EVIDENCE:%%'
                   ORDER BY created_at DESC, record_id DESC
                   LIMIT 1""",
                (owner,),
            ).fetchone()
    except Exception as exc:
        raise SikaAndroidEvidenceUnavailable("android_evidence_read_failed") from exc

    if not row:
        return {
            "owner_id": owner,
            "evidence_present": False,
            "real_android_pwa_acceptance": False,
            "public_install_release_gate": False,
            "durable": True,
            "founder_auth_touched": False,
        }

    try:
        item = json.loads(str(row[1]))
    except ValueError as exc:
        raise SikaAndroidEvidenceUnavailable("android_evidence_unreadable") from exc
    if (
        not isinstance(item, dict)
        or item.get("owner_id") != owner
        or item.get("digest") != _digest({k: v for k, v in item.items() if k != "digest"})
    ):
        raise SikaAndroidEvidenceUnavailable("android_evidence_tampered")

    return {
        **item,
        "record_id": str(row[0]),
        "evidence_present": True,
        "durable": True,
        "founder_auth_touched": False,
    }


def readiness() -> dict[str, object]:
    return {
        "authenticated_evidence_route_software_ready": True,
        "canonical_store_reused": True,
        "audit_chain_reused": True,
        "real_device_evidence_required": True,
        "self_certification_allowed": False,
        "native_apk_claim_allowed": False,
        "esim_claim_allowed": False,
        "founder_auth_touched": False,
        "physical_android_acceptance": False,
        "reason": "real_authenticated_device_evidence_required",
    }
