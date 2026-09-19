"""Decode OAP-owned OSRM vector tiles into lightweight road line geometry.

This module never calls public/demo map services. It consumes the first-party
routing tile adapter and returns bounded linework for the Map Intelligence UI.
"""
from __future__ import annotations

from typing import Any

import mapbox_vector_tile

from . import routing

MAX_LINES = 600
MAX_POINTS_PER_LINE = 512


def _line_parts(geometry: dict[str, Any]) -> list[list[list[float]]]:
    kind = geometry.get("type")
    coords = geometry.get("coordinates")
    if kind == "LineString" and isinstance(coords, list):
        return [coords]
    if kind == "MultiLineString" and isinstance(coords, list):
        return [part for part in coords if isinstance(part, list)]
    return []


def tile_lines(*, x: object, y: object, zoom: object, profile: object = "driving") -> dict[str, object]:
    body, _ = routing.road_tile(x=x, y=y, zoom=zoom, profile=profile)
    try:
        decoded = mapbox_vector_tile.decode(body, default_options={"y_coord_down": True})
    except Exception as exc:  # decoder boundary: fail closed to a generic code
        raise routing.RoutingUnavailable("road_tile_decode_failed") from exc

    lines: list[dict[str, object]] = []
    for layer_name, layer in decoded.items():
        if not isinstance(layer, dict):
            continue
        extent = float(layer.get("extent") or 4096)
        if extent <= 0:
            continue
        features = layer.get("features")
        if not isinstance(features, list):
            continue
        for feature in features:
            if not isinstance(feature, dict):
                continue
            geometry = feature.get("geometry")
            if not isinstance(geometry, dict):
                continue
            props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
            for part in _line_parts(geometry):
                points: list[list[float]] = []
                for point in part[:MAX_POINTS_PER_LINE]:
                    if not isinstance(point, (list, tuple)) or len(point) < 2:
                        continue
                    try:
                        px = float(point[0]) / extent
                        py = float(point[1]) / extent
                    except (TypeError, ValueError):
                        continue
                    if -0.25 <= px <= 1.25 and -0.25 <= py <= 1.25:
                        points.append([round(px, 6), round(py, 6)])
                if len(points) >= 2:
                    road_name = str(
                        props.get("name")
                        or props.get("ref")
                        or props.get("road_name")
                        or ""
                    ).strip()[:96]
                    road_class = str(
                        props.get("class")
                        or props.get("highway")
                        or props.get("road_class")
                        or layer_name
                        or ""
                    ).strip()[:40]
                    lines.append({
                        "points": points,
                        "layer": str(layer_name)[:40],
                        "name": road_name,
                        "class": road_class,
                        "speed": props.get("speed"),
                        "is_small": props.get("is_small"),
                    })
                if len(lines) >= MAX_LINES:
                    break
            if len(lines) >= MAX_LINES:
                break
        if len(lines) >= MAX_LINES:
            break

    return {
        "tile": {"x": int(x), "y": int(y), "z": int(zoom)},
        "lines": lines,
        "line_count": len(lines),
        "source": "OAP-owned routing graph",
        "first_party": True,
        "read_only": True,
    }
