"""No implicit access or transport through the first-party SMI Mail adapter."""
from __future__ import annotations

import uuid

import pytest

from mission_control import mail_smi_adapter, mail_store

OWNER = str(uuid.uuid4())
OTHER = str(uuid.uuid4())


def test_consented_read_passes_exact_owner_and_folder(monkeypatch):
    calls = []
    def read(actor, owner, folder):
        calls.append((actor, owner, folder))
        return [{"subject": "private"}]
    monkeypatch.setattr(mail_store, "list_items", read)
    result = mail_smi_adapter.read_owner_folder(
        actor_id=OWNER, mailbox_owner_id=OWNER,
        folder=" Inbox ", owner_consent=True,
    )
    assert calls == [(OWNER, OWNER, "inbox")]
    assert result["items"] == [{"subject": "private"}]
    assert result["execute"] is False
    assert result["delivery_enabled"] is False
    assert result["production_approved"] is False


@pytest.mark.parametrize(
    ("actor", "owner", "consent", "ability", "folder"),
    [
        (OTHER, OWNER, True, "mail.read", "inbox"),
        (OWNER, OWNER, False, "mail.read", "inbox"),
        (OWNER, OWNER, True, "mail.send", "inbox"),
        (OWNER, OWNER, True, "mail.summarise", "inbox"),
        (OWNER, OWNER, True, "mail.draft", "inbox"),
        (OWNER, OWNER, True, "mail.read", "../messages"),
    ],
)
def test_adapter_denials_never_read_store(
    monkeypatch, actor, owner, consent, ability, folder,
):
    calls = []
    monkeypatch.setattr(mail_store, "list_items",
                        lambda *_: calls.append(True))
    with pytest.raises((PermissionError, ValueError)):
        mail_smi_adapter.read_owner_folder(
            actor_id=actor, mailbox_owner_id=owner, folder=folder,
            owner_consent=consent, ability=ability,
        )
    assert calls == []


def test_store_unavailable_is_not_recast_as_success(monkeypatch):
    def unavailable(*_):
        raise mail_store.MailUnavailable("mail_store_unavailable")
    monkeypatch.setattr(mail_store, "list_items", unavailable)
    with pytest.raises(mail_store.MailUnavailable):
        mail_smi_adapter.read_owner_folder(
            actor_id=OWNER, mailbox_owner_id=OWNER,
            folder="inbox", owner_consent=True,
        )
