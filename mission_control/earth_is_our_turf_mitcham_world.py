"""Mitcham world catalogue for EARTH IS OUR TURF.

Public roads/areas are recognisable anchors. Fine-grained cuts, estate passages,
private access, security and surveillance geometry are deliberately fictionalised
unless a separate public-map proof marks them verified.
"""
from __future__ import annotations

from typing import Any

CHUNKS = {
    "central": {
        "label": "Mitcham Central",
        "anchors": ["town-centre", "figges-marsh", "cricket-green"],
        "detail_status": "recognisable_public_anchor_seed",
    },
    "lavender": {
        "label": "Lavender",
        "anchors": ["lavender-avenue", "lavender-park", "western-road", "mount-road"],
        "detail_status": "recognisable_public_anchor_seed",
    },
    "phipps": {
        "label": "Phipps Bridge",
        "anchors": ["phipps-bridge", "phipps-bridge-road", "wandle-path"],
        "detail_status": "recognisable_public_anchor_seed",
    },
    "eastfields": {
        "label": "Eastfields + Laburnum",
        "anchors": ["eastfields", "laburnum-road", "st-marks-road", "armfield-crescent"],
        "detail_status": "recognisable_public_anchor_seed",
    },
    "southwest": {
        "label": "Lower Mitcham + Ravensbury",
        "anchors": ["ravensbury", "lower-mitcham", "junction"],
        "detail_status": "recognisable_public_anchor_seed",
    },
    "common": {
        "label": "Mitcham Common",
        "anchors": ["mitcham-common", "common-trail"],
        "detail_status": "recognisable_public_anchor_seed",
    },
    "pollards": {
        "label": "Pollards Hill",
        "anchors": ["pollards-hill"],
        "detail_status": "recognisable_public_anchor_seed",
    },
}

NODES = (
    {"id":"town-centre","label":"Mitcham Town Centre","kind":"centre","chunk":"central"},
    {"id":"figges-marsh","label":"Figge's Marsh","kind":"park","chunk":"central"},
    {"id":"cricket-green","label":"Cricket Green","kind":"neighbourhood","chunk":"central"},
    {"id":"market-lane","label":"Market Lane","kind":"alley","chunk":"central","fictional_detail":True},
    {"id":"marsh-path","label":"Marsh Path","kind":"footpath","chunk":"central","fictional_detail":True},

    {"id":"lavender-avenue","label":"Lavender Avenue","kind":"road","chunk":"lavender"},
    {"id":"lavender-park","label":"Lavender Park","kind":"park","chunk":"lavender"},
    {"id":"western-road","label":"Western Road","kind":"road","chunk":"lavender"},
    {"id":"mount-road","label":"Mount Road","kind":"road","chunk":"lavender"},
    {"id":"lavender-cut","label":"Lavender Cut","kind":"alley","chunk":"lavender","fictional_detail":True},

    {"id":"phipps-bridge","label":"Phipps Bridge","kind":"neighbourhood","chunk":"phipps"},
    {"id":"phipps-bridge-road","label":"Phipps Bridge Road","kind":"road","chunk":"phipps"},
    {"id":"wandle-path","label":"Wandle Path","kind":"footpath","chunk":"phipps"},
    {"id":"phipps-cut","label":"Phipps Cut","kind":"alley","chunk":"phipps","fictional_detail":True},

    {"id":"eastfields","label":"Mitcham Eastfields","kind":"transport","chunk":"eastfields"},
    {"id":"laburnum-road","label":"Laburnum Road","kind":"estate-road","chunk":"eastfields"},
    {"id":"st-marks-road","label":"St Mark's Road","kind":"road","chunk":"eastfields"},
    {"id":"armfield-crescent","label":"Armfield Crescent","kind":"road","chunk":"eastfields"},
    {"id":"estate-cut","label":"Estate Cut","kind":"alley","chunk":"eastfields","fictional_detail":True},

    {"id":"ravensbury","label":"Ravensbury Park","kind":"park","chunk":"southwest"},
    {"id":"lower-mitcham","label":"Lower Mitcham","kind":"neighbourhood","chunk":"southwest"},
    {"id":"junction","label":"Mitcham Junction","kind":"transport","chunk":"southwest"},

    {"id":"mitcham-common","label":"Mitcham Common","kind":"park","chunk":"common"},
    {"id":"common-trail","label":"Common Trail","kind":"footpath","chunk":"common","fictional_detail":True},

    {"id":"pollards-hill","label":"Pollards Hill","kind":"estate","chunk":"pollards"},
)

