from mission_control import music_rank


class _Result:
    def fetchall(self):
        return [
            (
                "11111111-1111-4111-8111-111111111111",
                "Track A",
                "22222222-2222-4222-8222-222222222222",
                "Release A",
                10,
                4,
                2,
                500,
            ),
            (
                "33333333-3333-4333-8333-333333333333",
                "Track B",
                "44444444-4444-4444-8444-444444444444",
                "Release B",
                5,
                3,
                1,
                0,
            ),
        ]


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        return _Result()


def test_rank_uses_qualified_unique_radio_and_reconciled_value(monkeypatch):
    monkeypatch.setattr(music_rank.postgres_db, "connect", lambda **kwargs: _Connection())
    result = music_rank.track_rank("55555555-5555-4555-8555-555555555555")
    assert result["raw_views_used"] is False
    assert result["paid_promotion_used"] is False
    assert result["queued_radio_used"] is False
    assert result["external_metrics_used"] is False
    assert result["items"][0]["track_title"] == "Track A"
    assert result["items"][0]["position"] == 1
    assert result["items"][0]["rank_score"] == 25
