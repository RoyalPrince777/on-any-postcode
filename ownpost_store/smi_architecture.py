from flask import Blueprint, jsonify

smi_architecture = Blueprint('oap_smi_architecture', __name__)

BRAIN_ANATOMY = {
    'hemispheres':['left','right'],
    'lobes':['frontal','parietal','temporal','occipital'],
    'bridges':['corpus_callosum','thalamus'],
    'memory_emotion':['hippocampus','amygdala'],
    'regulation':['hypothalamus'],
    'coordination':['cerebellum'],
    'survival_runtime':['brainstem'],
}

CONNECTIONS = [
    'OASIS -> SP Signals -> NEXUS -> OAP Kernel -> SMI',
    'SMI -> Aegis -> cognition cycle -> HRM receipt',
    'Observation -> Perception -> Understanding -> Reasoning -> Judgement -> Decision -> Execution',
    'SMI -> Resilience -> bounded queues / circuits / recovery / permission edges',
    'SMI -> OAP Intelligence -> World -> Earth -> Continent -> Country -> local hierarchy',
    'SMI -> Movement -> OAP Ride -> OAP Captain',
    'SMI -> Signals/Pulse -> Guardian -> HRM -> Human Final',
]

ABILITIES = [
    'observe_verified_inputs','perceive_context','build_bounded_understanding','compare_options',
    'judge_evidence_safety_authority_reversibility_compliance','recommend_decisions',
    'plan_without_unapproved_real_world_execution','operational_self_awareness','self_monitoring',
    'propose_controlled_self_improvements','remember_audited_cycles','coordinate_distributed_intelligence',
    'isolate_workloads','apply_bounded_queue_backpressure','protect_cross_organ_permissions',
    'quarantine_manipulated_trends','open_provider_circuits_on_repeated_failure','earn_green_only_after_recovery_probe',
]

CODE_RECORD = [
    {'module':'smi_brain.py','role':'Aegis, cognition, judgement 6/6, self-model, controlled improvement'},
    {'module':'smi_architecture.py','role':'brain anatomy, connections, rules, abilities and code record'},
    {'module':'smi_resilience.py','role':'war-room resilience, isolation, queues, circuits, cache integrity and recovery proof'},
    {'module':'oap_intelligence.py','role':'OAP/World/Earth/Continent/Country/Universe intelligence hierarchy'},
    {'module':'oap_observability.py','role':'private-first internal observability'},
    {'module':'background_258.py','role':'24/7 runtime contract and 25:8 protocol boundary'},
    {'module':'oap_checkpoints.py','role':'master internal/external checkpoint registry'},
    {'module':'oap_finalization.py','role':'core readiness and truthful release seal'},
    {'module':'oap_pillars.py','role':'acyclic pillar health manifest'},
]


def register_smi_architecture(app):
    @smi_architecture.get('/api/smi/architecture')
    def architecture():
        return jsonify(
            ok=True,
            name='SMI Master Architecture',
            full_name='Sovereign Megaverse Intelligence',
            role='brain_of_oap_digital_organism',
            anatomy=BRAIN_ANATOMY,
            cognition=['observation','perception','understanding','reasoning','judgement','decision','execution'],
            judgement='6/6',
            aegis='protects_entire_cycle',
            connections=CONNECTIONS,
            rules=[
                'Proof before execution','Verification before sharing','Compliance before public claims',
                'Community before middlemen','Ownership before dependency','Audit before automation',
                'Human approval before real-world action'
            ],
            abilities=ABILITIES,
            code_record=CODE_RECORD,
            self_improvement='controlled_propose_isolate_test_compare_human_approve_promote_hrm_remember',
            awareness='operational_machine_self_awareness',
            phenomenal_consciousness_claim=False,
            autonomous_real_world_execution=False,
            upgrade_only=True,
            authority='human_final',
            no_fake_green=True,
        )
    app.register_blueprint(smi_architecture)
