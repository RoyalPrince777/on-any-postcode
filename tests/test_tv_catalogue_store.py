"""OAP TV SQLite private catalogue: owner isolation and no playback claims."""
from uuid import uuid4

import pytest

from mission_control.tv_catalogue_store import PrivateCatalogueError, PrivateTvCatalogueStore


def draft(kind="film", **extra):
    return {"item_id": str(uuid4()), "kind": kind, "title": "Original film", **extra}


def test_durable_owner_scoped_drafts_across_store_instances(tmp_path):
    db = tmp_path / "oap_tv.sqlite3"
    store = PrivateTvCatalogueStore(db)
    first = store.save_draft("creator_A", draft())
    assert first["published"] is False
    recovered = PrivateTvCatalogueStore(db).list_drafts("creator_A")
    assert recovered["item_count"] == 1
    assert recovered["items"][0]["title"] == "Original film"
    assert recovered["items"][0]["playback_enabled"] is False
    assert PrivateTvCatalogueStore(db).list_drafts("creator_B")["item_count"] == 0


def test_submitted_flags_cannot_grant_playback(tmp_path):
    store = PrivateTvCatalogueStore(tmp_path / "tv.sqlite3")
    item = store.save_draft("founder", {**draft(), "rights_verified": True,
                            "published": True, "playback_enabled": True,
                            "playback_url": "https://external.invalid/video"})
    assert item["published"] is False
    result = store.list_drafts("founder")["items"][0]
    assert result["rights_verified"] is False
    assert result["playback_url"] is None


@pytest.mark.parametrize("owner", ["", "../outside", "a/b", " space ", "x" * 129])
def test_invalid_owner_denied(tmp_path, owner):
    store = PrivateTvCatalogueStore(tmp_path / "tv.sqlite3")
    with pytest.raises(PrivateCatalogueError):
        store.save_draft(owner, draft())
    with pytest.raises(PrivateCatalogueError):
        store.list_drafts(owner)


def test_episode_links_survive_persistence(tmp_path):
    store = PrivateTvCatalogueStore(tmp_path / "tv.sqlite3")
    series_id = str(uuid4())
    store.save_draft("owner", {"item_id": series_id, "kind": "series", "title": "Seasoned"})
    store.save_draft("owner", draft("episode", series_id=series_id, season=2, episode=3))
    episodes = [i for i in store.list_drafts("owner")["items"] if i["kind"] == "episode"]
    assert len(episodes) == 1
    assert episodes[0]["series_id"] == f"oap:tv:{series_id}"


def test_invalid_draft_not_written(tmp_path):
    store = PrivateTvCatalogueStore(tmp_path / "tv.sqlite3")
    with pytest.raises(PrivateCatalogueError):
        store.save_draft("owner", {"title": "Missing id"})
    assert store.list_drafts("owner")["item_count"] == 0
