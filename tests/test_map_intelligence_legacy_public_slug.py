from mission_control.map_intelligence import CANONICAL_PUBLIC_SLUG, RETIRED_PUBLIC_SLUGS
from mission_control.products import PUBLIC_SPOT_CAPABILITIES


def test_duplicate_movement_delivery_surface_is_retired():
    slugs = {item["slug"] for item in PUBLIC_SPOT_CAPABILITIES}
    assert CANONICAL_PUBLIC_SLUG in slugs
    assert set(RETIRED_PUBLIC_SLUGS).isdisjoint(slugs)
