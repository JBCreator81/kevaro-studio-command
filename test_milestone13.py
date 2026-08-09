from studio_command.decisions import (
    build_corrective_work_record,
    build_production_decision_history_entry,
    derive_production_workflow_state,
    record_studio_head_decision,
)
from studio_command.models import StudioHeadDecisionPackage


def make_package(blockers=None, recommendation="REQUEST CHANGES"):
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Milestone 13 corrective-cycle test package.",
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
    decision_notes="Resolve brand approval.",
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


incomplete = build_corrective_work_record(
    history_entry=history_entry,
    issues_to_correct=[
        "Secure final brand approval.",
        "Confirm final distribution requirements.",
    ],
    corrective_actions_completed=[
        "Final brand approval secured."
    ],
    submitted_by="Production Manager",
)

assert incomplete.ready_for_re_review is False
assert incomplete.re_review_required is True
assert incomplete.studio_head_reapproval_required is True


complete = build_corrective_work_record(
    history_entry=history_entry,
    issues_to_correct=[
        "Secure final brand approval.",
        "Confirm final distribution requirements.",
    ],
    corrective_actions_completed=[
        "Final brand approval secured.",
        "Final distribution requirements confirmed.",
    ],
    submitted_by="Production Manager",
)

assert complete.ready_for_re_review is True
assert complete.re_review_required is True
assert complete.studio_head_reapproval_required is True


clear_package = make_package(
    blockers=[],
    recommendation="APPROVE",
)

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

approved_history = build_production_decision_history_entry(
    sequence=2,
    decision_record=approved_record,
    workflow_state=approved_state,
)

try:
    build_corrective_work_record(
        history_entry=approved_history,
        issues_to_correct=["Invented issue."],
        corrective_actions_completed=["Invented correction."],
        submitted_by="Production Manager",
    )
    raise AssertionError(
        "Approved production should not originate corrective work."
    )
except ValueError:
    pass


try:
    build_corrective_work_record(
        history_entry=history_entry,
        issues_to_correct=[],
        corrective_actions_completed=[],
        submitted_by="Production Manager",
    )
    raise AssertionError(
        "Corrective work without an issue should have failed."
    )
except ValueError:
    pass


print("MILESTONE 13 CORRECTIVE CYCLE VALIDATION: PASS")
