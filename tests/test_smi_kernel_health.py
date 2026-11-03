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
