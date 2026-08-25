"""Bounded consequence simulation for complex or high-impact requests."""

from __future__ import annotations

from collections.abc import Mapping

from oap.contracts import (
    BrainRequest,
    IntegratedAnalysis,
    OutputState,
    ProviderResult,
    SafetyDecision,
    WarRoomReport,
)


class WarRoomEngine:
    """Build evidence-backed scenarios without granting decision authority."""

    @staticmethod
    def _coherence_conflicts(
        coherence: Mapping[str, object] | None,
    ) -> tuple[str, ...]:
        if not coherence:
            return ()
        conflicts = coherence.get("conflicts")
        if not isinstance(conflicts, (tuple, list)):
            return ()
        values: list[str] = []
        for item in conflicts:
            if isinstance(item, Mapping):
                claim = str(item.get("claim") or "unknown")
                raw_values = item.get("values")
                if isinstance(raw_values, (tuple, list)):
                    rendered = ", ".join(str(value) for value in raw_values)
                    values.append(f"{claim} -> {rendered}")
                else:
                    values.append(claim)
            else:
                values.append(str(item))
        return tuple(values)

    @staticmethod
    def _degraded_components(
        self_model: Mapping[str, object] | None,
    ) -> tuple[str, ...]:
        if not self_model:
            return ()
        degraded = self_model.get("degraded_components")
        unknown = self_model.get("unknown_components")
        values: list[str] = []
        for source in (degraded, unknown):
            if isinstance(source, (tuple, list)):
                values.extend(str(item) for item in source)
        return tuple(dict.fromkeys(values))

    def review(
        self,
        request: BrainRequest,
        analysis: IntegratedAnalysis,
        safety: SafetyDecision,
        output_state: OutputState,
        *,
        advisor_ids: tuple[str, ...] = (),
        provider_results: tuple[ProviderResult, ...] = (),
        authority_level: int | None = None,
        authority_roles: tuple[str, ...] = (),
        self_model: Mapping[str, object] | None = None,
        coherence: Mapping[str, object] | None = None,
    ) -> WarRoomReport:
        conflicts = self._coherence_conflicts(coherence)
        degraded = self._degraded_components(self_model)
        unavailable = tuple(
            result.provider_id for result in provider_results if not result.available
        )
        blocking_codes = tuple(
            finding.code for finding in safety.findings if finding.blocks
        )
        triggered = (
            request.high_impact
            or safety.human_review_required
            or bool(conflicts)
            or bool(degraded)
            or output_state
            in {
                OutputState.REVIEW_REQUIRED,
                OutputState.BLOCK_REQUEST,
            }
        )

        participants = tuple(
            dict.fromkeys(
                (
                    "Integrated Analysis",
                    "Guardian",
                    "Coherence",
                    *advisor_ids,
                    *(result.provider_id for result in provider_results),
                )
            )
        )
        positions = [
            f"Guardian: {'PASS' if safety.passed else 'BLOCK'}",
            f"Integrated Analysis: {analysis.signal_level.value} at {analysis.confidence:.0%}",
            f"Coherence: {'REVIEW' if conflicts else 'COHERENT'}",
        ]
        positions.extend(f"{advisor_id}: ADVISORY_PARTICIPANT" for advisor_id in advisor_ids)
        positions.extend(
            f"{result.provider_id}: {'AVAILABLE' if result.available else 'UNAVAILABLE'}"
            for result in provider_results
        )
        if authority_level is not None:
            role_text = ", ".join(authority_roles) or "unassigned"
            positions.append(f"Authority: level {authority_level} ({role_text})")

        evidence = [
            f"output_state={output_state.value}",
            f"signal_level={safety.signal_level.value}",
            f"analysis_confidence={analysis.confidence:.2f}",
        ]
        evidence.extend(f"guardian_blocker={code}" for code in blocking_codes)
        evidence.extend(f"provider_unavailable={provider}" for provider in unavailable)
        evidence.extend(f"coherence_conflict={conflict}" for conflict in conflicts)
        evidence.extend(f"component_degraded={component}" for component in degraded)

        dissent: list[str] = []
        if not safety.passed:
            dissent.append("Guardian blocks progression.")
        if conflicts:
            dissent.append("Coherence engine reports unresolved disagreement.")
        if unavailable:
            dissent.append("One or more approved providers are unavailable.")
        if degraded:
            dissent.append("Self Model reports degraded or unknown components.")
        if analysis.confidence < 0.75:
            dissent.append("Integrated analysis confidence is below 75%.")

        if not triggered:
            return WarRoomReport(
                triggered=False,
                scenarios=(),
                recommendation="Standard Human Authority review remains required.",
                evidence=tuple(evidence),
                participants=participants,
                positions=tuple(positions),
                dissent=tuple(dissent),
                authority_level=authority_level,
                coherence_conflicts=conflicts,
            )

        scenarios: list[str] = []
        if not safety.passed:
            codes = ", ".join(blocking_codes) or "Guardian safety findings"
            scenarios.append(f"Reject progression while blockers remain: {codes}.")
        else:
            scenarios.append(
                "Proceed only after Human Authority verifies evidence, permissions and rollback controls."
            )

        if unavailable:
            scenarios.append(
                "Delay until unavailable approved providers recover or an explicitly approved alternative is selected: "
                + ", ".join(unavailable)
                + "."
            )
        elif analysis.confidence < 0.75:
            scenarios.append(
                f"Delay for more evidence because integrated confidence is {analysis.confidence:.0%}."
            )
        else:
            scenarios.append(
                "Validate provider evidence and assumptions before any Builder action is prepared."
            )

        if conflicts:
            scenarios.append(
                "Pause and reconcile coherence conflicts before progression: "
                + "; ".join(conflicts)
                + "."
            )
        elif degraded:
            scenarios.append(
                "Delay while Self Model degradation is resolved: "
                + ", ".join(degraded)
                + "."
            )
        else:
            scenarios.append(
                "Reject or roll back if the proposed path becomes irreversible or exceeds approved scope."
            )

        if not safety.passed or conflicts:
            recommendation = "Block progression and record the evidence for Human Authority review."
        elif authority_level != 0:
            recommendation = (
                "Escalate the evidence package to level-zero Human Authority; "
                "War Room has no approval authority."
            )
        else:
            recommendation = (
                "Level-zero Human Authority should compare benefit, risk, dissent and reversibility; "
                f"internal confidence is {analysis.confidence:.0%}."
            )

        return WarRoomReport(
            triggered=True,
            scenarios=tuple(scenarios),
            recommendation=recommendation,
            evidence=tuple(evidence),
            participants=participants,
            positions=tuple(positions),
            dissent=tuple(dissent),
            authority_level=authority_level,
            human_authority_final=True,
            coherence_conflicts=conflicts,
            reversibility_required=True,
        )

    def status(self) -> dict[str, object]:
        return {
            "component": "War Room",
            "ready": True,
            "version": 2,
            "mode": "simulation_only",
            "decision_authority": False,
            "evidence_driven": True,
            "authority_context": True,
            "coherence_context": True,
            "reversibility_required": True,
        }
