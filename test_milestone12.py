from studio_command.decisions import (
    build_production_decision_history_entry,
    derive_production_workflow_state,
    record_studio_head_decision,
)
from studio_command.models import StudioHeadDecisionPackage


def make_package(blockers=None, recommendation="REQUEST CHANGES"):
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Milestone 12 history test package.",
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


blocked_package = make_package(
    blockers=["Brand approval remains unresolved."],
    recommendation="REQUEST CHANGES",
)

decision_record = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="REQUEST CHANGES",
    conditions=[],
    decision_notes="Resolve brand approval before proceeding.",
    decided_by="Studio Head",
    decision_package=blocked_package,
    unresolved_risks_acknowledged=[
        "Brand approval remains unresolved."
    ],
)

workflow_state = derive_production_workflow_state(decision_record)

history_entry = build_production_decision_history_entry(
    sequence=1,
    decision_record=decision_record,
    workflow_state=workflow_state,
)

assert history_entry.sequence == 1
assert history_entry.production_name == "Luxury Wellness Campaign"
assert history_entry.decision == "REQUEST CHANGES"
assert history_entry.decided_by == "Studio Head"
assert history_entry.source_recommendation == "REQUEST CHANGES"
assert history_entry.recommendation_followed is True
assert history_entry.resulting_status == "CHANGES_REQUESTED"
assert history_entry.next_stage == "CORRECTIVE_WORK"
assert history_entry.production_may_advance is False
assert history_entry.corrective_action_required is True
assert history_entry.production_stopped is False
assert history_entry.active_conditions == []
assert history_entry.unresolved_risks_acknowledged == [
    "Brand approval remains unresolved."
]
assert history_entry.decision_notes == (
    "Resolve brand approval before proceeding."
)


# sequence must be valid
try:
    build_production_decision_history_entry(
        sequence=0,
        decision_record=decision_record,
        workflow_state=workflow_state,
    )
    raise AssertionError("Sequence validation should have failed.")
except ValueError:
    pass


# decision and workflow state must refer to the same production
mismatched_state = workflow_state.model_copy(
    update={"production_name": "Different Production"}
)

try:
    build_production_decision_history_entry(
        sequence=2,
        decision_record=decision_record,
        workflow_state=mismatched_state,
    )
    raise AssertionError("Production mismatch should have failed.")
except ValueError:
    pass


print("MILESTONE 12 DECISION HISTORY VALIDATION: PASS")
