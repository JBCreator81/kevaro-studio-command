from studio_command.decisions import record_studio_head_decision
from studio_command.models import StudioHeadDecisionPackage


def make_package(blockers=None, recommendation="REQUEST CHANGES"):
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Test decision package.",
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


package_with_blocker = make_package(
    blockers=["Brand approval remains unresolved."]
)

package_clear = make_package(
    blockers=[],
    recommendation="APPROVE",
)


# 1. Valid human request-changes decision
record = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="REQUEST CHANGES",
    conditions=[],
    decision_notes="Resolve brand approval before proceeding.",
    decided_by="Studio Head",
    decision_package=package_with_blocker,
    unresolved_risks_acknowledged=[
        "Brand approval remains unresolved."
    ],
)

assert record.decision == "REQUEST CHANGES"
assert record.recommendation_followed is True
assert "corrective work" in record.next_action.lower()


# 2. Agent may never impersonate Studio Head
try:
    record_studio_head_decision(
        production_name="Luxury Wellness Campaign",
        decision="REQUEST CHANGES",
        conditions=[],
        decision_notes="",
        decided_by="Studio Head Agent",
        decision_package=package_with_blocker,
        unresolved_risks_acknowledged=[],
    )
    raise AssertionError("Agent impersonation should have failed.")
except ValueError:
    pass


# 3. Conditional approval must contain conditions
try:
    record_studio_head_decision(
        production_name="Luxury Wellness Campaign",
        decision="APPROVE WITH CONDITIONS",
        conditions=[],
        decision_notes="",
        decided_by="Studio Head",
        decision_package=package_clear,
        unresolved_risks_acknowledged=[],
    )
    raise AssertionError(
        "APPROVE WITH CONDITIONS without conditions should have failed."
    )
except ValueError:
    pass


# 4. Unconditional approval cannot bypass material blockers
try:
    record_studio_head_decision(
        production_name="Luxury Wellness Campaign",
        decision="APPROVE",
        conditions=[],
        decision_notes="",
        decided_by="Studio Head",
        decision_package=package_with_blocker,
        unresolved_risks_acknowledged=[],
    )
    raise AssertionError(
        "APPROVE with material blockers should have failed."
    )
except ValueError:
    pass


# 5. Clean package may be approved by the human
approved = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="APPROVE",
    conditions=[],
    decision_notes="Approved for production.",
    decided_by="Studio Head",
    decision_package=package_clear,
    unresolved_risks_acknowledged=[],
)

assert approved.decision == "APPROVE"
assert approved.recommendation_followed is True
assert "advance production" in approved.next_action.lower()


print("MILESTONE 10 HUMAN DECISION VALIDATION: PASS")
