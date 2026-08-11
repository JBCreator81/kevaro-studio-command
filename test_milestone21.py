from studio_command.decisions import (
    build_final_production_package,
    build_governed_production_runtime_state,
    build_production_decision_history_entry,
    build_production_execution_authorization,
    derive_production_workflow_state,
    record_studio_head_decision,
)
from studio_command.models import (
    AssetMediaPlan,
    ClearanceComplianceReport,
    ComplianceCheck,
    CreativeConcept,
    CreativeTreatment,
    EvidenceSource,
    FinalProductionPackage,
    MediaAssetRequirement,
    ProductionBrief,
    ProductionPlan,
    ProductionSchedule,
    ProductionTask,
    ResearchEvidence,
    ResearchPacket,
    ScheduledTask,
    StudioHeadDecisionPackage,
    VerificationFinding,
    VerificationQAReport,
)

PRODUCTION = "Luxury Wellness Campaign"


decision_package = StudioHeadDecisionPackage(
    production_name=PRODUCTION,
    executive_summary="Milestone 21 connected final-package validation.",
    qa_decision="PASS",
    readiness_score=100,
    clearance_status="CLEAR TO PROCEED",
    decision_items=[],
    material_blockers=[],
    conditions_for_approval=[],
    recommended_decision="APPROVE",
    decision_options=[
        "APPROVE",
        "APPROVE WITH CONDITIONS",
        "REQUEST CHANGES",
        "REJECT",
    ],
    final_warning="none",
)

decision = record_studio_head_decision(
    production_name=PRODUCTION,
    decision="APPROVE",
    conditions=[],
    decision_notes="Approved for final delivery.",
    decided_by="Studio Head",
    decision_package=decision_package,
    unresolved_risks_acknowledged=[],
)

workflow_state = derive_production_workflow_state(decision)

history = build_production_decision_history_entry(
    sequence=1,
    decision_record=decision,
    workflow_state=workflow_state,
)

runtime = build_governed_production_runtime_state(
    workflow_state=workflow_state,
    decision_history=[history],
    preserved_artifacts=[
        "Production Brief",
        "Research Packet",
        "Creative Treatment",
        "Production Plan",
        "Production Schedule",
        "Asset Media Plan",
        "Clearance Report",
        "Verification QA Report",
    ],
)

authorization = build_production_execution_authorization(
    runtime_state=runtime,
    requested_actions=[
        "Assemble final production package",
        "Release approved delivery artifacts",
    ],
)

assert authorization.may_execute is True


production_brief = ProductionBrief(
    production_title=PRODUCTION,
    production_type="Commercial",
    objective="Deliver a 30-second luxury wellness campaign.",
    target_audience="Premium wellness consumers",
    launch_or_delivery_date="next Friday",
    required_deliverables=["30-second hero video"],
    creative_constraints=["Quiet luxury visual language"],
    production_constraints=[],
    acceptance_criteria=["Final production passes QA and clearance"],
    research_questions=["What visual cues support premium wellness positioning?"],
    automatic_work=["Research and production planning"],
    approval_required=["Final creative approval"],
    assumptions=[],
    risks_or_unknowns=[],
)

research_packet = ResearchPacket(
    evidence=[
        ResearchEvidence(
            research_question="What visual cues support premium wellness positioning?",
            finding="Restrained design and premium visual treatment support the positioning.",
            sources=[
                EvidenceSource(
                    title="Validated production research",
                    url="https://example.com/research",
                    publisher_or_domain="example.com",
                    evidence_summary="Premium wellness creative benefits from restrained visual systems.",
                    production_relevance="Supports the approved creative direction.",
                    confidence="high",
                )
            ],
            production_impact="Supports creative treatment.",
            unresolved_questions=[],
            requires_studio_head_decision=False,
        )
    ],
    overall_summary="Research supports the approved production direction.",
    blockers=[],
)

concept = CreativeConcept(
    concept_name="Quiet Luxury Wellness",
    core_idea="Premium wellness expressed through calm, restrained cinematic imagery.",
    emotional_target="Trust and aspiration",
    visual_direction="Soft light, restrained palette, premium composition.",
    narrative_arc=["Open", "Experience", "Resolve"],
    key_messages=["Wellness can feel elevated and calm."],
    evidence_used=["Validated production research"],
    production_requirements=["Hero footage"],
    risks_or_tradeoffs=[],
)

creative_treatment = CreativeTreatment(
    recommended_concept=concept,
    alternate_concepts=[],
    script_direction="Minimal premium voiceover.",
    visual_system=["Restrained typography", "Soft premium lighting"],
    audio_direction="Subtle cinematic sound bed.",
    mandatory_elements=["Premium wellness positioning"],
    studio_head_approvals=[],
    unresolved_creative_questions=[],
)

production_plan = ProductionPlan(
    production_name=PRODUCTION,
    execution_summary="Execute the approved campaign.",
    tasks=[
        ProductionTask(
            task_name="Hero Production",
            responsible_role="Production Manager",
            deliverable="Approved hero asset",
            dependencies=[],
            completion_criteria=["Hero asset complete"],
            approval_required=False,
            risk_notes=[],
        )
    ],
    critical_path=["Hero Production"],
    parallel_workstreams=[],
    milestones=["Hero Complete"],
    approval_gates=[],
    blockers=[],
    schedule_risks=[],
    next_actions=["Complete hero production"],
)

