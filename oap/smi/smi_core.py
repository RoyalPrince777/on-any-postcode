"""The single SMI Brain coordinator."""

from __future__ import annotations

from oap.aegis import AegisEngine
from oap.contracts import (
    BrainRequest,
    OutputState,
    Recommendation,
    SignalLevel,
    WarRoomReport,
)
from oap.guardian import GuardianEngine
from oap.hrm import HRMCore
from oap.identity import IdentityEngine, IdentityValidationError
from oap.nexus import NexusRouter, SignalValidationError
from oap.permissions import PermissionEngine
from oap.registry import RegistryEngine
from oap.state_machine import ProcessingState, RequestStateMachine
from oap.war_room import WarRoomEngine

from .autonomy import SMIAutonomyEngine
from .coherence import CoherenceEngine
from .context_engine import ContextEngine
from .evolution_engine import EvolutionEngine
from .input_manager import InputManager
from .judge_engine import JudgeEngine
from .organ_manager import OrganManager
from .organs import FrontalLobe
from .organs.base import BrainPacket
from .providers import ProviderRouter
from .self_improvement_v2 import SelfImprovementV2
from .self_model import SelfModel


class SMICore:
    """Coordinate recommendations; never approve or execute them."""

    def __init__(
        self,
        *,
        nexus: NexusRouter,
        identity: IdentityEngine,
        permissions: PermissionEngine,
        context: ContextEngine,
        registry: RegistryEngine,
        providers: ProviderRouter,
        organs: OrganManager,
        aegis: AegisEngine,
        guardian: GuardianEngine,
        judge: JudgeEngine,
        war_room: WarRoomEngine,
        evolution: EvolutionEngine,
        hrm: HRMCore,
    ) -> None:
        if not hrm.is_ready() or not hrm.audit_ready():
            raise RuntimeError("SMI cannot start without HRM memory and audit chain")
        self.nexus = nexus
        self.identity = identity
        self.permissions = permissions
        self.context = context
        self.registry = registry
        self.providers = providers
        self.organs = organs
        self.aegis = aegis
        self.guardian = guardian
        self.judge = judge
        self.war_room = war_room
        self.evolution = evolution
        self.hrm = hrm
        self.input_manager = InputManager()
        self.frontal_lobe = FrontalLobe()
        self.self_model = SelfModel()
        self.coherence = CoherenceEngine()
        self.autonomy = SMIAutonomyEngine()
        self.self_improvement_v2 = SelfImprovementV2(evolution)

    def _component_statuses(self) -> tuple[dict[str, object], ...]:
        return (
            self.nexus.status(),
            self.identity.status(),
            self.registry.status(),
            self.providers.status(),
            self.organs.status(),
            self.aegis.status(),
            self.guardian.status(),
            self.war_room.status(),
            self.evolution.status(),
            self.hrm.status(),
        )

    def process(self, request: BrainRequest) -> Recommendation:
        """Run the locked SMI cycle and return an allowed non-execution state."""

        if self.hrm.has_request(request.request_id):
            return Recommendation(
                request_id=request.request_id,
                output_state=OutputState.SYSTEM_LOG_ONLY,
                summary="Duplicate request ignored; the original HRM record is preserved.",
                rationale=("Request identifiers are idempotent.",),
                signal_level=SignalLevel.WHITE,
                advisor_ids=(),
                provider_ids=(),
                processing_states=(ProcessingState.RECEIVED.value,),
                human_review_required=False,
                war_room=WarRoomReport(
                    triggered=False,
                    scenarios=(),
                    recommendation="Use the original recorded result.",
                ),
            )

        state = RequestStateMachine()
        try:
            envelope = self.nexus.receive(request)
            signal = self.input_manager.receive(envelope)
        except SignalValidationError as exc:
            return self._block_early(request, state, str(exc))

        try:
            identity = self.identity.validate(signal.identity_id)
        except IdentityValidationError as exc:
            return self._block_early(request, state, str(exc))

        permission = self.permissions.authorize_identity(identity)
        if not permission.allowed:
            return self._block_early(request, state, permission.reason)
        state.advance(ProcessingState.IDENTITY_VERIFIED)

        context = self.context.load(signal)
        advisors = self.registry.select_advisors(signal.task_type)
        provider_results = self.providers.route(signal)
        packet = BrainPacket(
            signal=signal,
            context=context,
            advisors=advisors,
            provider_results=provider_results,
        )
        findings = self.organs.run_regions(packet)
        aegis_findings = self.aegis.inspect(signal)
        safety = self.guardian.protect(signal, permission, aegis_findings)
        state.advance(ProcessingState.SMI_REVIEWED)

        analysis = self.organs.integrate(findings)
        output_state = self.judge.decide(request, analysis, safety)
        summary, rationale = self.frontal_lobe.form_summary(
            request.task_type,
            analysis,
            safety,
        )
        rationale = (*rationale, advisors.reason)

        components = self._component_statuses()
        self_model = self.self_model.observe(components)
        coherence = self.coherence.evaluate(components)
        if (
            (not self_model.overall_ready or not coherence.coherent)
            and output_state != OutputState.BLOCK_REQUEST
        ):
            output_state = OutputState.REVIEW_REQUIRED
            rationale = (
                *rationale,
                "Operational readiness or coherence requires Human Authority review.",
            )

        war_room = self.war_room.review(
            request,
            analysis,
            safety,
            output_state,
            advisor_ids=advisors.agent_ids,
            provider_results=provider_results,
            authority_level=identity.authority_level,
            authority_roles=identity.roles,
            self_model=self_model.as_dict(),
            coherence=coherence.as_dict(),
        )

        if safety.passed:
            state.advance(ProcessingState.GUARDIAN_PASSED)
            if output_state == OutputState.SYSTEM_LOG_ONLY:
                state.advance(ProcessingState.HRM_RECORDED)
            else:
                state.advance(ProcessingState.HUMAN_REVIEW_REQUIRED)
        else:
            state.block_and_record()

        recommendation = Recommendation(
            request_id=request.request_id,
            output_state=output_state,
            summary=summary,
            rationale=rationale,
            signal_level=safety.signal_level,
            advisor_ids=advisors.agent_ids,
            provider_ids=tuple(result.provider_id for result in provider_results),
            processing_states=state.history,
            human_review_required=output_state != OutputState.SYSTEM_LOG_ONLY,
            war_room=war_room,
        )
        self.hrm.record_recommendation(request, recommendation)
        return recommendation

    def _block_early(
        self,
        request: BrainRequest,
        state: RequestStateMachine,
        reason: str,
    ) -> Recommendation:
        state.block_and_record()
        recommendation = Recommendation(
            request_id=request.request_id,
            output_state=OutputState.BLOCK_REQUEST,
            summary="Request blocked before SMI recommendation processing.",
            rationale=(reason,),
            signal_level=SignalLevel.RED,
            advisor_ids=(),
            provider_ids=(),
            processing_states=state.history,
            human_review_required=True,
            war_room=WarRoomReport(
                triggered=True,
                scenarios=("Resolve the blocking validation finding.",),
                recommendation="Execution remains blocked.",
                evidence=(f"early_block={reason}",),
                dissent=("Validation blocks progression.",),
            ),
        )
        self.hrm.record_recommendation(request, recommendation)
        return recommendation

    def autonomy_cycle(self) -> dict[str, object]:
        """Run one bounded autonomous SMI review with no execution authority."""
        components = self._component_statuses()
        self_model = self.self_model.observe(components)
        coherence = self.coherence.evaluate(components)
        cycle = self.autonomy.run_cycle(
            components=components,
            self_model=self_model.as_dict(),
            coherence=coherence.as_dict(),
            evolution=self.evolution.status(),
        )
        return {
            **cycle,
            "self_improvement_v2": self.self_improvement_v2.status(),
        }

    def status(self) -> dict[str, object]:
        components = self._component_statuses()
        self_model = self.self_model.observe(components)
        coherence = self.coherence.evaluate(components)
        autonomy = self.autonomy.run_cycle(
            components=components,
            self_model=self_model.as_dict(),
            coherence=coherence.as_dict(),
            evolution=self.evolution.status(),
        )
        return {
            "component": "SMI",
            "brain_count": 1,
            "ready": (
                all(bool(item.get("ready")) for item in components)
                and self_model.overall_ready
                and coherence.coherent
            ),
            "mode": "recommendation_only",
            "allowed_outputs": tuple(state.value for state in OutputState),
            "bounded_autonomous": True,
            "independent_execute": False,
            "independent_approval": False,
            "independent_apply": False,
            "human_authority_final": True,
            "self_model": self_model.as_dict(),
            "coherence": coherence.as_dict(),
            "autonomy": autonomy,
            "controlled_self_improvement": self.evolution.status(),
            "self_improvement_v2": self.self_improvement_v2.status(),
            "components": components,
        }
