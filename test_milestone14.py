from studio_command.decisions import (
    build_corrective_work_record,
    build_production_decision_history_entry,
    build_production_re_review_record,
    derive_production_workflow_state,
    record_studio_head_decision,
)
from studio_command.models import StudioHeadDecisionPackage


def make_package():
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Milestone 14 re-review test package.",
        qa_decision="CONDITIONAL PASS",
        readiness_score=75,
        clearance_status="CONDITIONAL",
        decision_items=[],
        material_blockers=[
            "Brand approval remains unresolved."
        ],
        conditions_for_approval=[],
        recommended_decision="REQUEST CHANGES",
        decision_options=[
            "APPROVE",
            "APPROVE WITH CONDITIONS",
            "REQUEST CHANGES",
            "REJECT",
        ],
        final_warning="Test warning.",
    )


decision_record = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="REQUEST CHANGES",
    conditions=[],
    decision_notes="Resolve outstanding approval.",
    decided_by="Studio Head",
    decision_package=make_package(),
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

corrective_record = build_corrective_work_record(
    history_entry=history_entry,
    issues_to_correct=[
        "Secure final brand approval."
    ],
    corrective_actions_completed=[
        "Final brand approval secured."
    ],
    submitted_by="Production Manager",
)

assert corrective_record.ready_for_re_review is True


awaiting_verification = build_production_re_review_record(
    corrective_record=corrective_record,
    verification_completed=False,
    verification_passed=False,
)

assert awaiting_verification.next_stage == "INDEPENDENT_RE_VERIFICATION"
assert awaiting_verification.may_return_to_studio_head is False
assert awaiting_verification.may_advance_to_production is False


failed_verification = build_production_re_review_record(
    corrective_record=corrective_record,
    verification_completed=True,
    verification_passed=False,
)

assert failed_verification.next_stage == "CORRECTIVE_WORK"
assert failed_verification.may_return_to_studio_head is False
assert failed_verification.may_advance_to_production is False


passed_verification = build_production_re_review_record(
    corrective_record=corrective_record,
    verification_completed=True,
    verification_passed=True,
)

assert passed_verification.next_stage == "STUDIO_HEAD_REAPPROVAL"
assert passed_verification.may_return_to_studio_head is True
assert passed_verification.may_advance_to_production is False
assert passed_verification.verification_passed is True


try:
    build_production_re_review_record(
        corrective_record=corrective_record,
        verification_completed=False,
        verification_passed=True,
    )
    raise AssertionError(
        "Verification pass without completion should fail."
    )
except ValueError:
    pass


incomplete_corrective = corrective_record.model_copy(
    update={"ready_for_re_review": False}
)

try:
    build_production_re_review_record(
        corrective_record=incomplete_corrective,
        verification_completed=False,
        verification_passed=False,
    )
    raise AssertionError(
        "Incomplete corrective work should not enter re-review."
    )
except ValueError:
    pass


print("MILESTONE 14 RE-REVIEW GATE VALIDATION: PASS")
