"""Identity-collision regression for inert OAP Music candidate intelligence."""
from uuid import uuid4

from mission_control.open_music_intake import private_catalogue_intelligence


def _lead(uid, page):
    return {
        "candidate_id": uid,
        "title": "Independent track",
        "artist": "Independent artist",
        "source_kind": "internet_archive",
        "claimed_licence": "CC_BY",
        "source_page_url": page,
    }


def test_distinct_source_pages_cannot_duplicate_one_candidate_identity():
    uid = str(uuid4())
    first = _lead(uid, "https://archive.org/details/track-one")
    second = _lead(uid, "https://archive.org/details/track-two")
    result = private_catalogue_intelligence([first, second])
    assert result["review_count"] == 1
    assert result["review_queue"][0]["source_page_url"] == first["source_page_url"]
    assert result["rights_verified"] is False
    assert result["playback_enabled"] is False
    assert result["catalogue_write_performed"] is False


def test_distinct_candidate_ids_can_retain_distinct_source_pages():
    first = _lead(str(uuid4()), "https://archive.org/details/track-one")
    second = _lead(str(uuid4()), "https://archive.org/details/track-two")
    result = private_catalogue_intelligence([first, second])
    assert result["review_count"] == 2
    assert all(row["human_release_approved"] is False for row in result["review_queue"])
    assert all(row["playback_enabled"] is False for row in result["review_queue"])
