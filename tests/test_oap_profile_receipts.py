import hashlib
import hmac
import json

import pytest
from mission_control.oap_profile_receipts import OapProfileReceiptVerifier


KEY = b"x" * 32


def signed(operation="prepare", profile_ref="oap-profile-1", receipt_id="r-1"):
    message = json.dumps(
        {"operation": operation, "profile_ref": profile_ref, "receipt_id": receipt_id},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return {
        "operation": operation,
        "profile_ref": profile_ref,
        "receipt_id": receipt_id,
        "signature": hmac.new(KEY, message, hashlib.sha256).hexdigest(),
    }


def test_valid_scoped_backend_receipt():
    verifier = OapProfileReceiptVerifier(verification_key=KEY)
    assert verifier.verify(receipt=signed(), operation="prepare", profile_ref="oap-profile-1") == "r-1"


def test_rejects_forged_or_wrong_scope_receipt():
    verifier = OapProfileReceiptVerifier(verification_key=KEY)
    forged = signed()
    forged["receipt_id"] = "forged"
    with pytest.raises(PermissionError):
        verifier.verify(receipt=forged, operation="prepare", profile_ref="oap-profile-1")
    with pytest.raises(ValueError):
        verifier.verify(receipt=signed(), operation="revoke", profile_ref="oap-profile-1")


def test_rejects_secret_fields_and_short_key():
    with pytest.raises(ValueError):
        OapProfileReceiptVerifier(verification_key=b"weak")
    verifier = OapProfileReceiptVerifier(verification_key=KEY)
    with pytest.raises(ValueError):
        verifier.verify(receipt={**signed(), "ki": "forbidden"}, operation="prepare", profile_ref="oap-profile-1")
