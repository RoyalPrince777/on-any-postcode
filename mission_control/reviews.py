"""First-party OAP Reviews backed by the canonical owner-scoped workspace store."""

from __future__ import annotations

import json
import uuid
from typing import Any

from . import postgres_db, workspaces

PREFIX = "OAP-REVIEW:v1:"
MAX_BODY = 1200


class ReviewsUnavailable(RuntimeError):
    """Raised when the first-party reviews store cannot complete safely."""


def _identity(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_review_identity") from exc


def _product(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_review_product") from exc


def _rating(value: object) -> int:
    try:
        rating = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_review_rating") from exc
    if rating < 1 or rating > 5:
        raise ValueError("invalid_review_rating")
    return rating


def create_review(identity_id: object, *, product_id: object, rating: object, body: object) -> str:
    identity = _identity(identity_id)
    product = _product(product_id)
    stars = _rating(rating)
    text = " ".join(str(body or "").strip().split())[:MAX_BODY]
    if not text:
        raise ValueError("review_body_required")

    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT p.seller_id
                   FROM products p JOIN users u ON u.id=p.seller_id
                   WHERE p.id=%s AND p.active=TRUE AND u.status='active'
                   LIMIT 1""",
                (product,),
            ).fetchone()
            if row is None:
                raise ValueError("review_target_unavailable")
            if str(row[0]) == identity:
                raise ValueError("cannot_review_own_listing")
            existing = connection.execute(
                """SELECT 1 FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='market'
                     AND title LIKE %s AND status='active'
                   LIMIT 1""",
                (identity, f"{PREFIX}{product}:%"),
            ).fetchone()
            if existing is not None:
                raise ValueError("review_already_exists")
    except ValueError:
        raise
    except Exception as exc:
        raise ReviewsUnavailable("review_precheck_failed") from exc

    payload = json.dumps(
        {"product_id": product, "rating": stars, "body": text},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    try:
        return workspaces.add_record(
            identity,
            "market",
            title=f"{PREFIX}{product}:{stars}",
            body=payload,
            status="active",
        )
    except (ValueError, workspaces.WorkspaceUnavailable) as exc:
        if isinstance(exc, ValueError):
            raise
        raise ReviewsUnavailable("review_write_failed") from exc


def list_reviews(product_id: object, *, limit: int = 50) -> list[dict[str, Any]]:
    product = _product(product_id)
    bounded = max(1, min(int(limit), 100))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT w.record_id,w.identity_id,w.body,w.created_at,
                          COALESCE(u.display_name,u.username)
                   FROM oap_workspace_records w
                   JOIN users u ON u.id=w.identity_id
                   WHERE w.workspace_id='market'
                     AND w.title LIKE %s
                     AND w.status='active'
                     AND u.status='active'
                   ORDER BY w.created_at DESC
                   LIMIT %s""",
                (f"{PREFIX}{product}:%", bounded),
            ).fetchall()
    except Exception as exc:
        raise ReviewsUnavailable("review_read_failed") from exc

    reviews: list[dict[str, Any]] = []
    for row in rows:
        try:
            payload = json.loads(str(row[2]))
            stars = _rating(payload.get("rating"))
            body = str(payload.get("body") or "").strip()[:MAX_BODY]
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
        if not body:
            continue
        reviews.append(
            {
                "review_id": str(row[0]),
                "product_id": product,
                "rating": stars,
                "body": body,
                "author": str(row[4]),
                "created_at": row[3].isoformat(),
                "first_party": True,
                "owner_scoped_write": True,
            }
        )
    return reviews


def summaries(product_ids: list[object]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for value in product_ids[:100]:
        product = _product(value)
        rows = list_reviews(product, limit=100)
        count = len(rows)
        average = round(sum(int(item["rating"]) for item in rows) / count, 2) if count else None
        result[product] = {
            "count": count,
            "average": average,
            "reviews": rows[:5],
        }
    return result


def status() -> dict[str, object]:
    ready = False
    try:
        with postgres_db.connect(readonly=True) as connection:
            tables = connection.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name IN ('oap_workspace_records','products','users')"""
            ).fetchall()
            ready = {str(row[0]) for row in tables} == {
                "oap_workspace_records",
                "products",
                "users",
            }
    except Exception:  # noqa: BLE001
        ready = False
    return {
        "component": "OAP Reviews",
        "first_party": True,
        "canonical_store": "oap_workspace_records",
        "owner_scoped_writes": True,
        "schema_migration_required": False,
        "ready": ready,
        "payment_capture": False,
        "external_review_authority": False,
    }
