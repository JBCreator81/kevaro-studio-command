from studio_command.decisions import approve_governed_production
from studio_command.models import StudioHeadDecisionPackage


class FakePersistence:
    def __init__(self):
        self.runtime = None
        self.artifacts = None

    def save_runtime_state(self, runtime_state):
        self.runtime = runtime_state

    def save_approved_artifacts(self, *, production_name, approved_artifacts):
        self.artifacts = {
            "production_name": production_name,
            "approved_artifacts": approved_artifacts,
        }


def package():
    return StudioHeadDecisionPackage(
        production_name="Bridge Test",
        executive_summary="Governed approval bridge validation package.",
        qa_decision="PASS",
        readiness_score=100,
        clearance_status="CLEARED",
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


approved_artifacts = {
    "production_brief": {"status": "approved"},
    "research_packet": {"status": "approved"},
    "creative_treatment": {"status": "approved"},
    "production_plan": {"status": "approved"},
    "production_schedule": {"status": "approved"},
    "asset_media_plan": {"status": "approved"},
    "clearance_report": {"status": "approved"},
    "verification_report": {"status": "approved"},
}


# APPROVE
p = FakePersistence()

runtime = approve_governed_production(
    production_name="Bridge Test",
    decision="APPROVE",
    conditions=[],
    decision_notes="Approved for downstream production.",
    decided_by="Studio Head",
    decision_package=package(),
    unresolved_risks_acknowledged=[],
    approved_artifacts=approved_artifacts,
    preserved_artifacts=list(approved_artifacts.keys()),
    persistence=p,
)

assert runtime.workflow_state.status == "APPROVED"
assert runtime.execution_authorized is True
assert p.runtime is runtime
assert p.artifacts is not None

print("APPROVE: PASS")


# APPROVE WITH CONDITIONS
p = FakePersistence()

runtime = approve_governed_production(
    production_name="Bridge Test",
    decision="APPROVE WITH CONDITIONS",
    conditions=["Final legal copy review required."],
    decision_notes="Proceed subject to the stated condition.",
    decided_by="Studio Head",
    decision_package=package(),
    unresolved_risks_acknowledged=[],
    approved_artifacts=approved_artifacts,
    preserved_artifacts=list(approved_artifacts.keys()),
    persistence=p,
)

assert runtime.workflow_state.status == "APPROVED_WITH_CONDITIONS"
assert "Final legal copy review required." in runtime.workflow_state.active_conditions
assert p.runtime is runtime
assert p.artifacts is not None

print("APPROVE WITH CONDITIONS: PASS")


# REQUEST CHANGES
p = FakePersistence()

runtime = approve_governed_production(
    production_name="Bridge Test",
    decision="REQUEST CHANGES",
    conditions=[],
    decision_notes="Production package requires corrective work.",
    decided_by="Studio Head",
    decision_package=package(),
    unresolved_risks_acknowledged=[],
    approved_artifacts=approved_artifacts,
    preserved_artifacts=list(approved_artifacts.keys()),
    persistence=p,
)

assert runtime.workflow_state.status == "CHANGES_REQUESTED"
assert runtime.execution_authorized is False
assert p.runtime is runtime
assert p.artifacts is None

print("REQUEST CHANGES: PASS")


# REJECT
p = FakePersistence()

runtime = approve_governed_production(
    production_name="Bridge Test",
    decision="REJECT",
    conditions=[],
    decision_notes="Production path rejected.",
    decided_by="Studio Head",
    decision_package=package(),
    unresolved_risks_acknowledged=[],
    approved_artifacts=approved_artifacts,
    preserved_artifacts=list(approved_artifacts.keys()),
    persistence=p,
)

assert runtime.workflow_state.status == "REJECTED"
assert runtime.execution_authorized is False
assert p.runtime is runtime
assert p.artifacts is None

print("REJECT: PASS")

print("GOVERNED APPROVAL BRIDGE: PASS")
