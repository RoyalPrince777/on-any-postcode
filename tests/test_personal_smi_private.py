from pathlib import Path

from mission_control import smi_chat_grounded

ROOT = Path(__file__).resolve().parents[1]


def test_personal_smi_contract_is_private_provider_neutral_and_direct():
    contract = smi_chat_grounded.evidence_contract(
        {
            "status": "green",
            "checks": {"database": True, "audit": False},
            "invariants": {"execution_locked": True},
        }
    )
    assert "PERSONAL SMI CONTRACT" in contract
    assert "private Founder-facing mode" in contract
    assert "Keep private Founder context private" in contract
    assert "governed HRM memory" in contract
    assert "Aegis protects" in contract
    assert "Human Authority is final" in contract
    assert "avoid diagnosis" in contract
    assert "never invent an attack" in contract
    assert "implementation engine" in contract.lower()
    assert "execution_locked" in contract
    assert "SMI THINKING DISCIPLINE" in contract
    assert "hidden chain-of-thought" in contract
    assert "INFERRED" in contract
    assert "answer the user's actual question first" in contract
    assert "Do not start every response with 'SMI'" in contract
    assert "purple is learning, never warning" in contract


def test_personal_smi_ui_identity_and_safe_thinking_process_are_explicit():
    compact = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()
    base = (ROOT / "mission_control" / "templates" / "ollama_chat_base.html").read_text()
    combined = compact + base

    assert "Personal SMI" in combined
    assert "Private Founder intelligence" in combined
    assert "HRM" in combined
    assert "Aegis" in combined
    assert "Thinking Process" in compact
    assert "Understand · Context · Route · Evidence · Challenge · Synthesise · Govern" in compact
    assert "private chain-of-thought" in combined
    assert "Seven safe work stages only" in compact
