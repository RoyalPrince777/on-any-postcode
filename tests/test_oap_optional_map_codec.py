"""Native road-tile decoder absence cannot prevent Home V2 and Store startup."""
from __future__ import annotations

import builtins

import pytest

from mission_control import road_tile_geometry, routing


def test_road_geometry_fails_closed_if_mapbox_decoder_is_unavailable(monkeypatch):
    original_import = builtins.__import__

    def missing_decoder(name, *args, **kwargs):
        if name == "mapbox_vector_tile":
            raise ModuleNotFoundError("No module named 'mapbox_vector_tile'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_decoder)

    with pytest.raises(routing.RoutingUnavailable, match="road_tile_decoder_unavailable"):
        road_tile_geometry.tile_lines(x=0, y=0, zoom=0)


def test_road_geometry_module_can_load_without_decoder_at_import_time():
    assert callable(road_tile_geometry.tile_lines)
