"""No implicit access or transport through the first-party SMI Mail adapter."""
from __future__ import annotations

import uuid

import pytest

from mission_control import mail_smi_adapter, mail_store
from oap.registry.tools import ToolCapability, ToolRegistry

OWNER = str(uuid.uuid4())
OTHER = str(uuid.uuid4())


def test_consented_read_passes_exact_owner_and_folder(monkeypatch):
    calls = []
    def read(actor, owner, folder):
        calls.append((actor, owner, folder))
        return [{"subject": "private"}]
    monkeypatch.setattr(mail_store, "list_subjects", read)
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
    monkeypatch.setattr(mail_store, "list_subjects",
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
    monkeypatch.setattr(mail_store, "list_subjects", unavailable)
    with pytest.raises(mail_store.MailUnavailable):
        mail_smi_adapter.read_owner_folder(
            actor_id=OWNER, mailbox_owner_id=OWNER,
            folder="inbox", owner_consent=True,
        )


def test_mail_capability_registry_is_read_only_and_not_independent():
    capability = mail_smi_adapter._MAIL_READ_TOOLS.authorize_capability(
        "oap.mail.owner.read", "mail.read", mutation=False,
    )
    assert capability.read_only is True
    assert capability.requires_human_approval is True
    assert capability.requires_kernel is True
    assert capability.can_execute_independently is False
    with pytest.raises(PermissionError):
        mail_smi_adapter._MAIL_READ_TOOLS.authorize_capability(
            "oap.mail.owner.read", "mail.read", mutation=True,
        )


def test_disabled_mail_capability_fails_before_store(monkeypatch):
    monkeypatch.setattr(
        mail_smi_adapter, "_MAIL_READ_TOOLS",
        ToolRegistry((ToolCapability(
            tool_id="oap.mail.owner.read", name="OAP Mail Owner Read",
            category="mail", abilities=("mail.read",), enabled=False,
        ),)),
    )
    calls = []
    monkeypatch.setattr(mail_store, "list_subjects",
                        lambda *_: calls.append(True))
    with pytest.raises(PermissionError, match="mail_smi_capability_unavailable"):
        mail_smi_adapter.read_owner_folder(
            actor_id=OWNER, mailbox_owner_id=OWNER,
            folder="inbox", owner_consent=True,
        )
    assert calls == []


def test_mail_registry_does_not_authorize_send_or_forward():
    for ability in ("mail.send", "mail.forward", "mail.delete"):
        with pytest.raises(PermissionError):
            mail_smi_adapter._MAIL_READ_TOOLS.authorize_capability(
                "oap.mail.owner.read", ability, mutation=False,
            )



def test_smi_subject_list_excludes_body_ids_and_unknown_fields(monkeypatch):
    private_row = {
        "id": "secret-message-id",
        "subject": "<private>",
        "body": "NEVER_TRANSFER_MAIL_BODY",
        "correspondent": "owner@example.test",
        "created_at": "secret-timestamp",
        "debug_secret": "INTERNAL_SECRET",
    }
    monkeypatch.setattr(
        mail_store, "list_subjects",
        lambda *_: [{
            "subject": private_row["subject"],
            "correspondent": private_row["correspondent"],
        }],
    )
    monkeypatch.setattr(
        mail_store, "list_items",
        lambda *_: (_ for _ in ()).throw(
            AssertionError("SMI cannot invoke the full-message query")
        ),
    )
    result = mail_smi_adapter.read_owner_folder(
        actor_id=OWNER, mailbox_owner_id=OWNER,
        folder="inbox", owner_consent=True,
    )
    assert result["items"] == [{
        "subject": "<private>",
        "correspondent": "owner@example.test",
    }]
    assert private_row["body"] == "NEVER_TRANSFER_MAIL_BODY"
    assert "NEVER_TRANSFER_MAIL_BODY" not in repr(result)
    assert "INTERNAL_SECRET" not in repr(result)
    assert "secret-message-id" not in repr(result)
