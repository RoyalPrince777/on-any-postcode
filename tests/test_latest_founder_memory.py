from oap.smi import latest_founder_memory, memory_orchestrator


def test_latest_founder_memory_contains_current_locked_rules():
    items = latest_founder_memory.latest_founder_memory_items()
    text = "\n".join(item.summary for item in items)
    assert "JOOG MEMORY" in text
    assert "no demo" in text
    assert "no fake green" in text
    assert "Kaa is completely excluded" in text
    assert "one canonical Send/Enter/Mic/Voice/Stop runtime" in text
    assert (
        latest_founder_memory.status()["revision"]
        == "2026-09-18-war-room-intelligence"
    )


def test_latest_founder_memory_outranks_older_canonical_context():
    items = memory_orchestrator.compose_memory("GENERAL", limit=21)
    status = memory_orchestrator.status()
    assert items[0].task_type == "LATEST_FOUNDER_LOCK"
    assert items[0].memory_id.startswith("founder-lock:")
    assert status["authority_order"][0] == "LATEST_FOUNDER_LOCK"
    assert status["budget_total"] == 21


def test_latest_founder_memory_never_claims_raw_chat_or_private_reasoning_copy():
    status = latest_founder_memory.status()
    assert status["raw_chat_dump"] is False
    assert status["private_chain_of_thought_included"] is False
    assert status["credentials_or_secrets_included"] is False
    assert status["human_authority_final"] is True


def test_war_room_intelligence_is_locked_in_joog_memory():
    items = latest_founder_memory.latest_founder_memory_items()
    text = "\n".join(item.summary for item in items)
    assert "JOOG MEMORY full War Room Intelligence lock" in text
    for marker in (
        "Truth, Evidence, Gap, SWOT, Risk, Dependency, Architecture, Alignment",
        "Civic, Jungle Book, Animal, Matrix, Civilisation, Akan Core and Akan Animal",
        "Shere Khan, Bagheera, Agent Smith, Lion, Morpheus, Akela and Owl",
        "SMI, Neo, Wolf Pack, Trinity, Oracle, Architect, Keymaker and Seraph",
        "RUN, RESEARCH, CHALLENGE, 7X DEEP DIVE, STOP, COMPARE",
        "Discovery, Verification, Alternatives, Adversarial, Systems, Consequence and Synthesis",
        "Truth, Function, Security, Stability, Integration, Compliance and Learning",
        "Neo -> Shere Khan -> Bagheera -> Agent Smith -> Judges -> SMI Return -> Green Gate",
        "TITLE -> MODE/DEPTH -> QUESTION/MISSION -> EVIDENCE",
        "MISSION, SIGNAL, EVIDENCE, CONFIDENCE",
        "25%=Rollback/Recovery",
        "50%=Runtime Guard",
        "75%=Aegis Isolation/Recovery",
        "100%=Green Gate + Founder Final",
        "simulation passed is not production proven",
        "Human Authority remains final",
    ):
        assert marker in text
