"""Explicitly consented first-party SMI Mail read boundary.

This is a library adapter only: not a route, agent registration, background
reader, summariser, or mail transport. No implicit consent is persisted.
"""
from __future__ import annotations

from . import mail_store
from .mail_contract import authorize_smi, require_folder


def read_owner_folder(
    *, actor_id: object, mailbox_owner_id: object, folder: object,
    owner_consent: bool, ability: object = "mail.read",
) -> dict[str, object]:
    """Return a single bounded, owner-scoped folder read after explicit consent."""
    decision = authorize_smi(
        actor_id=actor_id,
        mailbox_owner_id=mailbox_owner_id,
        ability=ability,
        owner_consent=owner_consent,
    )
    if decision["ability"] != "mail.read":
        raise PermissionError("mail_smi_read_only")
    selected = require_folder(folder)
    owner = decision["mailbox_owner_id"]
    items = mail_store.list_items(actor_id, owner, selected)
    return {
        "folder": selected,
        "items": items,
        "execute": False,
        "delivery_enabled": False,
        "production_approved": False,
    }
