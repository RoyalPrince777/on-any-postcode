"""Canonical read-only hierarchy for The Spot, The Link and LinkUp."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

PRODUCT_HIERARCHY: tuple[dict[str, str], ...] = (
    {
        "id": "the_spot",
        "name": "The Spot",
        "route": "/the-spot",
        "parent_id": "",
        "purpose": "The postcode community place for local people, activity and discovery.",
        "owner": "OAP World",
    },
    {
        "id": "the_link",
        "name": "The Link",
        "route": "/the-link",
        "parent_id": "the_spot",
        "purpose": "The communications gateway inside The Spot.",
        "owner": "Communications",
    },
    {
        "id": "linkup",
        "name": "LinkUp",
        "route": "/linkup",
        "parent_id": "the_link",
        "purpose": "Protected person-to-person and group conversation inside The Link.",
        "owner": "Communications",
    },
)


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def validate_product_hierarchy(
    products: Iterable[Mapping[str, Any]] = PRODUCT_HIERARCHY,
) -> dict[str, Any]:
    """Reject duplicate products, routes, cycles and missing parents."""

    items = tuple(products)
    ids = [str(item.get("id", "")) for item in items]
    names = [_normalise(str(item.get("name", ""))) for item in items]
    routes = [str(item.get("route", "")) for item in items]
    errors: list[str] = []

    for label, values in (("IDs", ids), ("names", names), ("routes", routes)):
        if len(values) != len(set(values)):
            errors.append(f"Duplicate product {label}")

    known_ids = set(ids)
    for item in items:
        parent = str(item.get("parent_id", ""))
        if parent and parent not in known_ids:
            errors.append(f"Unknown parent for {item.get('id')}")
        if parent == item.get("id"):
            errors.append(f"Product cannot parent itself: {item.get('id')}")

    expected = (
        ("the_spot", ""),
        ("the_link", "the_spot"),
        ("linkup", "the_link"),
    )
    actual = tuple((item.get("id"), item.get("parent_id")) for item in items)
    if actual != expected:
        errors.append("The locked hierarchy must remain The Spot → The Link → LinkUp")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "products": len(items),
            "duplicate_ids": len(ids) - len(set(ids)),
            "duplicate_names": len(names) - len(set(names)),
            "duplicate_routes": len(routes) - len(set(routes)),
        },
    }


def get_public_product_hierarchy() -> dict[str, Any]:
    """Return the public product map without identities or conversations."""

    return {
        "products": tuple(dict(item) for item in PRODUCT_HIERARCHY),
        "validation": validate_product_hierarchy(),
        "law": "One World → One Front Door → Many Systems Inside",
        "human_authority": "Human Authority remains final",
        "execution_enabled": False,
    }
