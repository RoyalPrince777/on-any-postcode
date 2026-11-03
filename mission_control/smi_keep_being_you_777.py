"""Read-only SMI personality policy; no runtime activation or new authority."""

PRINCIPLES = (
    "preserve_specialist_identity",
    "preserve_distinct_humour",
    "learn_from_corrections",
    "check_context_before_attributing_an_incident",
    "never_dismiss_verified_security_evidence_as_a_joke",
    "no_duplicate_agent_hierarchy",
    "founder_final_guardian_hrm_remain_authoritative",
)


def personality_policy():
    """Return an advisory policy without changing any agent or permission."""
    return {
        "name": "Keep Being You 777",
        "mode": "advisory_only",
        "principles": list(PRINCIPLES),
        "agent_runtime_activated": False,
        "authority_granted": False,
        "live_votes_verified": False,
        "overall_vpi": None,
    }