# Connectivity is a gameplay approximation joining recognisable public anchors.
# "alley" entries and any exact fine geometry are fictional game shortcuts.
NAV_LINKS = (
    ("town-centre","figges-marsh","road",650,("car","bike","foot")),
    ("town-centre","cricket-green","road",720,("car","bike","foot")),
    ("town-centre","western-road","road",900,("car","bike","foot")),
    ("western-road","lavender-avenue","road",520,("car","bike","foot")),
    ("lavender-avenue","lavender-park","road",260,("car","bike","foot")),
    ("lavender-avenue","mount-road","road",500,("car","bike","foot")),
    ("mount-road","phipps-bridge-road","road",650,("car","bike","foot")),
    ("phipps-bridge-road","phipps-bridge","road",420,("car","bike","foot")),
    ("phipps-bridge","wandle-path","footpath",240,("bike","foot")),
    ("town-centre","eastfields","road",900,("car","bike","foot")),
    ("eastfields","laburnum-road","road",280,("car","bike","foot")),
    ("laburnum-road","st-marks-road","road",430,("car","bike","foot")),
    ("st-marks-road","armfield-crescent","road",380,("car","bike","foot")),
    ("armfield-crescent","town-centre","road",880,("car","bike","foot")),
    ("eastfields","pollards-hill","road",1300,("car","bike","foot")),
    ("cricket-green","ravensbury","road",1050,("car","bike","foot")),
    ("ravensbury","lower-mitcham","road",850,("car","bike","foot")),
    ("lower-mitcham","junction","road",1100,("car","bike","foot")),
    ("lower-mitcham","mitcham-common","road",1250,("car","bike","foot")),
    ("mitcham-common","pollards-hill","road",1800,("car","bike","foot")),

    ("town-centre","market-lane","alley",210,("bike","foot")),
    ("market-lane","figges-marsh","alley",310,("bike","foot")),
    ("figges-marsh","marsh-path","footpath",260,("bike","foot")),
    ("marsh-path","cricket-green","footpath",420,("bike","foot")),

    ("lavender-avenue","lavender-cut","alley",170,("bike","foot")),
    ("lavender-cut","lavender-park","alley",190,("bike","foot")),
    ("phipps-bridge","phipps-cut","alley",160,("bike","foot")),
    ("phipps-cut","wandle-path","alley",150,("bike","foot")),

    ("eastfields","estate-cut","alley",220,("bike","foot")),
    ("estate-cut","laburnum-road","alley",180,("bike","foot")),
    ("mitcham-common","common-trail","footpath",500,("bike","foot")),
    ("common-trail","ravensbury","footpath",760,("bike","foot")),
)

def node_row(node_id: str) -> dict[str, Any]:
    for row in NODES:
        if row["id"] == node_id:
            return row
    raise ValueError("eiot_node_invalid")

def chunk_for(node_id: str) -> str:
    return str(node_row(node_id)["chunk"])

def streamed_chunks(current_chunk: str, route_nodes: list[str] | None = None) -> list[str]:
    """Keep current + route-adjacent chunks loaded, capped for mobile memory."""
    ordered=[current_chunk]
    for node_id in route_nodes or []:
        chunk=chunk_for(node_id)
        if chunk not in ordered:
            ordered.append(chunk)
    # preserve one central overview chunk as a navigation bridge
    if "central" not in ordered:
        ordered.append("central")
    return ordered[:4]

def environment_state(*, node_id: str, minute: int, day: int) -> dict[str, Any]:
    """Deterministic game environment, explicitly not live-world telemetry."""
    row=node_row(node_id)
    hour=(minute//60)%24
    kind=row["kind"]
    daylight=7 <= hour < 19
    commute=7 <= hour < 10 or 16 <= hour < 19
    late=hour >= 22 or hour < 5

    traffic=75 if commute and kind in {"road","transport","centre"} else 48 if kind in {"road","centre"} else 18
    footfall=82 if 11 <= hour < 19 and kind in {"centre","transport"} else 62 if kind in {"park","neighbourhood","estate-road"} and daylight else 24
    park_activity=78 if kind in {"park","footpath"} and 9 <= hour < 20 else 12 if kind in {"park","footpath"} else 0
    shop_activity=80 if kind in {"centre","road","transport"} and 8 <= hour < 20 else 20
    lighting="daylight" if daylight else "street-lit"
    soundscape="commute" if commute else "quiet-night" if late else "urban-day"

    return {
        "source":"game_environment_simulation_v1",
        "live_claim":False,
        "node":node_id,
        "chunk":row["chunk"],
        "day":day,
        "hour":hour,
        "traffic":traffic,
        "footfall":footfall,
        "park_activity":park_activity,
        "shop_activity":shop_activity,
        "lighting":lighting,
        "soundscape":soundscape,
        "weather":"dry_seed",
        "visibility":"normal" if daylight else "reduced",
    }
