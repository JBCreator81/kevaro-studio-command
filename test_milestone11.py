from studio_command.decisions import (
    derive_production_workflow_state,
    record_studio_head_decision,
)
from studio_command.models import StudioHeadDecisionPackage


def make_package(blockers=None, recommendation="REQUEST CHANGES"):
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Milestone 11 routing test package.",
        qa_decision="PASS" if not blockers else "CONDITIONAL PASS",
        readiness_score=100 if not blockers else 75,
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
        final_warning="Test warning.",
    )


clear_package = make_package(blockers=[], recommendation="APPROVE")
blocked_package = make_package(
    blockers=["Brand approval remains unresolved."],
    recommendation="REQUEST CHANGES",
)


# 1. APPROVE -> downstream production
approved_record = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="APPROVE",
    conditions=[],
    decision_notes="Proceed.",
    decided_by="Studio Head",
    decision_package=clear_package,
    unresolved_risks_acknowledged=[],
)

approved_state = derive_production_workflow_state(approved_record)

assert approved_state.status == "APPROVED"
assert approved_state.production_may_advance is True
assert approved_state.corrective_action_required is False
assert approved_state.production_stopped is False
assert approved_state.next_stage == "DOWNSTREAM_PRODUCTION"


# 2. APPROVE WITH CONDITIONS -> conditional downstream production
conditional_record = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="APPROVE WITH CONDITIONS",
    conditions=["Final brand approval required before public release."],
    decision_notes="Proceed under stated condition.",
    decided_by="Studio Head",
    decision_package=clear_package,
    unresolved_risks_acknowledged=[],
)

conditional_state = derive_production_workflow_state(conditional_record)

assert conditional_state.status == "APPROVED_WITH_CONDITIONS"
assert conditional_state.production_may_advance is True
assert conditional_state.corrective_action_required is False
assert conditional_state.production_stopped is False
assert conditional_state.active_conditions == [
    "Final brand approval required before public release."
]
assert conditional_state.next_stage == "CONDITIONAL_DOWNSTREAM_PRODUCTION"


# 3. REQUEST CHANGES -> corrective work
changes_record = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="REQUEST CHANGES",
    conditions=[],
    decision_notes="Resolve the blocker.",
    decided_by="Studio Head",
    decision_package=blocked_package,
    unresolved_risks_acknowledged=[
        "Brand approval remains unresolved."
    ],
)

changes_state = derive_production_workflow_state(changes_record)

assert changes_state.status == "CHANGES_REQUESTED"
assert changes_state.production_may_advance is False
assert changes_state.corrective_action_required is True
assert changes_state.production_stopped is False
assert changes_state.next_stage == "CORRECTIVE_WORK"


# 4. REJECT -> stop production path
reject_record = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="REJECT",
    conditions=[],
    decision_notes="Do not proceed.",
    decided_by="Studio Head",
    decision_package=blocked_package,
    unresolved_risks_acknowledged=[
        "Brand approval remains unresolved."
    ],
)

reject_state = derive_production_workflow_state(reject_record)

assert reject_state.status == "REJECTED"
assert reject_state.production_may_advance is False
assert reject_state.corrective_action_required is False
assert reject_state.production_stopped is True
assert reject_state.next_stage == "STOPPED"


print("MILESTONE 11 PRODUCTION ROUTING VALIDATION: PASS")
