"""Fail-closed read-only passport contract. Not an execution or authorisation engine."""
import json
from pathlib import Path

FIELDS = frozenset((
    "agent_id", "official_name", "family", "division", "role",
    "capabilities", "strengths", "limitations", "authority",
    "leadership", "collaborators", "memory", "evidence", "security",
    "tools", "environment", "recovery", "escalation", "version",
    "rating", "status",
))
ALLOWED_FAMILIES = frozenset(("matrix", "animal", "akan", "economic"))
REGISTRY_PATH = Path(__file__).with_name("agent_passports.json")


class PassportContractError(ValueError):
    """Passport data is invalid; consumers must fail closed."""


def validate_registry(payload):
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "purpose", "fields", "entries"}:
        raise PassportContractError("Unexpected registry structure")
    fields = payload["fields"]
    if not isinstance(fields, list) or len(fields) != 21 or len(set(fields)) != 21 or set(fields) != FIELDS:
        raise PassportContractError("Invalid 21-field schema")
    entries = payload["entries"]
    if not isinstance(entries, list) or not entries:
        raise PassportContractError("Empty or invalid entries")
    ids = set()
    names = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != FIELDS:
            raise PassportContractError("Passport fields mismatch")
        for field in FIELDS:
            value = entry[field]
            if value is None or value == "" or isinstance(value, bool):
                raise PassportContractError("Empty or invalid field")
        for key in ("agent_id", "official_name", "family", "division", "role",
                    "authority", "leadership", "memory", "evidence", "security",
                    "environment", "recovery", "escalation", "version", "rating", "status"):
            if not isinstance(entry[key], str):
                raise PassportContractError("Unexpected scalar type")
        for key in ("capabilities", "strengths", "limitations", "collaborators", "tools"):
            if not isinstance(entry[key], list) or not all(isinstance(v, str) for v in entry[key]):
                raise PassportContractError("Unexpected list type")
        if entry["agent_id"] in ids or entry["official_name"].casefold() in names:
            raise PassportContractError("Duplicate passport identity")
        ids.add(entry["agent_id"])
        names.add(entry["official_name"].casefold())
        if entry["family"] not in ALLOWED_FAMILIES:
            raise PassportContractError("Unknown family")
        if (entry["authority"], entry["environment"], entry["status"], entry["tools"]) != (
                "advisory-only", "design-only", "proposed", []):
            raise PassportContractError("Attempted permission or runtime elevation")
    return True


def load_registry(path=REGISTRY_PATH):
    """Validate before returning a detached data object; no tool dispatch."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PassportContractError("Passport registry unavailable or malformed") from exc
    validate_registry(data)
    return data
