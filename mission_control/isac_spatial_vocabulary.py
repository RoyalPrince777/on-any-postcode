"""Canonical human-facing spatial vocabulary for OAP ISAC / Digital Twin.

This module separates human geography from technical networking language.
`node` may remain an internal implementation/networking term, but OAP surfaces
should describe the spatial model with Spot, Point, Signal, Spatial Cell and Grid.
"""

from __future__ import annotations

from typing import Final

SPATIAL_VOCABULARY: Final[dict[str, dict[str, str]]] = {
    "spot": {
        "label": "Spot",
        "meaning": "Meaningful local or community place in OAP World.",
    },
    "point": {
        "label": "Point",
        "meaning": "Precise coordinate, entrance, landmark or feature associated with a Spot.",
    },
    "signal": {
        "label": "Signal",
        "meaning": "Connectivity or sensing presence associated with a location.",
    },
    "spatial_cell": {
        "label": "Spatial Cell",
        "meaning": "Bounded unit of space used by the Digital ISAC Twin for calculation.",
    },
    "grid": {
        "label": "Grid",
        "meaning": "Collection of Spatial Cells covering a larger modelled area.",
    },
}

# Telecom radio cells remain distinct from Digital Twin Spatial Cells.
RADIO_CELL_LABEL: Final[str] = "Radio Cell"
TECHNICAL_NODE_POLICY: Final[str] = (
    "Node is technical-only for networking/computing implementation; do not use it "
    "as the human-facing OAP place label."
)


def isac_spatial_vocabulary_status() -> dict[str, object]:
    """Expose the canonical vocabulary without making runtime/RF claims."""

    return {
        "id": "isac_spatial_vocabulary",
        "canonical": True,
        "human_facing_terms": tuple(item["label"] for item in SPATIAL_VOCABULARY.values()),
        "spot": "place",
        "point": "position",
        "signal": "connectivity_or_sensing_presence",
        "spatial_cell": "bounded_space",
        "grid": "spatial_system",
        "radio_cell_label": RADIO_CELL_LABEL,
        "node_policy": TECHNICAL_NODE_POLICY,
        "digital_twin_order": ("Spot", "Grid", "Spatial Cell", "Point", "Signal"),
        "physical_rf_claim": False,
    }
