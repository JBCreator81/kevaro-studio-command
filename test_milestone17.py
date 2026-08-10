from studio_command.decisions import (
    analyze_production_change_impact,
    apply_change_impact_to_runtime,
    build_governed_production_runtime_state,
    build_production_decision_history_entry,
    build_production_execution_authorization,
    build_studio_head_impact_brief,
    derive_production_workflow_state,
    record_studio_head_decision,
)
from studio_command.models import StudioHeadDecisionPackage


def make_package(
    *,
    recommendation="APPROVE",
    blockers=None,
):
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Milestone 17 execution authorization test.",
        qa_decision="PASS" if not blockers else "CONDITIONAL PASS",
        readiness_score=100 if not blockers else 80,
        clearance_status="CLEAR TO PROCEED" if not blockers else "CONDITIONAL",
        decision_items=[],
        material_blockers=blockers or [],
        conditions_for_approval=[],
        recommended_decision=recommendation,
        decision_options=[
            "APPROVE",
            "APPROVE WITH CONDITIONS",
            "REQUEST CHANGES",
            "REJECT",
        ],
        final_warning="none",
    )


def build_runtime(
    decision_value,
    *,
    conditions=None,
    package=None,
):
    decision = record_studio_head_decision(
        production_name="Luxury Wellness Campaign",
        decision=decision_value,
        conditions=conditions or [],
        decision_notes="Milestone 17 test decision.",
        decided_by="Studio Head",
        decision_package=package or make_package(),
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
            "Audience Research",
            "Campaign Strategy",
            "Hero Edit",
        ],
    )

    return runtime


requested_actions = [
    "Render final hero edit",
    "Prepare social cutdowns",
]


# APPROVE -> full execution authorization
approved_runtime = build_runtime("APPROVE")

approved_auth = build_production_execution_authorization(
    runtime_state=approved_runtime,
    requested_actions=requested_actions,
)

assert approved_auth.authorization_status == "AUTHORIZED"
assert approved_auth.execution_mode == "UNCONDITIONAL"
assert approved_auth.may_execute is True
assert approved_auth.authorized_actions == requested_actions
assert approved_auth.blocked_actions == []
assert approved_auth.active_conditions == []
assert approved_auth.human_authority_confirmed is True


# APPROVE WITH CONDITIONS -> authorization carries conditions forward
conditional_runtime = build_runtime(
    "APPROVE WITH CONDITIONS",
    conditions=[
        "Use only the cleared music track.",
        "Final copy must preserve approved wellness wording.",
    ],
    package=make_package(
        recommendation="APPROVE WITH CONDITIONS",
    ),
)

conditional_auth = build_production_execution_authorization(
    runtime_state=conditional_runtime,
    requested_actions=requested_actions,
)

assert conditional_auth.authorization_status == "AUTHORIZED_WITH_CONDITIONS"
assert conditional_auth.execution_mode == "CONDITIONAL"
assert conditional_auth.may_execute is True
assert len(conditional_auth.active_conditions) == 2
assert "Use only the cleared music track." in conditional_auth.active_conditions


# REQUEST CHANGES -> execution blocked
changes_runtime = build_runtime(
    "REQUEST CHANGES",
    package=make_package(
        recommendation="REQUEST CHANGES",
        blockers=["Creative revision required."],
    ),
)

changes_auth = build_production_execution_authorization(
    runtime_state=changes_runtime,
    requested_actions=requested_actions,
)

assert changes_auth.authorization_status == "BLOCKED"
assert changes_auth.execution_mode == "BLOCKED"
assert changes_auth.may_execute is False
assert changes_auth.authorized_actions == []
assert changes_auth.blocked_actions == requested_actions


# REJECT -> execution blocked
rejected_runtime = build_runtime(
    "REJECT",
    package=make_package(
        recommendation="REJECT",
        blockers=["Production path rejected."],
    ),
)

rejected_auth = build_production_execution_authorization(
    runtime_state=rejected_runtime,
    requested_actions=requested_actions,
)

assert rejected_auth.authorization_status == "BLOCKED"
assert rejected_auth.may_execute is False


# Approved production interrupted by high-impact change -> blocked
change_command = "Replace the approved lead talent."

impact = analyze_production_change_impact(
    runtime_state=approved_runtime,
    requested_change=change_command,
    affected_work=[
        "Hero Edit",
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
    schedule_impact="Affected talent work must reopen.",
    delivery_impact="Delivery may slip pending re-clearance and re-verification.",
)

brief = build_studio_head_impact_brief(
    runtime_state=approved_runtime,
    command=change_command,
    change_impact=impact,
    scope_confirmed=True,
    stale_decision_detected=False,
)

guarded_runtime = apply_change_impact_to_runtime(
    runtime_state=approved_runtime,
    change_impact=impact,
    impact_brief=brief,
)

guarded_auth = build_production_execution_authorization(
    runtime_state=guarded_runtime,
    requested_actions=requested_actions,
)

assert guarded_runtime.current_stage == "STUDIO_HEAD_IMPACT_REVIEW"
assert guarded_auth.authorization_status == "BLOCKED"
assert guarded_auth.may_execute is False
assert guarded_auth.authorized_actions == []
assert guarded_auth.blocked_actions == requested_actions
assert guarded_runtime.memory_snapshot.stale_artifacts == [
    "Hero Edit"
]


# Requested execution action list may not be empty
try:
    build_production_execution_authorization(
        runtime_state=approved_runtime,
        requested_actions=[],
    )
    raise AssertionError(
        "Empty requested execution actions should fail."
    )
except ValueError:
    pass


print("MILESTONE 17 APPROVED PRODUCTION EXECUTION VALIDATION: PASS")
