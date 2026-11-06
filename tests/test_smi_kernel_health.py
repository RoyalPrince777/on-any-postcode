"""Regression tests for the SMI–Living Kernel health boundary."""

from oap.smi.health import SMIHealthService


class _Status:
    def __init__(self, value):
        self.value = value

    def status(self):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def test_smi_health_degrades_when_kernel_not_wired():
    report = SMIHealthService(_Status({"ready": True})).check()
    assert report["status"] == "degraded"
    assert report["kernel"]["reason"] == "Not wired"


def test_smi_health_requires_both_brain_and_kernel():
    assert SMIHealthService(
        _Status({"ready": True}), _Status({"ready": True})
    ).check()["status"] == "healthy"
    assert SMIHealthService(
        _Status({"ready": False}), _Status({"ready": True})
    ).check()["status"] == "degraded"
    assert SMIHealthService(
        _Status({"ready": True}), _Status({"ready": False})
    ).check()["status"] == "degraded"


def test_smi_health_rejects_invalid_or_failed_status_probes():
    for unhealthy in (None, {"ready": "yes"}, RuntimeError("secret")):
        report = SMIHealthService(
            _Status({"ready": True}), _Status(unhealthy)
        ).check()
        assert report["status"] == "degraded"
        assert "secret" not in str(report)

    report = SMIHealthService(
        _Status(RuntimeError("private")), _Status({"ready": True})
    ).check()
    assert report["status"] == "degraded"
    assert report["brain"]["reason"] == "status_unavailable"


def test_smi_health_identifies_each_unready_component_without_guessing():
    cases = (
        (True, True, ()),
        (False, True, ("brain",)),
        (True, False, ("living_kernel",)),
        (False, False, ("brain", "living_kernel")),
    )
    for brain_ready, kernel_ready, blockers in cases:
        report = SMIHealthService(
            _Status({"ready": brain_ready}), _Status({"ready": kernel_ready})
        ).check()
        assert report["readiness_blockers"] == blockers
        assert report["status"] == ("degraded" if blockers else "healthy")


def test_smi_health_unwired_kernel_reports_explicit_blocker():
    report = SMIHealthService(_Status({"ready": True})).check()
    assert report["readiness_blockers"] == ("living_kernel",)
    assert report["independent_execute"] is False
    assert report["human_approval_final"] is True
