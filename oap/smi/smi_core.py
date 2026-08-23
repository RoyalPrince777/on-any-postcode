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

from .coherence_engine import AdaptiveCoherenceEngine
from .context_engine import ContextEngine
from .input_manager import InputManager
from .judge_engine import JudgeEngine
from .organ_manager import OrganManager
from .organs import FrontalLobe
from .organs.base import BrainPacket
from .providers import ProviderRouter


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
        coherence: AdaptiveCoherenceEngine,
        war_room: WarRoomEngine,
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
        self.coherence = coherence
        self.war_room = war_room
        self.hrm = hrm
        self.input_manager = InputManager()
        self.frontal_lobe = FrontalLobe()

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
        coherence = self.coherence.assess(analysis)
        output_state = self.judge.decide(request, analysis, safety, coherence)
        summary, rationale = self.frontal_lobe.form_summary(
            request.task_type,
            analysis,
            safety,
        )
        rationale = (
            *rationale,
            advisors.reason,
            f"Coherence score: {coherence.score}/100.",
            coherence.adaptive_proposal,
        )
        war_room = self.war_room.review(request, analysis, safety, output_state)

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
            coherence=coherence,
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
            ),
        )
        self.hrm.record_recommendation(request, recommendation)
        return recommendation

    def status(self) -> dict[str, object]:
        components = (
            self.nexus.status(),
            self.identity.status(),
            self.registry.status(),
            self.providers.status(),
            self.organs.status(),
            self.aegis.status(),
            self.guardian.status(),
            self.coherence.status(),
            self.war_room.status(),
            self.hrm.status(),
        )
        return {
            "component": "SMI",
            "brain_count": 1,
            "ready": all(bool(item.get("ready")) for item in components),
            "mode": "recommendation_only",
            "allowed_outputs": tuple(state.value for state in OutputState),
            "independent_execute": False,
            "components": components,
        }
