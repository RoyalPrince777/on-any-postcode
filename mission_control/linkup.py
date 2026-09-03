"""Canonical governed model for OAP Link Up communications.

Link Up is the protected person-to-person conversation product inside The Link.
World Rooms and geography-led spaces belong to OAP World / Community Power and
are deliberately kept out of this messenger surface.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

COMMUNICATIONS_SYSTEM = "Communications"
COMMUNITY_POWER_SYSTEM = "Community Power"

LINK_UP_LANGUAGE_LAW: tuple[str, ...] = (
    "Brand language for identity.",
    "Human language for conversation.",
    "Plain language for safety.",
    "Local character without global confusion.",
)

LINK_UP_PUBLIC_VOCABULARY: dict[str, str] = {
    "product": "Link Up",
    "conversations": "Link Ups",
    "people": "People",
    "connection": "Link",
    "connection_request": "Link Request",
    "new_conversation": "New Link",
    "presence": "Around Now",
    "available": "I'm Free",
    "delivered": "Landed",
    "read": "Seen",
    "voice_note": "Voice",
    "audio_call": "Call",
    "video_call": "Face Up",
    "share_location": "Share My Spot",
    "live_location": "Live Spot",
    "short_status": "Now",
    "status_prompt": "What you on?",
    "notifications": "Alerts",
    "announcement": "Signal",
    "profile": "My Card",
    "trust_status": "Certified",
    "trusted_contact": "Trusted Contact",
}

LINK_UP_PLAIN_CONTROLS: tuple[str, ...] = (
    "Mute",
    "Camera",
    "Speaker",
    "Answer",
    "Decline",
    "End",
    "Block",
    "Report",
    "Privacy",
    "Delete",
)
LINK_UP_PLAIN_SAFETY_TERMS = LINK_UP_PLAIN_CONTROLS

LINK_DASHBOARD_VIEWS: tuple[dict[str, str], ...] = (
    {"id":"directory","name":"Directory","owner":COMMUNICATIONS_SYSTEM,"ownership":"owned_view","purpose":"Find verified people and local connections.","status":"Protected","data":"Authenticated member projection only","boundary":"People and community connections only; this is not the Agent Intelligence directory."},
    {"id":"inbox","name":"Inbox","owner":COMMUNICATIONS_SYSTEM,"ownership":"owned_view","purpose":"Private conversation access for authenticated members.","status":"Protected","data":"Sender and recipient scoped messages only","boundary":"A view over approved Communications records, not a second Mail or Messenger store."},
    {"id":"community_power","name":"Community Power","owner":COMMUNITY_POWER_SYSTEM,"ownership":"linked_view","purpose":"World Rooms and geography spaces live outside Link Up.","status":"Read-only link","data":"No private room or contribution records exposed","boundary":"Continent, country and other World Rooms remain owned by Community Power / OAP World, never by the private messenger."},
)
LOCKED_LINK_VIEW_IDS = tuple(view["id"] for view in LINK_DASHBOARD_VIEWS)
LOCKED_LINK_VIEW_NAMES = tuple(view["name"] for view in LINK_DASHBOARD_VIEWS)
EXPECTED_VIEW_OWNERS = {"directory":(COMMUNICATIONS_SYSTEM,"owned_view"),"inbox":(COMMUNICATIONS_SYSTEM,"owned_view"),"community_power":(COMMUNITY_POWER_SYSTEM,"linked_view")}

RELATED_COMMUNICATION_BOUNDARIES: tuple[dict[str, str], ...] = (
    {"id":"signals","name":"Signal","owner":"OAP World","relationship":"Public announcements remain Signal; they are not private conversations or Inbox messages."},
    {"id":"pulse","name":"Pulse","owner":"OAP World","relationship":"Pulse remains the community heartbeat and may link into approved threads without becoming another message store."},
    {"id":"team_rooms","name":"OAP TV Team Rooms","owner":"OAP TV","relationship":"Existing match-room conversations stay on their current surface; this dashboard does not copy them."},
    {"id":"mail_notifications","name":"Mail, Alerts and Broadcasts","owner":COMMUNICATIONS_SYSTEM,"relationship":"They remain sibling Communications modules; Inbox does not replace or duplicate them."},
    {"id":"identity_guardian_hrm","name":"Identity, Guardian and HRM","owner":"Shared protective systems","relationship":"Identity validates access, Guardian protects privacy and youth safety, and HRM receives approved audit metadata only."},
)

PRIVACY_PATH: tuple[dict[str, str], ...] = (
    {"name":"Identity","action":"Validates the member"},{"name":"Permissions","action":"Scopes conversation access"},{"name":"Guardian","action":"Protects privacy and youth safety"},{"name":"Link Up","action":"Presents the approved conversation view"},{"name":"HRM","action":"Receives approved audit metadata only"},
)
PROTECTED_LINK_RUNTIME: dict[str, object] = {"authenticated_identity_required":True,"csrf_required_for_mutations":True,"sender_recipient_scope":True,"message_persistence":"Postgres Communications store","rate_limit_enabled":True,"guardian_message_screening":True,"read_receipts":True,"public_message_projection":False,"human_authority_final":True}
REMAINING_LINK_GATES: tuple[dict[str, str], ...] = (
    {"title":"Blocking and reporting workflow","description":"Durable block/report state, moderation routing and auditable Guardian escalation.","status":"Implemented; certification evidence required"},
    {"title":"Private-message retention and encryption policy","description":"Certify storage encryption, retention/deletion behaviour and backup handling for protected Communications records.","status":"Not yet certified"},
    {"title":"World Rooms participation","description":"World Rooms stay outside Link Up and may only be referenced without copying room or contribution records.","status":"Separated from messenger"},
)
PROPOSED_LINK_ENABLEMENT = REMAINING_LINK_GATES

def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())

def _duplicates(values: Iterable[str]) -> set[str]:
    seen:set[str]=set(); duplicates:set[str]=set()
    for value in values:
        if value in seen: duplicates.add(value)
        seen.add(value)
    return duplicates

def validate_link_scope(views: Iterable[Mapping[str, Any]] = LINK_DASHBOARD_VIEWS) -> dict[str, Any]:
    view_list=tuple(views); ids=[str(v.get("id","")).strip().casefold() for v in view_list]; names=[_normalise(str(v.get("name",""))) for v in view_list]
    duplicate_ids=_duplicates(ids); duplicate_names=_duplicates(names); missing=set(LOCKED_LINK_VIEW_IDS)-set(ids); unexpected=set(ids)-set(LOCKED_LINK_VIEW_IDS); mutation_controls=sum(bool(v.get("mutation_enabled")) for v in view_list)
    ownership_conflicts=[]
    for view in view_list:
        view_id=str(view.get("id","")).strip().casefold(); expected=EXPECTED_VIEW_OWNERS.get(view_id)
        if expected and (str(view.get("owner","")),str(view.get("ownership",""))) != expected: ownership_conflicts.append(view_id)
    errors=[]
    if duplicate_ids: errors.append("Duplicate Link view IDs: "+", ".join(sorted(duplicate_ids)))
    if duplicate_names: errors.append("Duplicate Link view names: "+", ".join(sorted(duplicate_names)))
    if missing: errors.append("Locked Link views missing: "+", ".join(sorted(missing)))
    if unexpected: errors.append("Unapproved Link views present: "+", ".join(sorted(unexpected)))
    if ownership_conflicts: errors.append("Link view ownership conflict: "+", ".join(sorted(set(ownership_conflicts))))
    if mutation_controls: errors.append("Public The Link mutation controls must remain disabled")
    return {"passed":not errors,"errors":errors,"checks":{"dashboard_views":len(view_list),"communication_views":sum(v.get("ownership")=="owned_view" for v in view_list),"linked_views":sum(v.get("ownership")=="linked_view" for v in view_list),"duplicate_ids":len(duplicate_ids),"naming_conflicts":len(duplicate_names),"ownership_conflicts":len(set(ownership_conflicts)),"mutation_controls":mutation_controls}}

def get_public_link_dashboard() -> dict[str, Any]:
    return {
        "product_name": LINK_UP_PUBLIC_VOCABULARY["product"],
        "tagline": "Simple private chat.",
        "law": "The Link → Link Up",
        "features": [
            {"name": "Chats", "purpose": "Your private one-to-one Link Ups."},
            {"name": "Calls", "purpose": "Voice, Call and Face Up from the chat screen."},
        ],
    }
