"""Standalone OAP PTT front door.

PTT is a top-level OAP communication product. It reuses the existing first-party
voice store, accepted-contact, youth-safety and block guards without being owned
by The Link or Link Up.
"""
from __future__ import annotations

from flask import Blueprint, make_response, render_template

from . import link_relationships, product_store, web_security

bp = Blueprint("ptt_ui", __name__, template_folder="templates")


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _accepted_contacts(identity_id: str) -> list[dict[str, str]]:
    try:
        dashboard = product_store.linkup_dashboard(identity_id) or {}
        directory = {
            str(person.get("identity_id")): person
            for person in dashboard.get("directory", [])
        }
        contacts: list[dict[str, str]] = []
        for relation in link_relationships.list_for_identity(identity_id):
            if relation.get("status") != "accepted":
                continue
            peer_id = (
                str(relation["recipient_id"])
                if str(relation["requester_id"]) == identity_id
                else str(relation["requester_id"])
            )
            peer = directory.get(peer_id, {})
            contacts.append(
                {
                    "identity_id": peer_id,
                    "display_name": str(peer.get("display_name") or "OAP Contact"),
                    "card_id": str(
                        peer.get("card_id") or product_store.member_card_id(peer_id)
                    ),
                }
            )
        contacts.sort(key=lambda item: item["display_name"].casefold())
        return contacts
    except (
        product_store.ProductStoreUnavailable,
        link_relationships.LinkRelationshipsUnavailable,
    ):
        return []


@bp.get("/ptt")
@web_security.login_required()
def front_door():
    user = web_security.current_authenticated_user()
    identity_id = str(user["id"])
    response = make_response(
        render_template(
            "ptt.html",
            contacts=_accepted_contacts(identity_id),
            oap_csrf_token=web_security.csrf_token(),
        )
    )
    return _no_store(response)
