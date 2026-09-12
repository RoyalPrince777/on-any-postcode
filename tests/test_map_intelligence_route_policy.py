from mission_control.map_intelligence import CANONICAL_PUBLIC_SLUG, RETIRED_PUBLIC_SLUGS


def test_map_intelligence_has_one_canonical_public_slug():
    assert CANONICAL_PUBLIC_SLUG == "maps-weather-travel"
    assert CANONICAL_PUBLIC_SLUG not in RETIRED_PUBLIC_SLUGS
    assert RETIRED_PUBLIC_SLUGS == ("movement-delivery",)
