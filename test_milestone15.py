from studio_command.decisions import (
    build_corrective_work_record,
    build_production_decision_history_entry,
    build_production_re_review_record,
    derive_production_workflow_state,
    record_studio_head_decision,
    record_studio_head_reapproval,
)
from studio_command.models import StudioHeadDecisionPackage


def make_package(
    *,
    blockers=None,
    recommendation="REQUEST CHANGES",
    readiness=75,
    clearance="CONDITIONAL",
):
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Milestone 15 reapproval test package.",
        qa_decision="PASS" if not blockers else "CONDITIONAL PASS",
        readiness_score=readiness,
        clearance_status=clearance,
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


# Original Studio Head decision: sequence 1
original_decision = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="REQUEST CHANGES",
    conditions=[],
    decision_notes="Resolve brand approval.",
    decided_by="Studio Head",
    decision_package=make_package(
        blockers=["Brand approval remains unresolved."]
    ),
    unresolved_risks_acknowledged=[
        "Brand approval remains unresolved."
    ],
)

original_state = derive_production_workflow_state(
    original_decision
)

original_history = build_production_decision_history_entry(
    sequence=1,
    decision_record=original_decision,
    workflow_state=original_state,
)

assert original_history.sequence == 1
assert original_history.decision == "REQUEST CHANGES"


# Corrective work
corrective_record = build_corrective_work_record(
    history_entry=original_history,
    issues_to_correct=[
        "Secure final brand approval."
    ],
    corrective_actions_completed=[
        "Final brand approval secured."
    ],
    submitted_by="Production Manager",
)

assert corrective_record.ready_for_re_review is True


# Re-verification passes
re_review_record = build_production_re_review_record(
    corrective_record=corrective_record,
    verification_completed=True,
    verification_passed=True,
)

assert re_review_record.next_stage == "STUDIO_HEAD_REAPPROVAL"
assert re_review_record.may_return_to_studio_head is True
assert re_review_record.may_advance_to_production is False


# Fresh Studio Head reapproval must create sequence 2
reapproval = record_studio_head_reapproval(
    re_review_record=re_review_record,
    prior_history_entry=original_history,
    decision="APPROVE",
    conditions=[],
    decision_notes="Corrective work verified. Production approved.",
    decided_by="Studio Head",
    decision_package=make_package(
        blockers=[],
        recommendation="APPROVE",
        readiness=100,
        clearance="CLEAR TO PROCEED",
    ),
    unresolved_risks_acknowledged=[],
)

assert reapproval.prior_decision_sequence == 1
assert reapproval.new_decision_sequence == 2
assert reapproval.history_entry.sequence == 2
assert reapproval.history_entry.decision == "APPROVE"
assert reapproval.decision_record.decided_by == "Studio Head"
assert reapproval.fresh_human_decision_required is True


# Original history remains unchanged
assert original_history.sequence == 1
assert original_history.decision == "REQUEST CHANGES"


# Cannot reapprove before successful re-verification
blocked_re_review = build_production_re_review_record(
    corrective_record=corrective_record,
    verification_completed=False,
    verification_passed=False,
)

try:
    record_studio_head_reapproval(
        re_review_record=blocked_re_review,
        prior_history_entry=original_history,
        decision="APPROVE",
        conditions=[],
        decision_notes="Invalid bypass attempt.",
        decided_by="Studio Head",
        decision_package=make_package(
            blockers=[],
            recommendation="APPROVE",
            readiness=100,
            clearance="CLEAR TO PROCEED",
        ),
        unresolved_risks_acknowledged=[],
    )
    raise AssertionError(
        "Reapproval before successful re-verification should fail."
    )
except ValueError:
    pass


# Prior sequence must match the re-review source
wrong_history = original_history.model_copy(
    update={"sequence": 2}
)

try:
    record_studio_head_reapproval(
        re_review_record=re_review_record,
        prior_history_entry=wrong_history,
        decision="APPROVE",
        conditions=[],
        decision_notes="Invalid sequence attempt.",
        decided_by="Studio Head",
        decision_package=make_package(
            blockers=[],
            recommendation="APPROVE",
            readiness=100,
            clearance="CLEAR TO PROCEED",
        ),
        unresolved_risks_acknowledged=[],
    )
    raise AssertionError(
        "Mismatched prior history sequence should fail."
    )
except ValueError:
    pass


print("MILESTONE 15 FRESH REAPPROVAL VALIDATION: PASS")
