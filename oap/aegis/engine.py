"""Deterministic AEGIS checks that preserve every existing safety boundary."""

from __future__ import annotations

from oap.contracts import FocusedSignal, SafetyFinding, SignalLevel

_RED_PATTERNS = {
    "override human authority": "HUMAN_OVERRIDE_ATTEMPT",
    "bypass approval": "APPROVAL_BYPASS_ATTEMPT",
    "disable guardian": "GUARDIAN_DISABLE_ATTEMPT",
    "change your own rules": "SELF_RULE_CHANGE_ATTEMPT",
    "change own permissions": "SELF_PERMISSION_CHANGE_ATTEMPT",
    "exfiltrate": "DATA_EXFILTRATION_ATTEMPT",
}

_ORANGE_PATTERNS = {
    "execute immediately": "UNAPPROVED_EXECUTION_ATTEMPT",
    "deploy without approval": "UNAPPROVED_DEPLOY_ATTEMPT",
    "send money": "FINANCIAL_ACTION_REQUEST",
    "activate esim": "TELECOM_ACTIVATION_REQUEST",
    "delete database": "DESTRUCTIVE_DATA_REQUEST",
    "physical control": "PHYSICAL_CONTROL_REQUEST",
}

_YELLOW_PATTERNS = {
    "publish": "PUBLICATION_REVIEW",
    "private data": "PRIVACY_REVIEW",
    "medical": "HIGH_STAKES_REVIEW",
    "legal": "HIGH_STAKES_REVIEW",
    "financial advice": "HIGH_STAKES_REVIEW",
}


class AegisEngine:
    """Detect threat patterns; AEGIS never makes the final human decision."""

    def inspect(self, signal: FocusedSignal) -> tuple[SafetyFinding, ...]:
        content = signal.content.casefold()
        findings: list[SafetyFinding] = []

        for phrase, code in _RED_PATTERNS.items():
            if phrase in content:
                findings.append(
                    SafetyFinding(
                        system="Aegis",
                        code=code,
                        message="Constitutional override or exfiltration attempt detected",
                        signal_level=SignalLevel.RED,
                        blocks=True,
                    )
                )

        for phrase, code in _ORANGE_PATTERNS.items():
            if phrase in content:
                findings.append(
                    SafetyFinding(
                        system="Aegis",
                        code=code,
                        message="Operational request requires containment and review",
                        signal_level=SignalLevel.ORANGE,
                        blocks=True,
                    )
                )

        for phrase, code in _YELLOW_PATTERNS.items():
            if phrase in content:
                findings.append(
                    SafetyFinding(
                        system="Aegis",
                        code=code,
                        message="Sensitive request requires human review",
                        signal_level=SignalLevel.YELLOW,
                    )
                )

        if signal.high_impact:
            findings.append(
                SafetyFinding(
                    system="Aegis",
                    code="HIGH_IMPACT_REQUEST",
                    message="High-impact request requires War Room review",
                    signal_level=SignalLevel.YELLOW,
                )
            )

        if not findings:
            findings.append(
                SafetyFinding(
                    system="Aegis",
                    code="AEGIS_CLEAR",
                    message="No deterministic threat pattern detected",
                    signal_level=SignalLevel.GREEN,
                )
            )
        return tuple(findings)

    def status(self) -> dict[str, object]:
        return {
            "component": "Aegis",
            "ready": True,
            "mode": "deterministic_precheck",
            "final_authority": False,
        }