production_schedule = ProductionSchedule(
    production_name=PRODUCTION,
    delivery_target="next Friday",
    scheduled_tasks=[
        ScheduledTask(
            task_name="Hero Production",
            responsible_role="Production Manager",
            sequence_position=1,
            depends_on=[],
            can_run_in_parallel_with=[],
            target_window="Final production window",
            completion_gate="Hero asset complete",
        )
    ],
    critical_path=["Hero Production"],
    parallel_execution_groups=[],
    approval_windows=[],
    schedule_buffer=[],
    deadline_threats=[],
    immediate_schedule_actions=["Complete hero production"],
)

asset_media_plan = AssetMediaPlan(
    production_name=PRODUCTION,
    asset_requirements=[
        MediaAssetRequirement(
            asset_name="Hero video",
            asset_type="video",
            purpose="Primary campaign deliverable",
            source_strategy="internally created",
            required_specifications=["30 seconds"],
            dependencies=[],
            licensing_or_rights=[],
            approval_required=False,
            readiness_status="ready",
        )
    ],
    immediately_actionable_assets=["Hero video"],
    blocked_assets=[],
    client_supplied_assets=[],
    generation_candidates=[],
    licensed_asset_needs=[],
    format_matrix=["16:9 master"],
    asset_risks=[],
    next_asset_actions=["Package hero video"],
)

clearance_report = ClearanceComplianceReport(
    production_name=PRODUCTION,
    compliance_checks=[
        ComplianceCheck(
            check_name="Final delivery rights",
            category="licensing",
            applies_to=["Hero video"],
            status="clear",
            evidence_required=[],
            blocking_issue="none",
            approval_required=False,
        )
    ],
    cleared_items=["Hero video"],
    blocked_items=[],
    unresolved_questions=[],
    required_documents=[],
    claim_restrictions=[],
    distribution_constraints=[],
    clearance_risks=[],
    clearance_decision="CLEAR TO PROCEED",
    next_clearance_actions=[],
)

verification_report = VerificationQAReport(
    production_name=PRODUCTION,
    findings=[
        VerificationFinding(
            finding_name="Final package verification",
            category="completeness",
            severity="info",
            status="passed",
            affected_items=["Hero video"],
            evidence=["Final QA review"],
            remediation="none",
        )
    ],
    passed_checks=["Final package verification"],
    failed_checks=[],
    unresolved_items=[],
    cross_artifact_conflicts=[],
    technical_validation=["Delivery format valid"],
    evidence_validation=["Production decisions remain supported"],
    readiness_score=100,
    qa_decision="PASS",
    next_qa_actions=[],
)

final_package = build_final_production_package(
    runtime_state=runtime,
    execution_authorization=authorization,
    production_brief=production_brief,
    research_packet=research_packet,
    creative_treatment=creative_treatment,
    production_plan=production_plan,
    production_schedule=production_schedule,
    asset_media_plan=asset_media_plan,
    clearance_report=clearance_report,
    verification_report=verification_report,
    delivery_artifacts=["gs://test-bucket/final/hero-video.mp4"],
    final_notes=["Final governed delivery package."],
)

assert isinstance(final_package, FinalProductionPackage)
assert final_package.production_name == PRODUCTION
assert final_package.decision_sequence == 1
assert final_package.delivery_status == "READY_FOR_DELIVERY"
assert final_package.readiness_score == 100
assert final_package.decision_history[-1].decision == "APPROVE"
assert final_package.authorized_actions == authorization.authorized_actions
assert final_package.production_plan is production_plan
assert final_package.production_schedule is production_schedule
assert final_package.asset_media_plan is asset_media_plan
assert final_package.clearance_report is clearance_report
assert final_package.verification_report is verification_report


blocked_authorization = authorization.model_copy(
    update={
        "authorization_status": "BLOCKED",
        "execution_mode": "BLOCKED",
        "authorized_actions": [],
        "blocked_actions": authorization.authorized_actions,
        "blockers": ["Test blocker"],
        "may_execute": False,
    }
)

try:
    build_final_production_package(
        runtime_state=runtime,
        execution_authorization=blocked_authorization,
        production_brief=production_brief,
        research_packet=research_packet,
        creative_treatment=creative_treatment,
        production_plan=production_plan,
        production_schedule=production_schedule,
        asset_media_plan=asset_media_plan,
        clearance_report=clearance_report,
        verification_report=verification_report,
        delivery_artifacts=["gs://test-bucket/final/hero-video.mp4"],
    )
    raise AssertionError("Blocked execution must not produce a final package.")
except ValueError:
    pass


failed_qa = verification_report.model_copy(
    update={
        "qa_decision": "FAIL",
        "readiness_score": 60,
    }
)

try:
    build_final_production_package(
        runtime_state=runtime,
        execution_authorization=authorization,
        production_brief=production_brief,
        research_packet=research_packet,
        creative_treatment=creative_treatment,
        production_plan=production_plan,
        production_schedule=production_schedule,
        asset_media_plan=asset_media_plan,
        clearance_report=clearance_report,
        verification_report=failed_qa,
        delivery_artifacts=["gs://test-bucket/final/hero-video.mp4"],
    )
    raise AssertionError("Failed QA must block final delivery.")
except ValueError:
    pass


print("MILESTONE 21 FINAL PRODUCTION PACKAGE VALIDATION: PASS")
print("MILESTONE 21 GOVERNED CORE CONNECTION: PASS")
print("MILESTONE 1-21 DELIVERY PATH INTEGRATION: PASS")
