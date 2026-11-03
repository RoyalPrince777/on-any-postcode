"""Evidence-bound legal knowledge routing and passport enrichment for SMI Court 777.

No automatic learning, surveillance, live legal advice, court representation,
tax filing, or external action. Review current primary law before conclusions.
"""
from __future__ import annotations
from .smi_court_agents_777 import COURT_AGENT_DEFINITIONS

LEGAL_DOMAINS = (
    "oap_internal_governance", "law_of_land", "law_of_jungle_internal_ethics",
    "human_rights", "treaties_and_domestic_effect", "global_affairs",
    "political_and_regulatory_change_neutral", "company_and_director_law",
    "contracts_and_consumer", "employment", "intellectual_property",
    "privacy_and_uk_gdpr", "cybersecurity_and_incidents", "fraud_prevention",
    "criminal_procedure_and_arrest_rights", "civil_litigation_and_appeals",
    "corporation_tax", "personal_tax", "vat_and_payroll", "international_tax",
    "sanctions_and_cross_border", "cultural_and_customary_law",
)

SOURCE_RULES = {
    "primary": ("legislation.gov.uk", "gov.uk", "ico.org.uk",
                "supremecourt.uk", "judiciary.uk", "un.org", "ohchr.org"),
    "required_fields": ("jurisdiction", "source_url", "source_date",
                        "effective_date", "legal_status", "verified_at"),
    "statuses": ("binding", "proposed", "guidance", "internal_policy", "unknown"),
}
PASSPORT_REQUIRED_FIELDS = (
    "id", "role", "kind", "operational", "training_verified",
    "permissions", "human_approval_required",
)

def legal_agent_passports():
    """21 distinct, non-operational identities with learning domains."""
    return tuple({
        **agent,
        "mission": "SMI Court 777",
        "learning_domains": LEGAL_DOMAINS,
        "legal_training_evidence": None,
        "human_training_consent_verified": False,
        "source_freshness_verified": False,
        "founder_final": True,
        "guardian_hrm_required": True,
        "legal_representation_authorised": False,
        "tax_filing_authorised": False,
        "external_monitoring_authorised": False,
    } for agent in COURT_AGENT_DEFINITIONS)

def evaluate_legal_source(record):
    """Fail closed for incomplete evidence or uncertain legal status."""
    missing = tuple(k for k in SOURCE_RULES["required_fields"] if not record.get(k))
    return {
        "accepted_for_legal_conclusion": not missing and record.get("legal_status") == "binding"
        and bool(record.get("primary_source_verified")),
        "missing": missing,
        "qualified_review_required": True,
        "jurisdiction": record.get("jurisdiction"),
    }

def legal_learning_status():
    return {
        "agent_definitions": len(COURT_AGENT_DEFINITIONS),
        "learning_domains": len(LEGAL_DOMAINS),
        "trained_agents_verified": None,
        "live_agents_verified": None,
        "overall_vpi": None,
        "human_rights_and_law_of_land_override_internal_rules": True,
        "tax_evasion_or_concealment": False,
        "lawful_tax_planning_only": True,
    }
