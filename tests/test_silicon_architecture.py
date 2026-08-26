from mission_control import silicon_architecture as silicon


def test_silicon_contract_validates() -> None:
    silicon.validate_silicon_contract()


def test_silicon_mission_and_locked_principles_are_canonical() -> None:
    contract = silicon.silicon_contract()

    assert contract["mission"] == (
        "Own the intelligence architecture before owning the transistor."
    )
    assert contract["design_principles"] == (
        "Human Authority above software.",
        "Software above hardware execution.",
        "Hardware proves, isolates and enforces — it does not rule.",
    )


def test_human_authority_remains_above_hardware_execution() -> None:
    contract = silicon.silicon_contract()

    assert contract["authority_chain"][0] == "Human Authority"
    assert contract["authority_chain"][-1] == "Hardware Execution"
    assert contract["human_authority_final"] is True
    assert contract["independent_hardware_authority"] is False


def test_silicon_retains_seven_layers_seven_zones_and_twenty_one_gates() -> None:
    contract = silicon.silicon_contract()

    assert len(contract["layers"]) == 7
    assert len(contract["execution_zones"]) == 7
    assert set(contract["gates"]) == {
        "hardware_trust",
        "intelligence",
        "human_authority",
    }
    assert all(len(gates) == 7 for gates in contract["gates"].values())
    assert contract["gate_count"] == 21


def test_current_home_node_is_generation_zero_reference() -> None:
    contract = silicon.silicon_contract()
    generation_zero = contract["reference_generations"][0]

    assert generation_zero["generation"] == 0
    assert generation_zero["status"] == "ACTIVE_REFERENCE"
    assert "Android/Termux" in generation_zero["platform"]
    assert contract["physical_chip_required_now"] is False


def test_hardware_cannot_gain_consequential_authority() -> None:
    blocked = set(silicon.BLOCKED_HARDWARE_AUTONOMY)

    assert {
        "self_apply_improvement",
        "deploy",
        "payment_capture",
        "money_transfer",
        "driver_dispatch",
        "permission_change",
        "production_migration",
        "esim_activation",
        "carrier_switch",
        "public_precise_tracking",
    } <= blocked


def test_silicon_stack_preserves_single_smi_brain_and_hrm_memory() -> None:
    stack = silicon.SILICON_STACK

    assert stack.count("SMI Brain") == 1
    assert stack.index("OAP Silicon") < stack.index("OAP Home Node")
    assert stack.index("OAP CORE") < stack.index("SMI Brain")
    assert stack.index("SMI Brain") < stack.index("Human Authority")
    assert stack[-1] == "HRM"
