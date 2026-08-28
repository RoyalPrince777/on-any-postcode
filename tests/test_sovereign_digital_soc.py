from mission_control.silicon_architecture import (
    BLOCKED_HARDWARE_AUTONOMY,
    SILICON_GATES,
)
from mission_control.sovereign_digital_soc import (
    ALL_GATE_KEYS,
    COGNITIVE_AUTHORITY,
    DIGITAL_SOC_BLOCKS,
    EXTERNAL_EXECUTION_ENABLED,
    FINAL_AUTHORITY,
    FPGA_LOADED,
    PHYSICAL_CHIP_BUILT,
    RTL_IMPLEMENTED,
    SovereignDigitalSoCSimulator,
    digital_soc_contract,
    validate_digital_soc_contract,
)


def _all_gate_evidence(value: bool = True) -> dict[str, bool]:
    return {key: value for key in ALL_GATE_KEYS}


def _hardware_evidence(value: bool = True) -> dict[str, bool]:
    return {f"hardware_trust.{gate}": value for gate in SILICON_GATES["hardware_trust"]}


def test_digital_soc_contract_preserves_single_brain_and_human_authority():
    validate_digital_soc_contract()
    contract = digital_soc_contract()

    assert COGNITIVE_AUTHORITY == "SMI Brain"
    assert FINAL_AUTHORITY == "Human Authority"
    assert contract["cognitive_authority"] == "SMI Brain"
    assert contract["final_authority"] == "Human Authority"
    assert len(DIGITAL_SOC_BLOCKS) == 21
    assert len(ALL_GATE_KEYS) == 21
    assert len(set(ALL_GATE_KEYS)) == 21


def test_v0_makes_no_physical_or_external_execution_claims():
    assert PHYSICAL_CHIP_BUILT is False
    assert RTL_IMPLEMENTED is False
    assert FPGA_LOADED is False
    assert EXTERNAL_EXECUTION_ENABLED is False

    status = SovereignDigitalSoCSimulator().status()
    assert status["physical_chip_built"] is False
    assert status["rtl_implemented"] is False
    assert status["fpga_loaded"] is False
    assert status["external_execution_enabled"] is False
    assert status["real_execution_count"] == 0


def test_boot_fails_closed_when_any_hardware_trust_gate_is_missing():
    simulator = SovereignDigitalSoCSimulator()
    evidence = _hardware_evidence()
    evidence["hardware_trust.secure_boot"] = False

    result = simulator.boot(evidence)

    assert result["booted"] is False
    assert result["state"] == "BLOCKED"
    assert result["missing_gates"] == ("secure_boot",)
    assert result["real_hardware_touched"] is False
    assert simulator.read_register("BOOT_STATE") == "BLOCKED"
    assert simulator.read_register("ACTIVE_ZONE") == "Recovery Zone"
    assert "GUARDIAN_BLOCK" in simulator.status()["interrupts"]


def test_boot_succeeds_only_as_an_in_memory_simulation():
    simulator = SovereignDigitalSoCSimulator()

    result = simulator.boot(_hardware_evidence())

    assert result["booted"] is True
    assert result["state"] == "READY"
    assert result["real_hardware_touched"] is False
    assert simulator.read_register("BOOT_STATE") == "READY"
    assert simulator.read_register("ACTIVE_ZONE") == "Device Zone"
    assert simulator.read_register("HRM_RECEIPT_COUNT") == 1
    assert simulator.status()["real_execution_count"] == 0


def test_nexus_messages_are_typed_internal_and_require_ready_boot():
    simulator = SovereignDigitalSoCSimulator()

    try:
        simulator.nexus_send(
            source="OAP CORE",
            target="Thalamus",
            message_type="CONTEXT",
            payload={"postcode": "SIMULATED"},
        )
    except RuntimeError as exc:
        assert "READY" in str(exc)
    else:
        raise AssertionError("NEXUS must reject messages before trusted boot")

    simulator.boot(_hardware_evidence())
    message = simulator.nexus_send(
        source="OAP CORE",
        target="Thalamus",
        message_type="CONTEXT",
        payload={"postcode": "SIMULATED"},
    )

    assert message["external_delivery"] is False
    assert message["source"] == "OAP CORE"
    assert message["target"] == "Thalamus"
    assert simulator.read_register("NEXUS_TX_COUNT") == 1


def test_consequential_action_is_blocked_when_21_gate_evidence_is_incomplete():
    simulator = SovereignDigitalSoCSimulator()
    simulator.boot(_hardware_evidence())
    evidence = _all_gate_evidence()
    evidence["human_authority.approval"] = False

    result = simulator.request_consequential_action("deploy", evidence)

    assert "deploy" in BLOCKED_HARDWARE_AUTONOMY
    assert result["simulation_result"] == "BLOCKED"
    assert result["gate_result"]["passed"] is False
    assert result["gate_result"]["passed_count"] == 20
    assert result["real_execution_performed"] is False
    assert simulator.read_register("REAL_EXECUTION_COUNT") == 0
    assert simulator.read_register("LAST_BLOCK_REASON") == "21_gate_evidence_incomplete"


def test_all_21_gates_only_authorize_a_simulated_result_never_real_execution():
    simulator = SovereignDigitalSoCSimulator()
    simulator.boot(_hardware_evidence())

    result = simulator.request_consequential_action("deploy", _all_gate_evidence())

    assert result["simulation_result"] == "AUTHORIZED_FOR_SIMULATION_ONLY"
    assert result["gate_result"]["passed"] is True
    assert result["gate_result"]["passed_count"] == 21
    assert result["real_execution_performed"] is False
    assert result["receipt"]["store"] == "SIMULATED_HRM_ONLY"
    assert len(result["receipt"]["sha256"]) == 64
    assert simulator.read_register("REAL_EXECUTION_COUNT") == 0


def test_interrupts_can_be_acknowledged_without_external_side_effects():
    simulator = SovereignDigitalSoCSimulator()
    simulator.boot(_hardware_evidence())

    pending_before = simulator.read_register("IRQ_PENDING")
    acknowledged = simulator.acknowledge_interrupt()

    assert pending_before >= 1
    assert acknowledged == "HRM_RECEIPT"
    assert simulator.read_register("IRQ_PENDING") == pending_before - 1
    assert simulator.status()["real_execution_count"] == 0
