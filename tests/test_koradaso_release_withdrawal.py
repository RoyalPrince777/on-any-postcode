"""Release revocation must atomically withdraw public projections."""
import inspect

from mission_control import koradaso_releases

SOURCE = inspect.getsource(koradaso_releases.revoke_release)


def test_revocation_withdraws_existing_publications_in_same_transaction():
    assert "UPDATE koradaso_publications" in SOURCE
    assert "WHERE claim_id=%s AND revoked_at IS NULL" in SOURCE
    assert SOURCE.index("UPDATE koradaso_publications") < SOURCE.index(
        "KORADASO_HERITAGE_RELEASE_REVOKED"
    ) < SOURCE.index("connection.commit()")


def test_revocation_never_deletes_history():
    assert "DELETE FROM koradaso_publications" not in SOURCE
    assert "DELETE FROM koradaso_release_consents" not in SOURCE
