from mission_control.silicon_architecture import SILICON_GATES
from mission_control.sovereign_digital_soc_v02 import (
    MEMORY_MAP,
    MMIO_REGISTERS,
    ORGAN_INTERFACES,
    REAL_ATTESTATION_ENABLED,
    REAL_DMA_ENABLED,
    REAL_MMIO_ENABLED,
    REAL_ORGAN_EXECUTION_ENABLED,
    SovereignDigitalSoCV02Simulator,
    validate_v02_contract,
    v02_contract,
)


def _hardware_evidence(value: bool = True) -> dict[str, bool]:
    return {f"hardware_trust.{gate}": value for gate in SILICON_GATES["hardware_trust"]}


def test_v02_contract_is_hardware_shaped_but_simulation_only():
    validate_v02_contract()
    contract = v02_contract()

    assert contract["version"] == "0.2.0"
    assert contract["cognitive_authority"] == "SMI Brain"
    assert contract["final_authority"] == "Human Authority"
    assert contract["gate_count"] == 21
    assert len(MEMORY_MAP) == 10
    assert len(MMIO_REGISTERS) == 7
    assert len(ORGAN_INTERFACES) == 13
    assert REAL_DMA_ENABLED is False
    assert REAL_MMIO_ENABLED is False
    assert REAL_ATTESTATION_ENABLED is False
    assert REAL_ORGAN_EXECUTION_ENABLED is False


def test_protected_memory_rejects_cross_zone_access():
    simulator = SovereignDigitalSoCV02Simulator()
    address = 0x2000_0000

    simulator.bus_write(address, 7, requester_zone="HRM Zone")
    assert simulator.bus_read(address, requester_zone="HRM Zone") == 7

    try:
        simulator.bus_read(address, requester_zone="Public Zone")
    except PermissionError:
        pass
    else:
        raise AssertionError("Cross-zone HRM memory access must fail closed")


def test_mmio_access_rules_are_enforced():
    simulator = SovereignDigitalSoCV02Simulator()

    assert simulator.bus_read(0x1000_0000, requester_zone="Guardian Zone") == 1
    try:
        simulator.bus_write(0x1000_0000, 0, requester_zone="Guardian Zone")
    except PermissionError:
        pass
    else:
        raise AssertionError("Read-only Guardian MMIO must reject writes")


def test_interrupt_priority_puts_guardian_block_first():
    simulator = SovereignDigitalSoCV02Simulator()
    simulator.raise_prioritised_interrupt("NEXUS_MESSAGE")
    simulator.raise_prioritised_interrupt("WATCHDOG")
    simulator.raise_prioritised_interrupt("GUARDIAN_BLOCK")

    assert simulator.acknowledge_interrupt() == "GUARDIAN_BLOCK"
    assert simulator.acknowledge_interrupt() == "WATCHDOG"
    assert simulator.acknowledge_interrupt() == "NEXUS_MESSAGE"


def test_iommu_blocks_dma_outside_device_domain():
    simulator = SovereignDigitalSoCV02Simulator()
    simulator.configure_dma_domain("sensor0", ("DEVICE_BUFFER",))

    blocked = simulator.dma_transfer("sensor0", 0x2400_0000, 0x2000_0000, 1)
    assert blocked == {"permitted": False, "bytes": 0, "real_dma": False}
    assert simulator.acknowledge_interrupt() == "GUARDIAN_BLOCK"


def test_dma_copy_is_simulated_only_inside_allowed_domain():
    simulator = SovereignDigitalSoCV02Simulator()
    simulator.configure_dma_domain("sensor0", ("DEVICE_BUFFER",))
    simulator.bus_write(0x2400_0000, 42, requester_zone="Device Zone")

    result = simulator.dma_transfer("sensor0", 0x2400_0000, 0x2400_0010, 1)

    assert result == {"permitted": True, "bytes": 1, "real_dma": False}
    assert simulator.bus_read(0x2400_0010, requester_zone="Device Zone") == 42


def test_boot_measurements_and_attestation_are_not_hardware_backed():
    simulator = SovereignDigitalSoCV02Simulator()
    boot = simulator.boot(_hardware_evidence())

    assert boot["booted"] is True
    assert len(boot["measurements"]) == 4
    assert all(len(item["sha256"]) == 64 for item in boot["measurements"])

    attestation = simulator.attest("challenge-1")
    assert attestation["hardware_backed"] is False
    assert attestation["store"] == "SIMULATED_ONLY"
    assert len(attestation["sha256"]) == 64


def test_all_13_organs_have_simulation_only_interfaces():
    simulator = SovereignDigitalSoCV02Simulator()
    simulator.boot(_hardware_evidence())

    for interface in ORGAN_INTERFACES:
        result = simulator.organ_signal(interface["organ_id"], {"intent": "observe"})
        assert result["organ_execution_performed"] is False
        assert result["external_delivery"] is False

    status = simulator.v02_status()
    assert status["organ_interfaces"] == 13
    assert status["real_execution_count"] == 0
