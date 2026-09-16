"""First-party routing federation for Map Intelligence.

The federation keeps the proven Greater London router active while allowing
future UK regional shards to declare their own OAP-owned endpoints. No public or
demo router is accepted and cross-shard routes are never fabricated.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from . import routing


@dataclass(frozen=True)
class RoutingShard:
    shard_id: str
    label: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    endpoint_env: str
    active: bool = True

    def contains(self, latitude: object, longitude: object) -> bool:
        try:
            lat = float(latitude); lon = float(longitude)
        except (TypeError, ValueError):
            return False
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon

    def endpoint(self) -> str:
        return os.environ.get(self.endpoint_env, "").strip()


DEFAULT_SHARDS = (
    RoutingShard(
        shard_id="greater_london",
        label="Greater London",
        min_lat=51.28,
        max_lat=51.70,
        min_lon=-0.52,
        max_lon=0.34,
        endpoint_env="OAP_OSRM_BASE_URL",
        active=True,
    ),
)


def _configured_shards() -> tuple[RoutingShard, ...]:
    raw = os.environ.get("OAP_ROUTING_SHARDS_JSON", "").strip()
    if not raw:
        return DEFAULT_SHARDS
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return DEFAULT_SHARDS
    if not isinstance(parsed, list):
        return DEFAULT_SHARDS
    shards: list[RoutingShard] = []
    for item in parsed[:32]:
        if not isinstance(item, dict):
            continue
        try:
            shard_id = str(item.get("id") or "")[:48]
            endpoint_env = str(item.get("endpoint_env") or "")[:80]
            shard = RoutingShard(
                shard_id=shard_id,
                label=str(item.get("label") or "")[:80],
                min_lat=float(item["min_lat"]),
                max_lat=float(item["max_lat"]),
                min_lon=float(item["min_lon"]),
                max_lon=float(item["max_lon"]),
                endpoint_env=endpoint_env,
                active=bool(item.get("active", False)),
            )
        except (KeyError, TypeError, ValueError):
            continue
        if (
            shard.shard_id
            and shard.label
            and shard.endpoint_env.startswith("OAP_ROUTING_SHARD_")
            and shard.endpoint_env.endswith("_URL")
            and shard.min_lat < shard.max_lat
            and shard.min_lon < shard.max_lon
        ):
            shards.append(shard)
    return tuple(shards) or DEFAULT_SHARDS


def shards() -> tuple[RoutingShard, ...]:
    return _configured_shards()


def select_shard(start: dict[str, object], end: dict[str, object]) -> RoutingShard | None:
    for shard in shards():
        if shard.active and shard.contains(start.get("latitude"), start.get("longitude")) and shard.contains(end.get("latitude"), end.get("longitude")):
            return shard
    return None


def coverage_state(start: dict[str, object], end: dict[str, object]) -> dict[str, object]:
    shard = select_shard(start, end)
    connected = bool(shard and shard.endpoint())
    return {
        "selected_shard": shard.shard_id if shard else None,
        "selected_label": shard.label if shard else None,
        "route_expected": bool(shard and connected),
        "shard_connected": connected,
        "active_shards": [item.shard_id for item in shards() if item.active],
        "connected_shards": [item.shard_id for item in shards() if item.active and item.endpoint()],
        "federated": True,
        "cross_shard_routing": False,
    }


def map_route(*, start: dict[str, object], end: dict[str, object], profile: object = "driving") -> dict[str, Any]:
    shard = select_shard(start, end)
    if shard is None:
        raise routing.RoutingUnavailable("outside_current_oap_map_coverage")
    endpoint = shard.endpoint()
    if not endpoint:
        raise routing.RoutingUnavailable("routing_shard_not_connected")
    result = routing.map_route_via_owned_endpoint(
        base_url=endpoint,
        pickup_latitude=start["latitude"],
        pickup_longitude=start["longitude"],
        destination_latitude=end["latitude"],
        destination_longitude=end["longitude"],
        profile=profile,
    )
    result["routing_shard"] = shard.shard_id
    result["routing_region"] = shard.label
    result["federated"] = True
    return result


def status() -> dict[str, object]:
    active = [item for item in shards() if item.active]
    connected = [item for item in active if item.endpoint()]
    return {
        "component": "OAP Routing Federation",
        "federated": True,
        "active_shard_count": len(active),
        "connected_shard_count": len(connected),
        "active_shards": [{"id": item.shard_id, "label": item.label, "connected": bool(item.endpoint())} for item in active],
        "cross_shard_routing": False,
        "public_fallback_enabled": False,
        "external_route_authority": False,
        "ready_for_additional_owned_shards": True,
    }
