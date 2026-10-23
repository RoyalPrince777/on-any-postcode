"""SMI Court 777: individual specialist agent definitions (non-executing).

Design registry only. No legal representation, adjudication, model training,
court authority, or live agent execution is created by importing this module.
"""
from __future__ import annotations

COURT_AGENT_ROLES = (
  'chief_justice',
  'deputy_judge',
  'court_administrator',
  'court_clerk',
  'court_marshal',
  'prosecutor',
  'defence_counsel',
  'legal_researcher',
  'appeals_counsel',
  'lead_investigator',
  'evidence_examiner',
  'digital_forensics_specialist',
  'witness_coordinator',
  'truth_contradiction_reviewer',
  'jury_coordinator',
  'jury_foreperson',
  'seven_star_rating_auditor',
  'independent_appeals_reviewer',
  'guardian_liaison',
  'hrm_records_officer',
  'founder_final_liaison'
)

COURT_AGENT_DEFINITIONS = tuple(
    {
        "id": f"SMI-COURT-{i:03d}",
        "role": role,
        "kind": "specialist_agent_definition",
        "operational": False,
        "training_verified": False,
        "permissions": ("read_authorised_case_material",),
        "external_contact": False,
        "independent_legal_advice": False,
        "independent_execution": False,
        "human_approval_required": True,
    }
    for i, role in enumerate(COURT_AGENT_ROLES, 1)
)

def court_status():
    """Report declared identities without misrepresenting deployment."""
    return {
        "mission": "SMI Court Intelligence 777",
        "agent_definition_count": len(COURT_AGENT_DEFINITIONS),
        "verified_running_agents": None,
        "operational_vpi": None,
        "founder_final": True,
        "guardian_hrm_required": True,
        "qualified_legal_review_required": True,
        "real_human_training": "consenting_authorised_participants_only",
        "definitions": COURT_AGENT_DEFINITIONS,
    }
