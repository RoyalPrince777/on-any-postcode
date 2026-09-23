"""Bounded contract regression: no Mail transport, routes or production claims."""
from __future__ import annotations

import uuid

import pytest

from mission_control import certification, product_core_views
from mission_control.mail_contract import (
    authorize_smi,
    require_first_contact,
    require_folder,
    require_owner,
)

OWNER = str(uuid.uuid4())
OTHER = str(uuid.uuid4())


def test_mail_owner_scope_and_folder_allowlist():
    assert require_owner(OWNER, OWNER) == OWNER
    with pytest.raises(PermissionError, match="mail_owner_required"):
        require_owner(OTHER, OWNER)
    with pytest.raises(PermissionError, match="mail_identity_required"):
        require_owner("untrusted", OWNER)
    assert require_folder(" Inbox ") == "inbox"
    with pytest.raises(ValueError, match="mail_folder_invalid"):
        require_folder("../messages")


def test_smi_mail_requires_explicit_owner_consent_and_never_executes():
    with pytest.raises(PermissionError, match="mail_owner_required"):
        authorize_smi(actor_id=OTHER, mailbox_owner_id=OWNER,
                      ability="mail.read", owner_consent=True)
    with pytest.raises(PermissionError, match="mail_owner_consent_required"):
        authorize_smi(actor_id=OWNER, mailbox_owner_id=OWNER,
                      ability="mail.read", owner_consent=False)
    with pytest.raises(PermissionError, match="mail_execution_not_implemented"):
        authorize_smi(actor_id=OWNER, mailbox_owner_id=OWNER,
                      ability="mail.send", owner_consent=True,
                      human_action_approved=True)
    result = authorize_smi(actor_id=OWNER, mailbox_owner_id=OWNER,
                           ability="mail.summarise", owner_consent=True)
    assert result["execute"] is False
    assert result["production_approved"] is False
    assert result["mail_transport_available"] is False


def test_mail_unsolicited_contact_fails_closed_on_missing_age_or_consent():
    for policy in (None, {"allowed": True, "resolved": False},
                   {"allowed": False, "resolved": True}):
        with pytest.raises(PermissionError):
            require_first_contact(age_policy=policy, consent=True)
    with pytest.raises(PermissionError, match="mail_contact_consent_required"):
        require_first_contact(age_policy={"allowed": True, "resolved": True},
                              consent=False)
    require_first_contact(age_policy={"allowed": True, "resolved": True},
                          consent=True)


def test_commerce_product_route_uses_merchant_gate_source():
    from pathlib import Path
    source = Path(product_core_views.__file__).read_text(encoding="utf-8")
    function = source.split('def create_product():', 1)[1].split(
        '@bp.post("/commerce/orders")', 1)[0]
    assert '_require_certified_merchant(seller_id)' in function
    assert function.index('_require_certified_merchant(seller_id)') < function.index(
        'product_store.create_product('
    )
    assert 'product_store.create_product(' in function


def test_commerce_merchant_guard_refuses_uncertified_and_unavailable(monkeypatch):
    monkeypatch.setattr(certification, "identity_status",
                        lambda _id: {"merchant": False})
    with pytest.raises(PermissionError, match="certified_merchant_required"):
        product_core_views._require_certified_merchant(OWNER)

    def unavailable(_identity):
        raise certification.CertificationUnavailable("unavailable")

    monkeypatch.setattr(certification, "identity_status", unavailable)
    with pytest.raises(certification.CertificationUnavailable):
        product_core_views._require_certified_merchant(OWNER)

    monkeypatch.setattr(certification, "identity_status",
                        lambda _id: {"merchant": True})
    assert product_core_views._require_certified_merchant(OWNER) is None
