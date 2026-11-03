"""SMI 777 choice comparison: advisory, evidence-bound, no execution."""
from __future__ import annotations

CHOICES = {
    "explore": ("Fox", "Octopus", "Owl"),
    "approve": ("Captain ALL IN", "Guardian", "HRM"),
    "vote": ("Owl", "Bagheera", "Shere Khan"),
    "challenge": ("Shere Khan", "Octopus", "Bagheera"),
    "protect": ("Bagheera", "Guardian", "HRM"),
    "upgrade": ("NIRMATA", "Fox", "Shere Khan"),
    "verify": ("Guardian", "HRM", "Trinity"),
}
REQUIRED_GATES = ("guardian_authorised", "founder_authorised", "evidence_verified")

def compare_choices(mission_id, choice, options, evidence=None):
    """Return an advisory comparison without fabricating votes or outcomes.

    Options must have unique IDs and independently supplied verified evidence.
    No numeric performance scores are inferred.
    """
    if not isinstance(mission_id, str) or not mission_id.strip():
        return {"ready": False, "reason": "mission_id_required"}
    if choice not in CHOICES:
        return {"ready": False, "reason": "unknown_choice"}
    if not isinstance(options, (list, tuple)) or not options:
        return {"ready": False, "reason": "options_required"}
    ids = [o.get("id") for o in options if isinstance(o, dict)]
    if len(ids) != len(options) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        return {"ready": False, "reason": "invalid_or_duplicate_options"}
    rows = tuple({"id": o["id"], "evidence_status": "verified" if o.get("evidence_verified") is True else "unverified",
                  "advantages": tuple(o.get("advantages", ())) if isinstance(o.get("advantages", ()), (tuple, list)) else (),
                  "risks": tuple(o.get("risks", ())) if isinstance(o.get("risks", ()), (tuple, list)) else ()}
                 for o in options)
    return {"ready": True, "mission_id": mission_id, "choice": choice,
            "suggested_specialists": CHOICES[choice], "comparison": rows,
            "agent_votes_executed": False, "execution_authorised": False,
            "operational_vpi": None, "decision": "founder_final_required"}

def execution_gate(approvals):
    """Only report eligibility from explicit booleans; never execute."""
    if not isinstance(approvals, dict):
        return False
    return all(approvals.get(key) is True for key in REQUIRED_GATES)
