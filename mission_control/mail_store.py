"""Owner-scoped OAP Mail persistence. No SMTP, sending or Link Up reuse."""
from __future__ import annotations

from . import postgres_db
from .mail_contract import identity, require_folder, require_owner


class MailUnavailable(RuntimeError):
    """The dedicated Mail store is unavailable or its migration is not applied."""


def list_items(actor_id: object, owner_id: object, folder: object) -> list[dict[str, object]]:
    owner = require_owner(actor_id, owner_id)
    selected = require_folder(folder)
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT id,folder,subject,body,correspondent,created_at
                   FROM oap_mail_items WHERE owner_id=%s AND folder=%s
                   ORDER BY created_at DESC,id DESC LIMIT 50""",
                (owner, selected),
            ).fetchall()
    except Exception as exc:
        raise MailUnavailable("mail_store_unavailable") from exc
    return [
        {
            "id": str(row[0]),
            "folder": row[1],
            "subject": row[2],
            "body": row[3],
            "correspondent": row[4],
            "created_at": row[5].isoformat(),
        }
        for row in rows
    ]


def list_subjects(
    actor_id: object, owner_id: object, folder: object,
) -> list[dict[str, object]]:
    """Bounded SMI subject list: never SELECT message body or message ID."""
    owner = require_owner(actor_id, owner_id)
    selected = require_folder(folder)
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT subject,correspondent
                   FROM oap_mail_items WHERE owner_id=%s AND folder=%s
                   ORDER BY created_at DESC,id DESC LIMIT 50""",
                (owner, selected),
            ).fetchall()
    except Exception as exc:
        raise MailUnavailable("mail_store_unavailable") from exc
    return [
        {"subject": row[0], "correspondent": row[1]}
        for row in rows
    ]


def validate_draft_fields(
    *, subject: object, body: object, correspondent: object = "",
) -> tuple[str, str, str]:
    """Validate without database access; share the same guard with route and store."""
    if any(value is not None and not isinstance(value, str)
           for value in (subject, body, correspondent)):
        raise ValueError("mail_draft_field_invalid")
    subject_text = (subject or "").strip()
    body_text = (body or "").strip()
    contact_text = (correspondent or "").strip()
    if not subject_text and not body_text:
        raise ValueError("mail_draft_empty")
    if len(subject_text) > 200 or len(body_text) > 20000 or len(contact_text) > 320:
        raise ValueError("mail_draft_too_large")
    return subject_text, body_text, contact_text


def save_draft(
    actor_id: object, owner_id: object, *, subject: object, body: object,
    correspondent: object = "",
) -> str:
    owner = require_owner(actor_id, owner_id)
    subject_text, body_text, contact_text = validate_draft_fields(
        subject=subject, body=body, correspondent=correspondent,
    )
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_mail_items
                   (owner_id,folder,subject,body,correspondent)
                   VALUES (%s,'draft',%s,%s,%s) RETURNING id""",
                (owner, subject_text, body_text, contact_text),
            ).fetchone()
            if row is None:
                raise MailUnavailable("mail_draft_unavailable")
            connection.commit()
    except MailUnavailable:
        raise
    except Exception as exc:
        raise MailUnavailable("mail_store_unavailable") from exc
    return identity(row[0])
