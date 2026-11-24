"""Read an existing Founder-imported OpenStreetMap extract for map display.

This is a read-only bounded fallback for OAP's local map. It never fabricates
roads, imports data over the network, or claims a routable/navigation graph.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

_SOURCE_PATH = Path(__file__).resolve().parents[1] / "static" / "tda_london" / "map_data.js"
_PREFIX = "window.TDA_MITCHAM_OSM ="
_MAX_SOURCE_BYTES = 24 * 1024 * 1024
_MAX_FEATURES = 10000
_MAX_LINES = 450


class LocalRoadsUnavailable(ValueError):
    """Imported OSM road geometry is unavailable or cannot be validated."""


def _point(value: object) -> list[float] | None:
    lon: object
    lat: object
    if isinstance(value, dict):
        lon = value.get("lon", value.get("longitude"))
        lat = value.get("lat", value.get("latitude"))
    elif isinstance(value, (tuple, list)) and len(value) >= 2:
        a, b = value[:2]
        if type(a) not in (float, int) or type(b) not in (float, int):
            return None
        # The Founder import may use [lat, lon] or GeoJSON [lon, lat].
        if 48 < a < 62 and -9 < b < 4:
            lon, lat = b, a
        else:
            lon, lat = a, b
    else:
        return None
    if type(lon) not in (int, float) or type(lat) not in (int, float):
        return None
    if not math.isfinite(lon) or not math.isfinite(lat):
        return None
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return None
    return [float(lon), float(lat)]


def _line(raw: object) -> list[list[float]]:
    if not isinstance(raw, list) or len(raw) < 2:
        return []
    points = [_point(node) for node in raw[:1200]]
    if any(p is None for p in points):
        return []
    return [p for p in points if p is not None]


def _geometry(feature: dict) -> list[list[list[float]]]:
    raw = feature.get("geometry", feature.get("coordinates", feature.get("points")))
    if raw is None:
        raw = feature.get("path", feature.get("nodes"))
    if isinstance(raw, dict):
        kind = str(raw.get("type") or "").lower()
        raw = raw.get("coordinates", raw.get("points"))
        if kind == "multilinestring" and isinstance(raw, list):
            return [line for part in raw[:8] if (line := _line(part))]
    line = _line(raw)
    if line:
        return [line]
    if isinstance(raw, list):
        return [line for part in raw[:8] if (line := _line(part))]
    return []


def _load() -> dict:
    try:
        if _SOURCE_PATH.stat().st_size > _MAX_SOURCE_BYTES:
            raise LocalRoadsUnavailable("local_osm_file_too_large")
        raw = _SOURCE_PATH.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError) as exc:
        raise LocalRoadsUnavailable("local_osm_not_installed") from exc
    if not raw.startswith(_PREFIX):
        raise LocalRoadsUnavailable("local_osm_format_unknown")
    data = raw[len(_PREFIX):].strip().removesuffix(";").strip()
    try:
        result = json.loads(data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise LocalRoadsUnavailable("local_osm_invalid_json") from exc
    if not isinstance(result, dict) or not isinstance(result.get("features"), list):
        raise LocalRoadsUnavailable("local_osm_features_missing")
    if len(result["features"]) > _MAX_FEATURES:
        raise LocalRoadsUnavailable("local_osm_features_excessive")
    source = str(result.get("source") or "").lower()
    if not any(name in source for name in ("openstreetmap", "osm")):
        raise LocalRoadsUnavailable("local_osm_provenance_missing")
    return result


def road_lines(*, west: float, south: float, east: float, north: float) -> dict:
    numbers = (west, south, east, north)
    if any(type(n) not in (int, float) or not math.isfinite(n) for n in numbers):
        raise LocalRoadsUnavailable("invalid_bounds")
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise LocalRoadsUnavailable("invalid_bounds")
    if east - west > 0.30 or north - south > 0.30:
        raise LocalRoadsUnavailable("bounds_too_large")
    imported = _load()
    lines: list[dict] = []
    for feature in imported["features"]:
        if not isinstance(feature, dict) or feature.get("kind") != "road":
            continue
        props = feature.get("properties")
        props = props if isinstance(props, dict) else {}
        name = str(feature.get("name") or props.get("name") or "").strip()[:95]
        road_class = str(
            feature.get("highway") or feature.get("class") or props.get("highway") or ""
        ).strip()[:30]
        for points in _geometry(feature):
            if not points:
                continue
            xlo = min(p[0] for p in points)
            xhi = max(p[0] for p in points)
            ylo = min(p[1] for p in points)
            yhi = max(p[1] for p in points)
            if xhi < west or xlo > east or yhi < south or ylo > north:
                continue
            # Limit response size; this is a display overlay, not routing data.
            stride = max(1, (len(points) + 159) // 160)
            shown = points[::stride]
            if shown[-1] != points[-1]:
                shown.append(points[-1])
            lines.append({"points": shown, "name": name, "class": road_class})
            if len(lines) >= _MAX_LINES:
                break
        if len(lines) >= _MAX_LINES:
            break
    if not lines:
        raise LocalRoadsUnavailable("no_valid_local_roads_in_view")
    return {
        "source": "existing_tda_osm_import",
        "provenance": str(imported.get("source"))[:120],
        "extracted_at": str(imported.get("extractedAt") or "")[:40],
        "coverage": "central_mitcham_only",
        "routing_verified": False,
        "live_traffic_verified": False,
        "road_count": len(lines),
        "lines": lines,
    }
