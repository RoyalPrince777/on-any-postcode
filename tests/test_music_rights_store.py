from mission_control import music_rights_store

OWNER = "11111111-1111-4111-8111-111111111111"
ASSET = "22222222-2222-4222-8222-222222222222"
GRANT = "33333333-3333-4333-8333-333333333333"


def test_music_rights_schema_is_persistent_owner_scoped_and_revocable():
    joined = "\n".join(music_rights_store.SCHEMA_STATEMENTS)
    assert music_rights_store.MUSIC_RIGHTS_MIGRATION_VERSION == "0014_oap_music_rights_grants"
    assert "oap_music_rights_grants" in joined
    assert "owner_identity_id UUID NOT NULL" in joined
    assert "asset_id UUID NOT NULL REFERENCES oap_music_assets" in joined
    assert "authority_verified BOOLEAN NOT NULL DEFAULT FALSE" in joined
    assert "human_approved BOOLEAN NOT NULL DEFAULT FALSE" in joined
    assert "revoked BOOLEAN NOT NULL DEFAULT FALSE" in joined


def test_creator_review_grant_cannot_self_certify_authority_or_human_approval():
    grant = music_rights_store._draft_grant(
        grant_id=GRANT,
        asset_id=ASSET,
        owner_identity_id=OWNER,
        grantor_reference="Creator claim under review",
        right_type="recording",
        permitted_uses=["stream"],
        territories=["GB"],
        permitted_channels=["OAP Music"],
        evidence_hashes=["a" * 64],
    )
    assert grant["authority_verified"] is False
    assert grant["authority_receipt_hash"] is None
    assert grant["human_approved"] is False
    assert grant["human_approval_receipt_hash"] is None
    assert grant["revoked"] is False


def test_review_grant_rejects_invalid_scope_before_persistence():
    try:
        music_rights_store._draft_grant(
            grant_id=GRANT,
            asset_id=ASSET,
            owner_identity_id=OWNER,
            grantor_reference="Review",
            right_type="recording",
            permitted_uses=["broadcast"],
            territories=["GB"],
            permitted_channels=["OAP Music"],
            evidence_hashes=["a" * 64],
        )
    except ValueError as exc:
        assert str(exc) == "right_type_use_mismatch"
    else:
        raise AssertionError("invalid right/use scope must fail closed")


def test_review_grant_has_no_playback_or_public_catalogue_authority():
    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, params=()):
            self.sql = sql
            if "SELECT 1 FROM oap_music_assets" in sql:
                return Result((1,))
            if "SELECT evidence_sha256 FROM oap_music_evidence_receipts" in sql:
                return Result([("a" * 64,)], many=True)
            if "INSERT INTO oap_music_rights_grants" in sql:
                return Result(None)
            return Result(None)
        def commit(self):
            return None

    class Result:
        def __init__(self, row, many=False):
            self.row = row
            self.many = many
        def fetchone(self):
            return self.row
        def fetchall(self):
            return self.row if self.many else []

    original = music_rights_store.postgres_db.connect
    music_rights_store.postgres_db.connect = lambda **_kwargs: Connection()
    try:
        result = music_rights_store.MusicRightsStore().create_review_grant(
            owner_identity_id=OWNER,
            release_id="44444444-4444-4444-8444-444444444444",
            asset_id=ASSET,
            grantor_reference="Creator claim under review",
            right_type="recording",
            permitted_uses=["stream"],
            territories=["GB"],
            permitted_channels=["OAP Music"],
            evidence_hashes=["a" * 64],
        )
    finally:
        music_rights_store.postgres_db.connect = original

    assert result["review_state"] == "REVIEW_REQUIRED"
    assert result["authority_verified"] is False
    assert result["human_approved"] is False
    assert result["playback_authorized"] is False
    assert result["public_catalogue_enabled"] is False


def test_review_receipt_hash_is_deterministic_and_never_authorizes_playback():
    payload = music_rights_store._review_receipt_payload(
        receipt_id="55555555-5555-4555-8555-555555555555",
        grant_id=GRANT,
        asset_id=ASSET,
        owner_identity_id=OWNER,
        reviewer_identity_id="66666666-6666-4666-8666-666666666666",
        review_kind="AUTHORITY",
        evidence_hashes=["a" * 64],
        decision="APPROVE",
    )
    first = music_rights_store._review_receipt_hash(payload)
    second = music_rights_store._review_receipt_hash(dict(payload))
    assert first == second
    assert len(first) == 64
    assert payload["playback_authorized"] is False
    assert payload["public_catalogue_enabled"] is False


def test_owner_cannot_act_as_independent_rights_reviewer():
    store = music_rights_store.MusicRightsStore()
    try:
        store.record_authority_review(
            owner_identity_id=OWNER,
            grant_id=GRANT,
            reviewer_identity_id=OWNER,
            evidence_hashes=["a" * 64],
            approved=True,
        )
    except PermissionError as exc:
        assert str(exc) == "independent_reviewer_required"
    else:
        raise AssertionError("owner self-review must fail closed")


def test_review_schema_persists_authority_and_human_approval_receipts():
    joined = "\n".join(music_rights_store.SCHEMA_STATEMENTS)
    assert "oap_music_rights_review_receipts" in joined
    assert "AUTHORITY" in joined
    assert "HUMAN_APPROVAL" in joined
    assert "reviewer_identity_id UUID NOT NULL" in joined
    assert "receipt_hash CHAR(64) NOT NULL UNIQUE" in joined
