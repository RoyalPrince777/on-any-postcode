"""Strict non-secret receipt verification for an isolated OAP profile backend.

A receipt is not GSMA certification or proof of eUICC installation. This
component validates only a configured backend's signed operation statement.
"""
from __future__ import annotations

import hashlib
import hmac
import json


class OapProfileReceiptVerifier:
    def __init__(self, *, verification_key: bytes) -> None:
        if not verification_key or len(verification_key) < 32:
            raise ValueError("backend_verification_key_required")
        self._key = verification_key

    def verify(self, *, receipt: dict, operation: str, profile_ref: str) -> str:
        if not isinstance(receipt, dict):
            raise TypeError("invalid_backend_receipt")
        expected = {"operation", "profile_ref", "receipt_id", "signature"}
        if set(receipt) != expected:
            raise ValueError("unexpected_backend_receipt_fields")
        if receipt["operation"] != operation or receipt["profile_ref"] != profile_ref:
            raise ValueError("backend_receipt_scope_mismatch")
        receipt_id = receipt["receipt_id"]
        if not isinstance(receipt_id, str) or not receipt_id.strip():
            raise ValueError("backend_receipt_id_required")
        signature = receipt["signature"]
        if not isinstance(signature, str) or len(signature) != 64:
            raise ValueError("invalid_backend_receipt_signature")
        message = json.dumps(
            {"operation": operation, "profile_ref": profile_ref, "receipt_id": receipt_id},
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        expected_signature = hmac.new(self._key, message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise PermissionError("backend_receipt_signature_invalid")
        return receipt_id
