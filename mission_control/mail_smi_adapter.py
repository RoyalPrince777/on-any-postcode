"""Explicitly consented first-party SMI Mail read boundary.

This is a library adapter only: not a route, agent registration, background
reader, summariser, or mail transport. No implicit consent is persisted.
"""
from __future__ import annotations

from oap.registry.tools import ToolCapability, ToolRegistry

from . import mail_store
from .mail_contract import authorize_smi, require_folder

_MAIL_READ_TOOLS = ToolRegistry((
    ToolCapability(
        tool_id="oap.mail.owner.read",
        name="OAP Mail Owner Read",
        category="mail",
        abilities=("mail.read",),
        read_only=True,
        requires_human_approval=True,
        requires_kernel=True,
    ),
))


def read_owner_folder(
    *, actor_id: object, mailbox_owner_id: object, folder: object,
    owner_consent: bool, ability: object = "mail.read",
) -> dict[str, object]:
    """Return a single bounded, owner-scoped folder read after explicit consent."""
    requested = str(ability or "").strip().casefold()
    if requested != "mail.read":
        raise PermissionError("mail_smi_read_only")
    _MAIL_READ_TOOLS.authorize_capability(
        "oap.mail.owner.read", requested, mutation=False,
    )
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
