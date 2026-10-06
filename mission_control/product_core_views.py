"""Authenticated first-party APIs for OAP Tune, Commerce and Post organs."""
from __future__ import annotations

import base64
import binascii
import uuid

from flask import Blueprint, jsonify, make_response, render_template, request

from . import (
    certification,
    commerce_install,
    commerce_provider_receipts,
    distribution_intelligence,
    distribution_runtime,
    entertainment_catalogue,
    live_music_core,
    market_sika_pod_runtime,
    market_supplier_network,
    market_transaction_spine,
    music_acceptance,
    music_assets,
    music_civilization,
    music_evidence,
    music_market_purchase,
    music_recovery,
    open_cinema,
    open_cinema_evidence,
    open_music_intake,
    product_core_services,
    product_cores,
    prodigi_pod_adapter,
    product_store,
    public_store,
    radio_core,
    records_core,
    sika_payment_orchestrator,
    sika_payment_submission_evidence,
    sika_secure_provider_runtime,
    web_security,
)

bp = Blueprint("product_core_organs", __name__)
_store = product_cores.PostgresProductCoreStore()
_music_evidence_store = music_evidence.MusicEvidenceStore()
_music_market_purchase_store = music_market_purchase.MusicMarketPurchaseStore()
_radio_store = radio_core.RadioStore()
_records_store = records_core.RecordsStore()
_live_music_store = live_music_core.LiveMusicStore()
_music_recovery_store = music_recovery.MusicRecoveryStore()
_music_acceptance_store = music_acceptance.MusicAcceptanceStore()
_distribution_runtime_store = distribution_runtime.DistributionRuntimeStore()
_music_asset_store = music_assets.MusicAssetStore()


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _error(code: str, message: str, status_code: int):
    return _no_store(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _identity(*, sync: bool = False) -> str:
    identity_id = web_security.authenticated_identity()
    if sync:
        user = web_security.current_authenticated_user()
        if user is None:
            raise PermissionError("authentication_required")
        public_store.ensure_authenticated_user(
            str(user["id"]),
            email=str(user["email"]),
            display_name=str(user["name"]),
            email_verified=bool(user.get("email_verified")),
        )
    return identity_id


def _require_certified_merchant(identity_id: str) -> str:
    try:
        status = certification.identity_status(identity_id)
    except certification.CertificationUnavailable as exc:
        raise RuntimeError("merchant_certification_unavailable") from exc
    if status.get("merchant") is not True:
        raise PermissionError("certified_merchant_required")
    return identity_id


def _payload() -> dict[str, object]:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


def _write_allowed() -> bool:
    return web_security.csrf_valid(request)


def _handle_write(action):
    if not _write_allowed():
        return _error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    try:
        return _no_store(make_response(jsonify(action()), 201))
    except PermissionError as exc:
        return _error("permission_denied", str(exc), 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_request", str(exc), 400)
    except (public_store.PublicStoreUnavailable, product_store.ProductStoreUnavailable, RuntimeError):
        return _error("organ_unavailable", "The OAP organ store is temporarily unavailable.", 503)
    except Exception:  # noqa: BLE001 - redact storage/provider implementation details.
        return _error("organ_unavailable", "The OAP organ store is temporarily unavailable.", 503)


def _media_projection(identity_id: str) -> dict[str, object]:
    tune = product_core_services.tune_dashboard(identity_id)
    return {
        "organ": "OAP Media",
        "source_organ": tune.get("organ", "OAP Music"),
        "releases": tune.get("releases", []),
        "playlists": tune.get("playlists", []),
        "release_count": len(tune.get("releases", [])),
        "playlist_count": len(tune.get("playlists", [])),
        "entertainment": entertainment_catalogue.project_catalogue(tune),
        "licensed_audio_delivery": False,
        "external_distribution": False,
        "royalty_payout": False,
        "human_authority_final": True,
    }


def _distribution_projection(identity_id: str) -> dict[str, object]:
    tune = product_core_services.tune_dashboard(identity_id)
    contract = distribution_intelligence.status()
    return {
        "organ": "OAP Distribution",
        "contract": contract,
        "releases": tune.get("releases", []),
        "release_count": len(tune.get("releases", [])),
        "entertainment": entertainment_catalogue.project_catalogue(tune),
        "external_execution_enabled": False,
        "external_distribution_state": contract.get("external_distribution_state"),
        "rights_proof_required": True,
        "human_authority_final": True,
    }


def _market_projection(identity_id: str) -> dict[str, object]:
    commerce = product_core_services.commerce_dashboard(identity_id)
    return {
        "organ": "OAP Market",
        "source_organ": commerce.get("organ", "OAP Commerce Core"),
        "storefront": commerce.get("storefront"),
        "products": commerce.get("products", []),
        "orders": commerce.get("orders", []),
        "payment_capture_performed": False,
        "external_fulfilment_performed": False,
        "sika_pod_runtime": market_sika_pod_runtime.status(),
        "human_authority_final": True,
    }


def _distribution_market_media_projection(identity_id: str) -> dict[str, object]:
    tune = product_core_services.tune_dashboard(identity_id)
    commerce = product_core_services.commerce_dashboard(identity_id)
    contract = distribution_intelligence.status()
    return {
        "suite": "OAP Distribution / Market / Media",
        "read_projection_ready": True,
        "entertainment": entertainment_catalogue.project_catalogue(tune),
        "media": {
            "organ": "OAP Media",
            "source_organ": tune.get("organ", "OAP Music"),
            "releases": tune.get("releases", []),
            "playlists": tune.get("playlists", []),
            "licensed_audio_delivery": False,
        },
        "market": {
            "organ": "OAP Market",
            "source_organ": commerce.get("organ", "OAP Commerce Core"),
            "storefront": commerce.get("storefront"),
            "products": commerce.get("products", []),
            "orders": commerce.get("orders", []),
            "payment_capture_performed": False,
            "external_fulfilment_performed": False,
        },
        "distribution": {
            "organ": "OAP Distribution",
            "contract": contract,
            "releases": tune.get("releases", []),
            "external_execution_enabled": False,
            "external_distribution_state": contract.get(
                "external_distribution_state"
            ),
        },
        "human_authority_final": True,
    }


@bp.get("/status")
@web_security.login_required(api=True)
def all_organs_status():
    try:
        return _no_store(
            make_response(jsonify(product_core_services.organ_status(_identity())))
        )
    except (ValueError, RuntimeError):
        return _error("organ_unavailable", "Product organ status is temporarily unavailable.", 503)


@bp.get("/tune")
@web_security.login_required(api=True)
def tune_status():
    try:
        return _no_store(make_response(jsonify(product_core_services.tune_dashboard(_identity()))))
    except (ValueError, RuntimeError):
        return _error("tune_unavailable", "OAP Music is temporarily unavailable.", 503)


@bp.get("/media")
@web_security.login_required(api=True)
def media_status():
    try:
        return _no_store(make_response(jsonify(_media_projection(_identity()))))
    except (ValueError, RuntimeError):
        return _error("media_unavailable", "OAP Media is temporarily unavailable.", 503)


@bp.get("/entertainment")
@web_security.login_required(api=True)
def entertainment_status():
    """Read-only owner-scoped catalogue; no media delivery or public projection."""
    try:
        tune = product_core_services.tune_dashboard(_identity())
        return _no_store(make_response(jsonify(
            entertainment_catalogue.project_catalogue(tune)
        )))
    except (ValueError, RuntimeError):
        return _error("entertainment_unavailable", "OAP Entertainment is temporarily unavailable.", 503)


@bp.post("/tune/catalogue-intelligence/preview")
@web_security.login_required(api=True, founder_only=True)
def tune_catalogue_intelligence_preview():
    """Founder-only OAP Music metadata review; never imports audio or grants rights."""
    if not _write_allowed():
        return _error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
        return _error("invalid_request", "Candidate list required.", 400)
    genres = payload.get("genres")
    if genres is not None and (not isinstance(genres, list)
                               or len(genres) > len(open_music_intake.GENRES)
                               or len({g for g in genres if isinstance(g, str)}) != len(genres)
                               or any(not isinstance(g, str) or g not in open_music_intake.GENRES
                                      for g in genres)):
        return _error("invalid_request", "Invalid genre filter.", 400)
    if payload.get("licence_filter", "all") not in ("all", "preferred"):
        return _error("invalid_request", "Invalid licence filter.", 400)
    if payload.get("vocals", "All") not in ("All", "Vocals", "Instrumental"):
        return _error("invalid_request", "Invalid vocals filter.", 400)
    try:
        _identity()  # The session, never claimant-supplied owner fields.
        return _no_store(make_response(jsonify(
            open_music_intake.private_catalogue_intelligence(
                payload["candidates"], genres=payload.get("genres"),
                licence_filter=payload.get("licence_filter", "all"),
                mood=payload.get("mood", "All moods"),
                vocals=payload.get("vocals", "All"),
            )
        )))
    except (PermissionError, ValueError):
        return _error("permission_denied", "Authenticated Founder required.", 403)


@bp.post("/tune/catalogue-intelligence/review-handoff")
@web_security.login_required(api=True, founder_only=True)
def tune_catalogue_review_handoff():
    """Session-owner-scoped, read-only plan for an existing OAP Music release."""
    if not _write_allowed():
        return _error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("candidate"), dict):
        return _error("invalid_request", "Candidate object required.", 400)
    release_id = payload.get("release_id")
    if not isinstance(release_id, str):
        return _error("invalid_request", "Release ID required.", 400)
    try:
        owner = _identity()
        # Read from the existing canonical, owner-scoped Tune Core projection.
        tune = product_core_services.tune_dashboard(owner)
        plan = open_music_intake.private_music_release_review_plan(
            payload["candidate"], owner, release_id,
        )
        if plan["candidate_id"] is None or plan["submitted_release_id"] is None:
            return _error("invalid_request", "Invalid candidate or release.", 400)
        release = next(
            (row for row in tune["releases"]
             if row["release_id"] == plan["submitted_release_id"]), None
        )
        if release is None:
            return _error("not_found", "Release unavailable for this owner.", 404)
        plan["owner_authenticated"] = True
        plan["owner_bound_to_music_release"] = True
        plan["existing_release"] = {
            "release_id": release["release_id"],
            "title": release["title"],
            "state": release["state"],
            "rights_status": release["rights_status"],
        }
        # Existing release status is not proof of the candidate's rights.
        return _no_store(make_response(jsonify(plan)))
    except (PermissionError, ValueError):
        return _error("permission_denied", "Authenticated Founder required.", 403)
    except Exception:  # noqa: BLE001 - fail closed, redact storage details.
        return _error("organ_unavailable", "OAP Music is temporarily unavailable.", 503)


@bp.get("/tune/releases/<release_id>/evidence")
@web_security.login_required(api=True, founder_only=True)
def tune_release_evidence(release_id: str):
    """Read owner-scoped immutable Music evidence and its private gate."""
    try:
        owner = _identity()
        receipts = _music_evidence_store.read_receipts(
            owner_identity_id=owner, release_id=release_id
        )
        return _no_store(make_response(jsonify({
            "release_id": release_id,
            "receipts": receipts,
            "chain": music_evidence.verify_receipt_chain(receipts),
            "distribution_gate": music_evidence.private_distribution_gate(
                receipts,
                recovery_readback_proven=any(
                    row.get("evidence_kind") == "recovery_readback" for row in receipts
                ),
            ),
            "external_distribution_enabled": False,
            "playback_enabled": False,
            "public_catalogue_enabled": False,
            "human_authority_final": True,
        })))
    except PermissionError:
        return _error("permission_denied", "Release unavailable for this owner.", 403)
    except (ValueError, RuntimeError):
        return _error("music_evidence_unavailable", "Music evidence is temporarily unavailable.", 503)


@bp.post("/tune/releases/<release_id>/evidence")
@web_security.login_required(api=True, founder_only=True)
def append_tune_release_evidence(release_id: str):
    """Persist actual evidence bytes; never treat their presence as rights verification."""
    def action():
        payload = _payload()
        encoded = payload.get("evidence_base64")
        if not isinstance(encoded, str) or len(encoded) > 11_500_000:
            raise ValueError("invalid_evidence_base64")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("invalid_evidence_base64") from exc
        receipt = _music_evidence_store.append_receipt(
            owner_identity_id=_identity(sync=True),
            release_id=release_id,
            evidence_kind=payload.get("evidence_kind"),
            evidence_bytes=raw,
            source_reference=payload.get("source_reference"),
            authority_reference=payload.get("authority_reference"),
            territory=payload.get("territory"),
        )
        return {
            "receipt": receipt,
            "rights_verified_by_software": False,
            "external_distribution_enabled": False,
            "playback_enabled": False,
            "public_catalogue_enabled": False,
            "human_authority_final": True,
        }

    return _handle_write(action)


@bp.post("/tune/releases/<release_id>/civilization")
@web_security.login_required(api=True, founder_only=True)
def add_tune_civilization_link(release_id: str):
    """Attach one evidence-backed cultural/geographic fact to an owned release."""
    def action():
        payload = _payload()
        return _music_evidence_store.add_civilization_link(
            owner_identity_id=_identity(sync=True),
            release_id=release_id,
            level=payload.get("level"),
            value=payload.get("value"),
            evidence_receipt_id=payload.get("evidence_receipt_id"),
        )

    return _handle_write(action)


@bp.post("/tune/releases/<release_id>/recovery-manifests")
@web_security.login_required(api=True, founder_only=True)
def capture_tune_recovery_manifest(release_id: str):
    """Capture server-derived owned Music/Records/Live metadata for read-back."""
    def action():
        owner = _identity(sync=True)
        tune = product_core_services.tune_dashboard(owner)
        release = next(
            (row for row in tune.get("releases", [])
             if row.get("release_id") == release_id),
            None,
        )
        if release is None:
            raise PermissionError("music_release_not_owned")
        evidence_rows = _music_evidence_store.read_receipts(
            owner_identity_id=owner,
            release_id=release_id,
        )
        records = _records_store.dashboard(owner_identity_id=owner)
        live = _live_music_store.dashboard(owner_identity_id=owner)
        payload = {
            "release": release,
            "evidence_receipts": evidence_rows,
            "records": {
                "masters": [
                    row for row in records.get("masters", [])
                    if row.get("release_id") == release_id
                ],
                "credits": [
                    row for row in records.get("credits", [])
                    if row.get("release_id") == release_id
                ],
                "receipts": [
                    row for row in records.get("receipts", [])
                    if row.get("release_id") == release_id
                ],
            },
            "live_sessions": [
                row for row in live.get("sessions", [])
                if row.get("release_id") == release_id
            ],
        }
        return _music_recovery_store.capture(
            owner_identity_id=owner,
            release_id=release_id,
            payload=payload,
        )

    return _handle_write(action)


@bp.get("/tune/recovery-manifests/<manifest_id>")
@web_security.login_required(api=True, founder_only=True)
def read_tune_recovery_manifest(manifest_id: str):
    try:
        return _no_store(make_response(jsonify(
            _music_recovery_store.read_and_verify(
                owner_identity_id=_identity(),
                manifest_id=manifest_id,
            )
        )))
    except PermissionError:
        return _error("permission_denied", "Recovery manifest unavailable.", 403)
    except (TypeError, ValueError, RuntimeError):
        return _error(
            "music_recovery_unavailable",
            "Music recovery manifest is temporarily unavailable.",
            503,
        )


@bp.get("/tune/releases/<release_id>/acceptance")
@web_security.login_required(api=True, founder_only=True)
def tune_release_acceptance(release_id: str):
    try:
        receipts = _music_acceptance_store.read(
            owner_identity_id=_identity(),
            release_id=release_id,
        )
        return _no_store(make_response(jsonify({
            "release_id": release_id,
            "receipts": receipts,
            "completion_gate": music_acceptance.software_completion_gate(receipts),
        })))
    except PermissionError:
        return _error("permission_denied", "Acceptance receipts unavailable.", 403)
    except (TypeError, ValueError, RuntimeError):
        return _error(
            "music_acceptance_unavailable",
            "Music acceptance receipts are temporarily unavailable.",
            503,
        )


@bp.post("/tune/releases/<release_id>/acceptance")
@web_security.login_required(api=True, founder_only=True)
def append_tune_release_acceptance(release_id: str):
    def action():
        payload = _payload()
        encoded = payload.get("evidence_base64")
        if not isinstance(encoded, str) or len(encoded) > 11_500_000:
            raise ValueError("invalid_evidence_base64")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("invalid_evidence_base64") from exc
        return _music_acceptance_store.append(
            owner_identity_id=_identity(sync=True),
            release_id=release_id,
            acceptance_kind=payload.get("acceptance_kind"),
            evidence_bytes=raw,
            evidence_reference=payload.get("evidence_reference"),
            human_approval_reference=payload.get("human_approval_reference"),
        )

    return _handle_write(action)


@bp.get("/music-civilization")
@web_security.login_required(api=True)
def music_civilization_status():
    """Single Music/Radio/Records/Live contract with no execution authority."""
    return _no_store(make_response(jsonify(music_civilization.contracts())))


@bp.post("/entertainment/open-cinema/preview")
@web_security.login_required(api=True, founder_only=True)
def open_cinema_preview():
    """Private candidate preview, no fetch, persistence or publishing."""
    if not _write_allowed():
        return _error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
        return _error("invalid_request", "Candidate list required.", 400)
    return _no_store(make_response(jsonify(
        open_cinema.preview(payload["candidates"])
    )))


@bp.post("/entertainment/open-cinema/evidence-preview")
@web_security.login_required(api=True, founder_only=True)
def open_cinema_evidence_preview():
    """Inert private review envelope; never verifies document bytes or rights."""
    if not _write_allowed():
        return _error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("invalid_request", "Evidence review object required.", 400)
    return _no_store(make_response(jsonify(
        open_cinema_evidence.review_envelope(
            payload.get("candidate_id"), payload.get("territory"),
            payload.get("evidence"),
        )
    )))


@bp.get("/radio")
@web_security.login_required(api=True)
def radio_status():
    """Authenticated owner-scoped OAP Radio dashboard."""
    try:
        return _no_store(make_response(jsonify(
            _radio_store.dashboard(owner_identity_id=_identity())
        )))
    except (ValueError, RuntimeError):
        return _error("radio_unavailable", "OAP Radio is temporarily unavailable.", 503)


@bp.post("/radio/stations")
@web_security.login_required(api=True)
def create_radio_station():
    def action():
        payload = _payload()
        return _radio_store.create_station(
            owner_identity_id=_identity(sync=True),
            name=payload.get("name"),
            slug=payload.get("slug"),
        )

    return _handle_write(action)


@bp.post("/radio/stations/<station_id>/shows")
@web_security.login_required(api=True)
def create_radio_show(station_id: str):
    def action():
        payload = _payload()
        return _radio_store.create_show(
            owner_identity_id=_identity(sync=True),
            station_id=station_id,
            title=payload.get("title"),
        )

    return _handle_write(action)


@bp.post("/radio/stations/<station_id>/schedule")
@web_security.login_required(api=True)
def schedule_radio_show(station_id: str):
    def action():
        payload = _payload()
        return _radio_store.schedule_show(
            owner_identity_id=_identity(sync=True),
            station_id=station_id,
            show_id=payload.get("show_id"),
            starts_at=payload.get("starts_at"),
            ends_at=payload.get("ends_at"),
        )

    return _handle_write(action)


@bp.post("/radio/stations/<station_id>/rotation")
@web_security.login_required(api=True)
def add_radio_rotation(station_id: str):
    def action():
        payload = _payload()
        return _radio_store.add_rotation(
            owner_identity_id=_identity(sync=True),
            station_id=station_id,
            track_id=payload.get("track_id"),
            position=payload.get("position"),
        )

    return _handle_write(action)


@bp.post("/radio/stations/<station_id>/stop")
@web_security.login_required(api=True)
def stop_radio_station(station_id: str):
    def action():
        payload = _payload()
        return _radio_store.stop_station(
            owner_identity_id=_identity(sync=True),
            station_id=station_id,
            reason=payload.get("reason"),
        )

    return _handle_write(action)


@bp.get("/records")
@web_security.login_required(api=True)
def records_status():
    try:
        return _no_store(make_response(jsonify(
            _records_store.dashboard(owner_identity_id=_identity())
        )))
    except (ValueError, RuntimeError):
        return _error("records_unavailable", "OAP Records is temporarily unavailable.", 503)


@bp.post("/records/masters")
@web_security.login_required(api=True)
def create_records_master():
    def action():
        payload = _payload()
        return _records_store.create_master(
            owner_identity_id=_identity(sync=True),
            release_id=payload.get("release_id"),
            track_id=payload.get("track_id"),
            version_label=payload.get("version_label"),
            evidence_receipt_id=payload.get("evidence_receipt_id"),
        )

    return _handle_write(action)


@bp.post("/records/credits")
@web_security.login_required(api=True)
def create_records_credit():
    def action():
        payload = _payload()
        return _records_store.add_credit(
            owner_identity_id=_identity(sync=True),
            release_id=payload.get("release_id"),
            role=payload.get("role"),
            display_name=payload.get("display_name"),
            evidence_receipt_id=payload.get("evidence_receipt_id"),
        )

    return _handle_write(action)


@bp.post("/records/receipts")
@web_security.login_required(api=True)
def create_records_receipt():
    def action():
        payload = _payload()
        return _records_store.append_receipt(
            owner_identity_id=_identity(sync=True),
            release_id=payload.get("release_id"),
            receipt_kind=payload.get("receipt_kind"),
            destination=payload.get("destination"),
            reference=payload.get("reference"),
        )

    return _handle_write(action)


@bp.get("/live-music")
@web_security.login_required(api=True)
def live_music_status():
    try:
        return _no_store(make_response(jsonify(
            _live_music_store.dashboard(owner_identity_id=_identity())
        )))
    except (ValueError, RuntimeError):
        return _error("live_music_unavailable", "OAP Live Music is temporarily unavailable.", 503)


@bp.post("/live-music/sessions")
@web_security.login_required(api=True)
def create_live_music_session():
    def action():
        payload = _payload()
        return _live_music_store.create_session(
            owner_identity_id=_identity(sync=True),
            release_id=payload.get("release_id"),
            title=payload.get("title"),
        )

    return _handle_write(action)


@bp.post("/live-music/sessions/<session_id>/stop")
@web_security.login_required(api=True)
def stop_live_music_session(session_id: str):
    def action():
        payload = _payload()
        return _live_music_store.stop_session(
            owner_identity_id=_identity(sync=True),
            session_id=session_id,
            reference=payload.get("reference"),
        )

    return _handle_write(action)


@bp.post("/live-music/sessions/<session_id>/archive")
@web_security.login_required(api=True)
def archive_live_music_session(session_id: str):
    def action():
        payload = _payload()
        return _live_music_store.archive_session(
            owner_identity_id=_identity(sync=True),
            session_id=session_id,
            master_id=payload.get("master_id"),
        )

    return _handle_write(action)


@bp.get("/distribution")
@web_security.login_required(api=True)
def distribution_status():
    try:
        return _no_store(make_response(jsonify(_distribution_projection(_identity()))))
    except (ValueError, RuntimeError):
        return _error(
            "distribution_unavailable",
            "OAP Distribution is temporarily unavailable.",
            503,
        )


@bp.get("/distribution/runtime")
@web_security.login_required(api=True)
def distribution_runtime_list():
    try:
        owner = _identity()
        return _no_store(make_response(jsonify({
            "runtime": distribution_runtime.status(),
            "items": _distribution_runtime_store.list_for_owner(
                owner_identity_id=owner
            ),
            "analytics": _distribution_runtime_store.analytics(
                owner_identity_id=owner
            ),
        })))
    except (ValueError, RuntimeError):
        return _error(
            "distribution_runtime_unavailable",
            "OAP Distribution Runtime is temporarily unavailable.",
            503,
        )


@bp.get("/distribution/runtime/<distribution_id>")
@web_security.login_required(api=True)
def distribution_runtime_item(distribution_id: str):
    try:
        return _no_store(make_response(jsonify(
            _distribution_runtime_store.read(
                owner_identity_id=_identity(),
                distribution_id=distribution_id,
            )
        )))
    except PermissionError:
        return _error("permission_denied", "Distribution item unavailable.", 403)
    except (ValueError, RuntimeError):
        return _error(
            "distribution_runtime_unavailable",
            "OAP Distribution Runtime is temporarily unavailable.",
            503,
        )


@bp.post("/distribution/runtime")
@web_security.login_required(api=True)
def create_distribution_runtime_item():
    def action():
        payload = _payload()
        return _distribution_runtime_store.create(
            owner_identity_id=_identity(sync=True),
            lane=payload.get("lane"),
            subject_type=payload.get("subject_type"),
            subject_id=payload.get("subject_id"),
            source_reference=payload.get("source_reference"),
            destination_reference=payload.get("destination_reference"),
            order_id=payload.get("order_id"),
        )

    return _handle_write(action)


@bp.post("/distribution/runtime/<distribution_id>/transition")
@web_security.login_required(api=True)
def transition_distribution_runtime_item(distribution_id: str):
    def action():
        payload = _payload()
        return _distribution_runtime_store.transition(
            owner_identity_id=_identity(sync=True),
            distribution_id=distribution_id,
            target_state=payload.get("target_state"),
            evidence_reference=payload.get("evidence_reference"),
        )

    return _handle_write(action)


@bp.get("/distribution-market-media")
@web_security.login_required(api=True)
def distribution_market_media_status():
    try:
        return _no_store(
            make_response(jsonify(_distribution_market_media_projection(_identity())))
        )
    except (ValueError, RuntimeError):
        return _error(
            "distribution_market_media_unavailable",
            "OAP Distribution, Market and Media are temporarily unavailable.",
            503,
        )


@bp.get("/distribution-market-media/dashboard")
@web_security.login_required(founder_only=True)
def distribution_market_media_dashboard():
    try:
        response = make_response(
            render_template(
                "distribution_market_media.html",
                suite=_distribution_market_media_projection(_identity()),
                error=None,
            )
        )
    except (ValueError, RuntimeError):
        response = make_response(
            render_template(
                "distribution_market_media.html",
                suite=None,
                error="The governed product-organ store is temporarily unavailable.",
            ),
            503,
        )
    return _no_store(response)


@bp.post("/tune/releases")
@web_security.login_required(api=True)
def create_release():
    def action():
        payload = _payload()
        return _store.create_release(
            owner_identity_id=_identity(sync=True),
            title=payload.get("title"),
            release_type=payload.get("release_type"),
            idempotency_key=payload.get("idempotency_key"),
        )

    return _handle_write(action)


@bp.post("/tune/releases/<release_id>/tracks")
@web_security.login_required(api=True)
def add_track(release_id: str):
    def action():
        payload = _payload()
        return _store.add_track(
            owner_identity_id=_identity(sync=True),
            release_id=release_id,
            title=payload.get("title"),
            position=payload.get("position"),
            media_ref=payload.get("media_ref"),
            duration_ms=payload.get("duration_ms"),
            explicit=bool(payload.get("explicit", False)),
        )

    return _handle_write(action)


@bp.post("/tune/releases/<release_id>/upload")
@web_security.login_required(api=True)
def upload_track_audio(release_id: str):
    """Store one owned audio file and bind it to a canonical OAP Music track."""

    if not _write_allowed():
        return _error("csrf_failed", "The secure session expired. Refresh and try again.", 403)
    upload = request.files.get("audio")
    if upload is None or not upload.filename:
        return _error("invalid_request", "Choose an audio file to upload.", 400)
    try:
        media = upload.read(music_assets.MAX_AUDIO_BYTES + 1)
        owner = _identity(sync=True)
        asset, track = _music_asset_store.create_track_asset(
            owner_identity_id=owner,
            release_id=release_id,
            title=request.form.get("title") or upload.filename.rsplit(".", 1)[0],
            position=request.form.get("position"),
            original_name=upload.filename,
            mime_type=upload.mimetype,
            media=media,
            duration_ms=request.form.get("duration_ms"),
            explicit=str(request.form.get("explicit", "")).lower()
            in {"1", "true", "yes", "on"},
        )
        response = make_response(
            jsonify(
                asset=asset,
                track=track,
                player_url=f"/mission/organs/tune/assets/{asset['asset_id']}/audio",
                radio_queue_ready=True,
                public_broadcast_enabled=False,
                external_distribution_enabled=False,
                rights_verified_by_software=False,
                human_authority_final=True,
            ),
            201,
        )
        return _no_store(response)
    except PermissionError as exc:
        return _error("permission_denied", str(exc), 403)
    except (TypeError, ValueError) as exc:
        return _error("invalid_request", str(exc), 400)
    except (
        music_assets.MusicAssetUnavailable,
        public_store.PublicStoreUnavailable,
        product_store.ProductStoreUnavailable,
        RuntimeError,
    ):
        return _error("organ_unavailable", "OAP Music audio storage is temporarily unavailable.", 503)
    except (OSError, EOFError):
        return _error("organ_unavailable", "OAP Music audio storage is temporarily unavailable.", 503)


@bp.get("/tune/assets")
@web_security.login_required(api=True)
def list_track_audio_assets():
    try:
        return _no_store(
            make_response(
                jsonify(
                    assets=_music_asset_store.list_assets(
                        owner_identity_id=_identity()
                    ),
                    playback_scope="OWNER_PRIVATE",
                )
            )
        )
    except (ValueError, music_assets.MusicAssetUnavailable):
        return _error("organ_unavailable", "OAP Music audio storage is temporarily unavailable.", 503)


@bp.get("/tune/assets/<asset_id>/audio")
@web_security.login_required(api=True)
def play_track_audio_asset(asset_id: str):
    try:
        item = _music_asset_store.read(
            owner_identity_id=_identity(),
            asset_id=asset_id,
        )
        if item is None:
            return _error("not_found", "Audio asset unavailable.", 404)
        media, mime_type, digest, original_name = item
        total = len(media)
        status = 200
        body = media
        content_range = None
        requested_range = request.headers.get("Range", "").strip()
        if requested_range:
            if not requested_range.startswith("bytes=") or "," in requested_range:
                response = make_response("", 416)
                response.headers["Content-Range"] = f"bytes */{total}"
                return _no_store(response)
            spec = requested_range[6:]
            start_text, separator, end_text = spec.partition("-")
            if not separator:
                response = make_response("", 416)
                response.headers["Content-Range"] = f"bytes */{total}"
                return _no_store(response)
            try:
                if start_text:
                    range_start = int(start_text)
                    range_end = int(end_text) if end_text else total - 1
                else:
                    suffix = int(end_text)
                    if suffix <= 0:
                        raise ValueError("invalid_range")
                    range_start = max(total - suffix, 0)
                    range_end = total - 1
            except ValueError:
                response = make_response("", 416)
                response.headers["Content-Range"] = f"bytes */{total}"
                return _no_store(response)
            if range_start < 0 or range_start >= total or range_end < range_start:
                response = make_response("", 416)
                response.headers["Content-Range"] = f"bytes */{total}"
                return _no_store(response)
            range_end = min(range_end, total - 1)
            body = media[range_start : range_end + 1]
            status = 206
            content_range = f"bytes {range_start}-{range_end}/{total}"

        response = make_response(body, status)
        response.headers["Content-Type"] = mime_type
        response.headers["Content-Length"] = str(len(body))
        response.headers["ETag"] = f'"{digest}"'
        safe_name = (
            original_name.replace(chr(34), "")
            .replace(chr(13), "")
            .replace(chr(10), "")
        )
        response.headers["Content-Disposition"] = f'inline; filename="{safe_name}"'
        response.headers["Accept-Ranges"] = "bytes"
        if content_range is not None:
            response.headers["Content-Range"] = content_range
        return _no_store(response)
    except (TypeError, ValueError):
        return _error("invalid_request", "Invalid audio asset.", 400)
    except music_assets.MusicAssetUnavailable:
        return _error("organ_unavailable", "OAP Music audio storage is temporarily unavailable.", 503)


@bp.post("/tune/releases/<release_id>/review")
@web_security.login_required(api=True)
def review_release(release_id: str):
    return _handle_write(
        lambda: _store.submit_release_for_review(
            owner_identity_id=_identity(sync=True), release_id=release_id
        )
    )


@bp.post("/tune/playlists")
@web_security.login_required(api=True)
def create_playlist():
    def action():
        payload = _payload()
        return _store.create_playlist(
            owner_identity_id=_identity(sync=True),
            title=payload.get("title"),
            visibility=payload.get("visibility", "PRIVATE"),
        )

    return _handle_write(action)


@bp.post("/tune/playlists/<playlist_id>/tracks")
@web_security.login_required(api=True)
def add_playlist_track(playlist_id: str):
    def action():
        payload = _payload()
        return product_core_services.add_playlist_track(
            owner_identity_id=_identity(sync=True),
            playlist_id=playlist_id,
            track_id=payload.get("track_id"),
            position=payload.get("position"),
        )

    return _handle_write(action)


@bp.get("/commerce")
@web_security.login_required(api=True)
def commerce_status():
    try:
        return _no_store(
            make_response(jsonify(product_core_services.commerce_dashboard(_identity())))
        )
    except (ValueError, RuntimeError):
        return _error("commerce_unavailable", "OAP Commerce Core is temporarily unavailable.", 503)


@bp.get("/market")
@web_security.login_required(api=True)
def market_status():
    try:
        return _no_store(make_response(jsonify(_market_projection(_identity()))))
    except (ValueError, RuntimeError):
        return _error("market_unavailable", "OAP Market is temporarily unavailable.", 503)


@bp.post("/commerce/storefront")
@web_security.login_required(api=True)
def create_storefront():
    def action():
        payload = _payload()
        seller = _require_certified_merchant(_identity(sync=True))
        return _store.create_storefront(
            seller_identity_id=seller,
            store_name=payload.get("store_name"),
            slug=payload.get("slug"),
        )

    return _handle_write(action)


@bp.post("/commerce/products")
@web_security.login_required(api=True)
def create_product():
    def action():
        payload = _payload()
        seller = _require_certified_merchant(_identity(sync=True))
        product_id = product_store.create_product(
            seller,
            name=payload.get("name"),
            description=payload.get("description"),
            price=payload.get("price"),
        )
        return {
            "product_id": product_id,
            "payment_capture_performed": False,
            "external_fulfilment_performed": False,
        }

    return _handle_write(action)


@bp.post("/commerce/orders")
@web_security.login_required(api=True)
def create_order():
    def action():
        payload = _payload()
        product_id = payload.get("product_id")
        gate = market_supplier_network.STORE.order_intent_allowed(
            product_id=product_id
        )
        if gate.get("allowed") is not True:
            raise ValueError(str(gate.get("reason") or "supplier_not_ready"))
        return _store.create_order_intent(
            buyer_identity_id=_identity(sync=True),
            product_id=product_id,
            quantity=payload.get("quantity", 1),
            idempotency_key=payload.get("idempotency_key"),
        )

    return _handle_write(action)


@bp.get("/market/suppliers")
@web_security.login_required(api=True)
def market_supplier_bindings():
    try:
        identity = _require_certified_merchant(_identity())
        return _no_store(make_response(jsonify({
            "supplier_network": market_supplier_network.truth_status(),
            "bindings": market_supplier_network.STORE.owner_bindings(
                seller_identity_id=identity
            ),
        })))
    except PermissionError as exc:
        return _error("permission_denied", str(exc), 403)
    except (ValueError, RuntimeError):
        return _error(
            "supplier_network_unavailable",
            "Supplier Network is temporarily unavailable.",
            503,
        )


@bp.post("/market/products/<product_id>/supplier-ready")
@web_security.login_required(api=True)
def mark_market_supplier_ready(product_id: str):
    def action():
        payload = _payload()
        seller = _require_certified_merchant(_identity(sync=True))
        return market_supplier_network.STORE.mark_ready(
            seller_identity_id=seller,
            product_id=product_id,
            evidence_reference=payload.get("evidence_reference"),
        )

    return _handle_write(action)


@bp.post("/market/products/<product_id>/supplier-stop")
@web_security.login_required(api=True)
def stop_market_supplier(product_id: str):
    def action():
        payload = _payload()
        seller = _require_certified_merchant(_identity(sync=True))
        return market_supplier_network.STORE.stop(
            seller_identity_id=seller,
            product_id=product_id,
            reason=payload.get("reason"),
        )

    return _handle_write(action)



@bp.post("/market/music-products")
@web_security.login_required(api=True)
def create_music_market_product():
    """Bind one rights-ready OAP Music release to one Market product."""
    def action():
        payload = _payload()
        seller = _require_certified_merchant(_identity(sync=True))
        split_plan = payload.get("split_plan")
        if not isinstance(split_plan, list):
            raise TypeError("split_plan_required")
        return _music_market_purchase_store.link_release_product(
            seller_identity_id=seller,
            release_id=payload.get("release_id"),
            product_id=payload.get("product_id"),
            rights_evidence_receipt_id=payload.get("rights_evidence_receipt_id"),
            split_plan=split_plan,
            optional_pay_more=bool(payload.get("optional_pay_more", True)),
        )

    return _handle_write(action)


@bp.post("/market/music-orders")
@web_security.login_required(api=True)
def create_music_market_order():
    """Create a Commerce order for a linked Music product without supplier fulfilment."""
    def action():
        payload = _payload()
        identity = _identity(sync=True)
        product_id = payload.get("product_id")
        price_minor = payload.get("price_minor")
        with music_market_purchase.postgres_db.connect(readonly=True) as connection:
            linked = connection.execute(
                """SELECT minimum_price_minor,optional_pay_more,state
                   FROM oap_music_market_products WHERE product_id=%s""",
                (product_id,),
            ).fetchone()
        if linked is None or str(linked[2]) != "READY":
            raise ValueError("music_market_product_not_ready")
        minimum = int(linked[0])
        with music_market_purchase.postgres_db.connect(readonly=True) as connection:
            product_row = connection.execute(
                "SELECT price_minor FROM products WHERE id=%s AND active=TRUE",
                (product_id,),
            ).fetchone()
        if product_row is None:
            raise ValueError("market_product_unavailable")
        effective_price = music_market_purchase.validate_order_terms(
            listing_price_minor=product_row[0],
            requested_price_minor=price_minor,
            minimum_price_minor=minimum,
            optional_pay_more=bool(linked[1]),
            quantity=1,
        )
        override = (
            effective_price if effective_price != int(product_row[0]) else None
        )
        order = _store.create_order_intent(
            buyer_identity_id=identity,
            product_id=product_id,
            quantity=1,
            idempotency_key=payload.get("idempotency_key"),
            unit_price_override_minor=override,
        )
        transaction = market_transaction_spine.STORE.create_from_order(
            buyer_identity_id=identity,
            order_id=order["order_id"],
            idempotency_key=f"music:{payload.get('idempotency_key')}",
        )
        return {
            "order": order,
            "transaction": transaction,
            "ownership_granted": False,
            "payment_capture_performed": False,
            "payout_performed": False,
        }

    return _handle_write(action)


@bp.post("/market/music-orders/<order_id>/finalize")
@web_security.login_required(api=True)
def finalize_music_market_order(order_id: str):
    """Observe an existing CAPTURED payment and mint the buyer entitlement."""
    return _handle_write(
        lambda: _music_market_purchase_store.finalize_captured_order(
            buyer_identity_id=_identity(sync=True),
            order_id=order_id,
        )
    )


@bp.get("/tune/library/purchases")
@web_security.login_required(api=True)
def music_purchase_library():
    try:
        return _no_store(
            make_response(
                jsonify(
                    {
                        "items": _music_market_purchase_store.library(
                            buyer_identity_id=_identity()
                        ),
                        "ownership_source": "captured_commerce_order",
                        "payment_capture_performed_here": False,
                    }
                )
            )
        )
    except (ValueError, RuntimeError):
        return _error(
            "music_library_unavailable",
            "Purchased Music library is temporarily unavailable.",
            503,
        )


@bp.get("/market/music-entitlements/<entitlement_id>/splits")
@web_security.login_required(api=True)
def music_purchase_splits(entitlement_id: str):
    try:
        return _no_store(
            make_response(
                jsonify(
                    {
                        "splits": _music_market_purchase_store.split_ledger(
                            identity_id=_identity(),
                            entitlement_id=entitlement_id,
                        ),
                        "payout_performed": False,
                    }
                )
            )
        )
    except PermissionError:
        return _error("permission_denied", "Split ledger unavailable.", 403)
    except (ValueError, RuntimeError):
        return _error(
            "music_split_ledger_unavailable",
            "Music split ledger is temporarily unavailable.",
            503,
        )


@bp.get("/market/orders")
@web_security.login_required(api=True)
def market_orders():
    try:
        identity = _identity()
        return _no_store(make_response(jsonify({
            "orders": product_core_services.commerce_dashboard(identity).get("orders", []),
            "transactions": market_transaction_spine.STORE.list_for_identity(
                identity_id=identity
            ),
            "payment_capture_performed": False,
            "external_fulfilment_performed": False,
            "human_authority_final": True,
        })))
    except (ValueError, RuntimeError):
        return _error("market_unavailable", "OAP Market is temporarily unavailable.", 503)


@bp.post("/market/orders")
@web_security.login_required(api=True)
def create_market_order():
    def action():
        payload = _payload()
        identity = _identity(sync=True)
        key = str(payload.get("idempotency_key") or "")
        product_id = payload.get("product_id")
        gate = market_supplier_network.STORE.order_intent_allowed(
            product_id=product_id
        )
        if gate.get("allowed") is not True:
            raise ValueError(str(gate.get("reason") or "supplier_not_ready"))
        order = _store.create_order_intent(
            buyer_identity_id=identity,
            product_id=product_id,
            quantity=payload.get("quantity", 1),
            idempotency_key=key,
        )
        transaction = market_transaction_spine.STORE.create_from_order(
            buyer_identity_id=identity,
            order_id=order["order_id"],
            idempotency_key=f"market:{key}",
        )
        return {
            "order": order,
            "transaction": transaction,
            "payment_capture_performed": False,
            "money_transfer_performed": False,
            "external_fulfilment_performed": False,
            "automatic_dispatch_performed": False,
            "human_authority_final": True,
        }

    return _handle_write(action)


@bp.get("/market/orders/<order_id>")
@web_security.login_required(api=True)
def market_order_detail(order_id: str):
    try:
        return _no_store(make_response(jsonify(
            product_core_services.commerce_order_detail(_identity(), order_id)
        )))
    except PermissionError:
        return _error("permission_denied", "Order unavailable for this identity.", 403)
    except (ValueError, RuntimeError):
        return _error("market_unavailable", "OAP Market is temporarily unavailable.", 503)


@bp.get("/market/transactions/<transaction_id>")
@web_security.login_required(api=True)
def market_transaction_detail(transaction_id: str):
    try:
        identity = _identity()
        transaction = market_transaction_spine.STORE.read_for_identity(
            transaction_id=transaction_id,
            identity_id=identity,
        )
        events = market_transaction_spine.STORE.events_for_identity(
            transaction_id=transaction_id,
            identity_id=identity,
        )
        recovery = market_transaction_spine.STORE.recovery_view(
            transaction_id=transaction_id,
            identity_id=identity,
        )
        return _no_store(make_response(jsonify({
            "transaction": transaction,
            "events": events,
            "recovery": recovery,
            "payment_capture_performed": False,
            "external_fulfilment_performed": False,
            "carrier_handoff_performed": False,
        })))
    except PermissionError:
        return _error("permission_denied", "Transaction unavailable for this identity.", 403)
    except (ValueError, RuntimeError):
        return _error("market_unavailable", "OAP Market is temporarily unavailable.", 503)


@bp.post("/market/transactions/<transaction_id>/stop")
@web_security.login_required(api=True)
def stop_market_transaction(transaction_id: str):
    return _handle_write(
        lambda: market_transaction_spine.STORE.stop(
            transaction_id=transaction_id,
            actor_identity_id=_identity(sync=True),
        )
    )


@bp.get("/post")
@web_security.login_required(api=True)
def post_status():
    try:
        return _no_store(make_response(jsonify(product_core_services.post_dashboard(_identity()))))
    except (ValueError, RuntimeError):
        return _error("post_unavailable", "OAP Post Core is temporarily unavailable.", 503)


@bp.post("/post/requests")
@web_security.login_required(api=True)
def create_post_request():
    def action():
        payload = _payload()
        details = payload.get("details")
        if details is not None and not isinstance(details, dict):
            raise TypeError("post_office_details_must_be_object")
        return _store.create_post_office_request(
            identity_id=_identity(sync=True),
            service_type=payload.get("service_type"),
            details=details,
            idempotency_key=payload.get("idempotency_key"),
            post_office_id=payload.get("post_office_id"),
        )

    return _handle_write(action)


@bp.post("/post/parcels")
@web_security.login_required(api=True)
def create_parcel():
    def action():
        payload = _payload()
        return _store.create_parcel_intent(
            owner_identity_id=_identity(sync=True),
            direction=payload.get("direction"),
            idempotency_key=payload.get("idempotency_key"),
            post_office_id=payload.get("post_office_id"),
        )

    return _handle_write(action)


@bp.get("/market/install-status")
@web_security.login_required(api=True, founder_only=True)
def market_install_status():
    """Founder-only secret-free install/provider readiness."""

    try:
        return _no_store(make_response(jsonify(commerce_install.status())))
    except RuntimeError:
        return _error(
            "commerce_install_status_unavailable",
            "Commerce install status is temporarily unavailable.",
            503,
        )


@bp.post("/market/install")
@web_security.login_required(api=True, founder_only=True)
def install_market_commerce_runtime():
    """Apply the unified commerce schema only after explicit Founder action."""

    def action():
        payload = _payload()
        return commerce_install.install(
            assume_yes=True,
            dry_run=bool(payload.get("dry_run", True)),
        )

    return _handle_write(action)


@bp.post("/market/payments/<payment_id>/execute")
@web_security.login_required(api=True, founder_only=True)
def execute_market_payment(payment_id: str):
    """Submit one already-AUTHORISED SIKA payment to the private provider."""

    def action():
        owner = _identity(sync=True)
        payload = _payload()
        intent = sika_payment_orchestrator.read_intent(payment_id)
        if intent is None:
            raise ValueError("payment_intent_not_found")
        if intent.status == "SUBMITTED":
            return {
                "payment": intent.as_dict(),
                "idempotent": True,
                "provider_called": False,
                "human_authority_final": True,
            }
        if intent.status != "AUTHORISED":
            raise ValueError("payment_not_authorised_for_provider_submission")
        provider_payload = payload.get("provider_payload")
        if provider_payload is None:
            provider_payload = {}
        if not isinstance(provider_payload, dict):
            raise TypeError("provider_payload_object_required")
        outbound = dict(provider_payload)
        outbound.update(
            payment_id=intent.payment_id,
            payee_reference=intent.payee_reference,
            amount=f"{intent.amount:.2f}",
            currency=intent.currency,
            jurisdiction=intent.jurisdiction,
        )
        receipt = sika_secure_provider_runtime.submit(
            kind="payment",
            payload=outbound,
            idempotency_key=intent.idempotency_key,
        )
        durable = commerce_provider_receipts.record(
            owner_identity_id=owner,
            kind="payment",
            subject_id=intent.payment_id,
            provider_receipt=receipt,
        )
        evidence = sika_payment_submission_evidence.record(
            evidence_id=str(uuid.uuid4()),
            payment_id=intent.payment_id,
            idempotency_key=intent.idempotency_key,
            provider_id=receipt["provider_id"],
            provider_reference=receipt["provider_reference"],
            outcome="ACCEPTED",
            evidence_hash=receipt["receipt_hash"],
        )
        submitted = sika_payment_orchestrator.transition(
            payment_id=intent.payment_id,
            target_status="SUBMITTED",
            provider_reference=receipt["provider_reference"],
        )
        return {
            "payment": submitted.as_dict(),
            "receipt": durable,
            "submission_evidence_id": evidence.evidence_id,
            "provider_called": True,
            "money_movement_claimed": False,
            "secret_values_exposed": False,
            "human_authority_final": True,
        }

    return _handle_write(action)


@bp.post("/market/payments/provider/webhook")
def market_payment_provider_webhook():
    """Accept only timestamped HMAC-verified provider payment callbacks."""

    raw = request.get_data(cache=True)
    timestamp = request.headers.get("X-OAP-Provider-Timestamp", "")
    signature = request.headers.get("X-OAP-Provider-Signature", "")
    try:
        verified = sika_secure_provider_runtime.verify_webhook(
            kind="payment",
            body=raw,
            timestamp=timestamp,
            signature=signature,
        )
        if verified.get("signature_verified") is not True:
            return _error("provider_signature_invalid", "Invalid provider signature.", 403)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise TypeError("provider_webhook_json_required")
        payment_id = str(payload.get("payment_id") or "").strip()
        state = str(payload.get("status") or payload.get("state") or "").strip().upper()
        if not payment_id:
            raise ValueError("payment_id_required")
        intent = sika_payment_orchestrator.read_intent(payment_id)
        if intent is None:
            raise ValueError("payment_intent_not_found")
        owner = commerce_provider_receipts.owner_for_subject(payment_id)
        if owner is None:
            raise ValueError("provider_receipt_owner_unavailable")
        webhook_receipt = sika_secure_provider_runtime.webhook_receipt(
            kind="payment",
            payload=payload,
            idempotency_key=f"payhook:{payment_id}:{timestamp}",
        )
        durable = commerce_provider_receipts.record(
            owner_identity_id=owner,
            kind="payment_webhook",
            subject_id=payment_id,
            provider_receipt=webhook_receipt,
        )
        target = {
            "SETTLED": "SETTLED",
            "CAPTURED": "SETTLED",
            "SUCCEEDED": "SETTLED",
            "FAILED": "FAILED",
            "REJECTED": "FAILED",
        }.get(state)
        payment = intent
        if target is not None and intent.status == "SUBMITTED":
            payment = sika_payment_orchestrator.transition(
                payment_id=payment_id,
                target_status=target,
            )
        return _no_store(
            make_response(
                jsonify(
                    accepted=True,
                    payment=payment.as_dict(),
                    receipt=durable,
                    signature_verified=True,
                    secret_values_exposed=False,
                )
            )
        )
    except (TypeError, ValueError):
        return _error("provider_webhook_invalid", "Invalid provider webhook.", 400)
    except RuntimeError:
        return _error("provider_webhook_unavailable", "Provider webhook unavailable.", 503)


@bp.post("/market/pod/<subject_id>/execute")
@web_security.login_required(api=True, founder_only=True)
def execute_market_pod(subject_id: str):
    """Submit one governed POD request and persist its provider receipt."""

    def action():
        owner = _identity(sync=True)
        payload = _payload()
        provider_payload = payload.get("provider_payload")
        if not isinstance(provider_payload, dict):
            raise TypeError("provider_payload_object_required")
        outbound = dict(provider_payload)
        outbound["oap_subject_id"] = subject_id
        pod_status = sika_secure_provider_runtime.configuration_status("pod")
        if str(pod_status.get("provider_id") or "").lower() == "prodigi":
            receipt = prodigi_pod_adapter.submit_order(
                payload=outbound,
                idempotency_key=payload.get("idempotency_key"),
            )
        else:
            receipt = sika_secure_provider_runtime.submit(
                kind="pod",
                payload=outbound,
                idempotency_key=payload.get("idempotency_key"),
            )
        durable = commerce_provider_receipts.record(
            owner_identity_id=owner,
            kind="pod",
            subject_id=subject_id,
            provider_receipt=receipt,
        )
        distribution = None
        distribution_id = payload.get("distribution_id")
        if distribution_id:
            distribution = _distribution_runtime_store.transition(
                owner_identity_id=owner,
                distribution_id=distribution_id,
                target_state="HANDED_OFF",
                evidence_reference=receipt["receipt_hash"],
            )
        return {
            "receipt": durable,
            "distribution": distribution,
            "provider_called": True,
            "secret_values_exposed": False,
            "human_authority_final": True,
        }

    return _handle_write(action)


@bp.post("/market/pod/provider/webhook")
def market_pod_provider_webhook():
    """Verify POD callback then persist and advance an owned Distribution item."""

    raw = request.get_data(cache=True)
    timestamp = request.headers.get("X-OAP-Provider-Timestamp", "")
    signature = request.headers.get("X-OAP-Provider-Signature", "")
    try:
        verified = sika_secure_provider_runtime.verify_webhook(
            kind="pod",
            body=raw,
            timestamp=timestamp,
            signature=signature,
        )
        if verified.get("signature_verified") is not True:
            return _error("provider_signature_invalid", "Invalid provider signature.", 403)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise TypeError("provider_webhook_json_required")
        subject_id = str(payload.get("oap_subject_id") or payload.get("subject_id") or "").strip()
        if not subject_id:
            raise ValueError("pod_subject_id_required")
        owner = commerce_provider_receipts.owner_for_subject(subject_id)
        if owner is None:
            raise ValueError("provider_receipt_owner_unavailable")
        webhook_receipt = sika_secure_provider_runtime.webhook_receipt(
            kind="pod",
            payload=payload,
            idempotency_key=f"podhook:{subject_id}:{timestamp}",
        )
        durable = commerce_provider_receipts.record(
            owner_identity_id=owner,
            kind="pod_webhook",
            subject_id=subject_id,
            provider_receipt=webhook_receipt,
        )
        distribution = None
        distribution_id = payload.get("distribution_id")
        state = str(payload.get("state") or payload.get("status") or "").upper()
        target = market_sika_pod_runtime.distribution_transition_for_supplier_state(state)
        if distribution_id and target is not None:
            distribution = _distribution_runtime_store.transition(
                owner_identity_id=owner,
                distribution_id=distribution_id,
                target_state=target,
                evidence_reference=webhook_receipt["receipt_hash"],
            )
        return _no_store(
            make_response(
                jsonify(
                    accepted=True,
                    receipt=durable,
                    distribution=distribution,
                    signature_verified=True,
                    secret_values_exposed=False,
                )
            )
        )
    except (TypeError, ValueError):
        return _error("provider_webhook_invalid", "Invalid provider webhook.", 400)
    except RuntimeError:
        return _error("provider_webhook_unavailable", "Provider webhook unavailable.", 503)
