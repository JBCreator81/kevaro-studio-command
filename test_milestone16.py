from studio_command.decisions import (
    analyze_production_change_impact,
    apply_change_impact_to_runtime,
    build_governed_production_runtime_state,
    build_production_decision_history_entry,
    build_studio_head_impact_brief,
    derive_production_workflow_state,
    record_studio_head_decision,
)
from studio_command.models import StudioHeadDecisionPackage


def make_package():
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Milestone 16 unified runtime test.",
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


# Human Studio Head approval
decision = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="APPROVE",
    conditions=[],
    decision_notes="Approved for production.",
    decided_by="Studio Head",
    decision_package=make_package(),
    unresolved_risks_acknowledged=[],
)

workflow_state = derive_production_workflow_state(decision)

history = build_production_decision_history_entry(
    sequence=1,
    decision_record=decision,
    workflow_state=workflow_state,
)

# Approved production enters governed runtime
runtime = build_governed_production_runtime_state(
    workflow_state=workflow_state,
    decision_history=[history],
    preserved_artifacts=[
        "Audience Research",
        "Campaign Strategy",
        "Hero Edit",
        "Social Cutdowns",
        "Talent Clearance",
    ],
)

assert runtime.execution_authorized is True
assert runtime.current_stage == "DOWNSTREAM_PRODUCTION"
assert runtime.memory_snapshot.active_decision_sequence == 1
assert runtime.memory_snapshot.known_good_state is True

# Studio Head issues a consequential production change
command = "Replace the approved lead talent."

impact = analyze_production_change_impact(
    runtime_state=runtime,
    requested_change=command,
    affected_work=[
        "Hero Edit",
        "Social Cutdowns",
        "Talent Clearance",
    ],
    preserved_work=[
        "Audience Research",
        "Campaign Strategy",
    ],
    approvals_invalidated=[
        "Lead Talent Approval",
    ],
    clearance_recheck_required=True,
    qa_reverification_required=True,
    schedule_impact=(
        "Casting, clearance, and affected edits must reopen before delivery."
    ),
    delivery_impact=(
        "Delivery may slip until replacement talent assets are cleared and re-verified."
    ),
)

assert impact.stale_work == [
    "Hero Edit",
    "Social Cutdowns",
    "Talent Clearance",
]

assert "Audience Research" in impact.preserved_work
assert "Campaign Strategy" in impact.preserved_work

# Kevaro explains the impact before execution
brief = build_studio_head_impact_brief(
    runtime_state=runtime,
    command=command,
    change_impact=impact,
    scope_confirmed=True,
    stale_decision_detected=False,
)

assert brief.impact_level == "HIGH"
assert brief.conflict_detected is True
assert brief.human_confirmation_required is True
assert brief.may_execute is False
assert "Hero Edit" in brief.production_explanation
assert "Audience Research" in brief.production_explanation

# Applying the impact must guard execution
guarded_runtime = apply_change_impact_to_runtime(
    runtime_state=runtime,
    change_impact=impact,
    impact_brief=brief,
)

assert guarded_runtime.execution_authorized is False
assert guarded_runtime.current_stage == "STUDIO_HEAD_IMPACT_REVIEW"
assert guarded_runtime.corrective_cycle_active is True

# Affected work becomes stale
assert "Hero Edit" in guarded_runtime.memory_snapshot.stale_artifacts
assert "Social Cutdowns" in guarded_runtime.memory_snapshot.stale_artifacts
assert "Talent Clearance" in guarded_runtime.memory_snapshot.stale_artifacts

# Unaffected work remains preserved
assert "Audience Research" in guarded_runtime.memory_snapshot.preserved_artifacts
assert "Campaign Strategy" in guarded_runtime.memory_snapshot.preserved_artifacts

# Affected work is no longer incorrectly treated as preserved
assert "Hero Edit" not in guarded_runtime.memory_snapshot.preserved_artifacts
assert "Social Cutdowns" not in guarded_runtime.memory_snapshot.preserved_artifacts
assert "Talent Clearance" not in guarded_runtime.memory_snapshot.preserved_artifacts

# Original approved runtime remains unchanged as the known-good prior state
assert runtime.execution_authorized is True
assert runtime.current_stage == "DOWNSTREAM_PRODUCTION"
assert runtime.memory_snapshot.stale_artifacts == []

# Ambiguous scope must also block execution
ambiguous_impact = analyze_production_change_impact(
    runtime_state=runtime,
    requested_change="Change everything.",
    affected_work=["Hero Edit"],
    preserved_work=["Audience Research"],
    approvals_invalidated=[],
    clearance_recheck_required=False,
    qa_reverification_required=False,
    schedule_impact="Exact schedule impact cannot be determined until scope is confirmed.",
    delivery_impact="Delivery impact is unknown until the command scope is clarified.",
)

ambiguous_brief = build_studio_head_impact_brief(
    runtime_state=runtime,
    command="Change everything.",
    change_impact=ambiguous_impact,
    scope_confirmed=False,
    stale_decision_detected=False,
)

assert ambiguous_brief.impact_level == "HIGH"
assert ambiguous_brief.scope_confirmed is False
assert ambiguous_brief.human_confirmation_required is True
assert ambiguous_brief.may_execute is False

# Stale approval information must block execution
stale_brief = build_studio_head_impact_brief(
    runtime_state=runtime,
    command=command,
    change_impact=impact,
    scope_confirmed=True,
    stale_decision_detected=True,
)

assert stale_brief.stale_decision_detected is True
assert stale_brief.may_execute is False

# Affected and preserved work may never overlap
try:
    analyze_production_change_impact(
        runtime_state=runtime,
        requested_change="Invalid overlap test.",
        affected_work=["Hero Edit"],
        preserved_work=["Hero Edit"],
        approvals_invalidated=[],
        clearance_recheck_required=False,
        qa_reverification_required=False,
        schedule_impact="none",
        delivery_impact="none",
    )
    raise AssertionError(
        "Affected and preserved work overlap should fail."
    )
except ValueError:
    pass


print("MILESTONE 16 UNIFIED GOVERNED RUNTIME VALIDATION: PASS")
