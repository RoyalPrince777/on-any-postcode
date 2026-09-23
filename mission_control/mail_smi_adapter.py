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
    try:
        _MAIL_READ_TOOLS.authorize_capability(
            "oap.mail.owner.read", requested, mutation=False,
        )
    except (LookupError, PermissionError) as exc:
        raise PermissionError("mail_smi_capability_unavailable") from exc
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
    # The SMI inbox tool is a subject-list action, not permission to deliver
    # message bodies, IDs, addresses or unknown store fields to the browser.
    # Keep the full owner-scoped store result intact for other Mail surfaces.
    projected = [
        {
            "subject": item.get("subject"),
            **(
                {"correspondent": item["correspondent"]}
                if "correspondent" in item else {}
            ),
        }
        for item in items
    ]
    return {
        "folder": selected,
        "items": projected,
        "execute": False,
        "delivery_enabled": False,
        "production_approved": False,
    }
