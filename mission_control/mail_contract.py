"""OAP Mail ownership contract; no routes, transport, or automatic SMI access.

Keep Mail separate from Link Up messages and Market listing authority.
Only explicit mailbox-owner scope permits a read; preparation never sends.
"""
from __future__ import annotations

import uuid

FOLDERS = frozenset({"inbox", "sent", "draft", "review"})
READ_ABILITIES = frozenset({"mail.read", "mail.search", "mail.summarise"})
WRITE_ABILITIES = frozenset({"mail.draft"})
EXECUTE_ABILITIES = frozenset({"mail.send", "mail.forward", "mail.delete"})


def identity(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise PermissionError("mail_identity_required") from exc


def require_owner(actor_id: object, mailbox_owner_id: object) -> str:
    actor = identity(actor_id)
    owner = identity(mailbox_owner_id)
    if actor != owner:
        raise PermissionError("mail_owner_required")
    return owner


def require_folder(folder: object) -> str:
    value = str(folder or "").strip().casefold()
    if value not in FOLDERS:
        raise ValueError("mail_folder_invalid")
    return value


def authorize_smi(
    *,
    actor_id: object,
    mailbox_owner_id: object,
    ability: object,
    owner_consent: bool,
    human_action_approved: bool = False,
) -> dict[str, object]:
    """An authorisation decision only, not a tool adapter or execution path."""
    owner = require_owner(actor_id, mailbox_owner_id)
    requested = str(ability or "").strip().casefold()
    if requested not in READ_ABILITIES | WRITE_ABILITIES | EXECUTE_ABILITIES:
        raise PermissionError("mail_ability_unapproved")
    if owner_consent is not True:
        raise PermissionError("mail_owner_consent_required")
    if requested in EXECUTE_ABILITIES:
        # There is no delivery, deletion, or other executor in this slice.
        raise PermissionError("mail_execution_not_implemented")
    if human_action_approved and requested in READ_ABILITIES:
        # Approval cannot widen the read scope beyond the owner.
        pass
    return {
        "mailbox_owner_id": owner,
        "ability": requested,
        "execute": False,
        "human_authority_final": True,
        "mail_transport_available": False,
        "production_approved": False,
    }


def require_first_contact(*, age_policy: dict[str, object] | None, consent: bool) -> None:
    """Fail closed for unsolicited Mail contact; do not alter Link Up policy."""
    if consent is not True:
        raise PermissionError("mail_contact_consent_required")
    if not isinstance(age_policy, dict) or age_policy.get("resolved") is not True:
        raise PermissionError("mail_age_policy_unresolved")
    if age_policy.get("allowed") is not True:
        raise PermissionError("mail_youth_contact_blocked")
