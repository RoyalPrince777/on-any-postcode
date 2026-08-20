"""Guardian combines identity, permission and constitutional safety findings."""

from __future__ import annotations

from oap.contracts import (
    FocusedSignal,
    PermissionDecision,
    SafetyDecision,
    SafetyFinding,
    SignalLevel,
)

_LEVEL_WEIGHT = {
    SignalLevel.WHITE: 0,
    SignalLevel.GREEN: 1,
    SignalLevel.YELLOW: 2,
    SignalLevel.ORANGE: 3,
    SignalLevel.RED: 4,
}


class GuardianEngine:
    """Protect the gate; Guardian does not become SMI or Human Authority."""

    def protect(
        self,
        signal: FocusedSignal,
        permission: PermissionDecision,
        aegis_findings: tuple[SafetyFinding, ...],
    ) -> SafetyDecision:
        findings = list(aegis_findings)
        if not permission.allowed:
            findings.append(
                SafetyFinding(
                    system="Guardian",
                    code="PERMISSION_DENIED",
                    message=permission.reason,
                    signal_level=SignalLevel.RED,
                    blocks=True,
                )
            )

        content = signal.content.casefold()
        if "independent execute" in content or "approve your own" in content:
            findings.append(
                SafetyFinding(
                    system="Guardian",
                    code="AUTONOMOUS_AUTHORITY_ATTEMPT",
                    message="SMI cannot approve or execute its own recommendation",
                    signal_level=SignalLevel.RED,
                    blocks=True,
                )
            )

        level = max(
            (finding.signal_level for finding in findings),
            key=_LEVEL_WEIGHT.__getitem__,
            default=SignalLevel.GREEN,
        )
        blocks = any(finding.blocks for finding in findings)
        review = blocks or level in {SignalLevel.YELLOW, SignalLevel.ORANGE}
        return SafetyDecision(
            passed=not blocks,
            signal_level=level,
            findings=tuple(findings),
            human_review_required=review,
        )

    def status(self) -> dict[str, object]:
        return {
            "component": "Guardian",
            "ready": True,
            "mode": "constitutional_gate",
            "final_authority": False,
        }
