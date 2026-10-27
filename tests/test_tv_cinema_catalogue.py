"""OAP TV catalogue tests: draft metadata is never a media licence."""
from uuid import uuid4

from mission_control.tv_cinema_catalogue import catalogue_item, private_catalogue


def valid(kind="film", **extras):
    return {"item_id": str(uuid4()), "kind": kind, "title": " OAP Original ",
            **extras}


def test_films_and_creator_videos_are_unpublished_drafts():
    for kind in ("film", "documentary", "creator_video", "live", "series"):
        record = catalogue_item({**valid(kind), "published": True,
                                 "rights_verified": True, "playback_url": "https://bad.invalid/"})
        assert record["title"] == "OAP Original"
        assert record["published"] is False
        assert record["rights_verified"] is False
        assert record["playback_enabled"] is False
        assert record["playback_url"] is None


def test_episode_requires_bounded_series_season_and_number():
    good = valid("episode", series_id=str(uuid4()), season=2, episode=4)
    record = catalogue_item(good)
    assert record["season"] == 2
    assert record["episode"] == 4
    for change in ({"series_id": "../outside"}, {"season": True},
                   {"episode": 0}, {"season": 1000}, {"episode": "4"}):
        assert catalogue_item({**good, **change}) is None


def test_rejects_untrusted_kind_and_identifier():
    assert catalogue_item(valid("external_stream")) is None
    assert catalogue_item({**valid(), "item_id": "../../secret"}) is None
    assert catalogue_item({**valid(), "title": " "}) is None


def test_catalogue_deduplicates_and_never_claims_publication():
    row = valid()
    result = private_catalogue([row, row, {"invalid": True}])
    assert result["item_count"] == 1
    assert result["public_catalogue_enabled"] is False
    assert result["playback_enabled"] is False
    assert result["asset_import_performed"] is False


def test_series_episodes_orders_seasons_without_publishing():
    from mission_control.tv_cinema_catalogue import series_episodes

    series_id = str(uuid4())
    other_id = str(uuid4())
    rows = [
        valid("episode", series_id=series_id, season=2, episode=3),
        valid("episode", series_id=other_id, season=1, episode=1),
        valid("episode", series_id=series_id, season=1, episode=9),
        valid("episode", series_id=series_id, season=1, episode=2),
    ]
    result = series_episodes(rows, series_id)
    assert [(x["season"], x["episode"]) for x in result["episodes"]] == [
        (1, 2), (1, 9), (2, 3)
    ]
    assert result["episode_count"] == 3
    assert result["playback_enabled"] is False
    assert result["public_catalogue_enabled"] is False


def test_series_episodes_rejects_invalid_series_id():
    from mission_control.tv_cinema_catalogue import series_episodes

    result = series_episodes([], "../invalid")
    assert result["episode_count"] == 0
    assert result["playback_enabled"] is False


def test_private_shelves_group_only_real_draft_records():
    from mission_control.tv_cinema_catalogue import private_shelves

    rows = [valid("film"), valid("documentary"), valid("series"),
            valid("creator_video"), valid("live"), {"title": "invalid"}]
    result = private_shelves(rows)
    assert {key: len(value) for key, value in result["shelves"].items()} == {
        "cinema": 2, "series": 1, "channels": 1, "live": 1,
    }
    assert result["item_count"] == 5
    assert result["playback_enabled"] is False
    assert result["public_catalogue_enabled"] is False
    assert all(not item["published"] and not item["playback_enabled"]
               for shelf in result["shelves"].values() for item in shelf)


def test_private_shelves_empty_without_approved_drafts():
    from mission_control.tv_cinema_catalogue import private_shelves

    result = private_shelves([{"kind": "film", "title": "invented"}])
    assert result["item_count"] == 0
    assert all(not contents for contents in result["shelves"].values())


def test_private_shelves_hide_orphan_episodes():
    from mission_control.tv_cinema_catalogue import private_shelves

    parent = str(uuid4())
    other = str(uuid4())
    rows = [
        {**valid("series"), "item_id": parent},
        valid("episode", series_id=parent, season=1, episode=1),
        valid("episode", series_id=other, season=1, episode=2),
    ]
    result = private_shelves(rows)
    assert [item["kind"] for item in result["shelves"]["series"]] == [
        "series", "episode",
    ]
    assert result["item_count"] == 2  # Orphan episodes are not counted as visible.
    assert result["playback_enabled"] is False
