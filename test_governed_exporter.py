from studio_command.exporter import (
    build_governed_export_manifest,
    canonical_manifest_bytes,
    governed_export,
)
from studio_command.models import (
    FinalProductionPackage,
    ProductionDecisionHistoryEntry,
)


class FakePersistence:
    def __init__(self):
        self.calls = []

    def upload_artifact_bytes(
        self,
        *,
        production_name,
        artifact_name,
        data,
        content_type,
    ):
        self.calls.append(
            {
                "production_name": production_name,
                "artifact_name": artifact_name,
                "data": data,
                "content_type": content_type,
            }
        )
        return f"gs://test-bucket/productions/{production_name}/{artifact_name}"


def make_package():
    history = ProductionDecisionHistoryEntry.model_construct(
        sequence=1,
        production_name="Luxury Wellness Campaign",
        decision="APPROVE",
        decided_by="Studio Head",
        source_recommendation="APPROVE",
        recommendation_followed=True,
        resulting_status="APPROVED",
        next_stage="DOWNSTREAM_PRODUCTION",
        production_may_advance=True,
        corrective_action_required=False,
        production_stopped=False,
        active_conditions=[],
        unresolved_risks_acknowledged=[],
        decision_notes="Approved for final delivery.",
    )

    return FinalProductionPackage.model_construct(
        production_name="Luxury Wellness Campaign",
        decision_sequence=1,
        approval_status="APPROVED",
        active_conditions=[],
        production_brief={},
        research_packet={},
        creative_treatment={},
        production_plan={},
        production_schedule={},
        asset_media_plan={},
        clearance_report={},
        verification_report={},
        decision_history=[history],
        authorized_actions=["DELIVER"],
        delivery_artifacts=[
            "gs://test-bucket/final/hero-video.mp4",
        ],
        delivery_status="READY_FOR_DELIVERY",
        readiness_score=100,
        final_notes=["Final governed package ready for delivery."],
    )


package = make_package()

manifest = build_governed_export_manifest(package)

assert manifest["production_name"] == "Luxury Wellness Campaign"
assert manifest["governance"]["decision_sequence"] == 1
assert manifest["governance"]["approval_status"] == "APPROVED"
assert manifest["delivery"]["status"] == "READY_FOR_DELIVERY"
assert manifest["delivery"]["artifacts"] == [
    "gs://test-bucket/final/hero-video.mp4"
]

first = canonical_manifest_bytes(package)
second = canonical_manifest_bytes(package)

assert first == second

persistence = FakePersistence()

receipt = governed_export(
    final_package=package,
    persistence=persistence,
)

assert receipt.production_name == package.production_name
assert receipt.decision_sequence == 1
assert receipt.delivery_status == "READY_FOR_DELIVERY"
assert receipt.readiness_score == 100
assert len(receipt.manifest_sha256) == 64
assert receipt.manifest_uri.startswith("gs://test-bucket/productions/")

assert len(persistence.calls) == 1
assert persistence.calls[0]["content_type"] == "application/json"
assert persistence.calls[0]["data"] == first
assert receipt.manifest_sha256 in persistence.calls[0]["artifact_name"]


blocked = package.model_copy(
    update={"delivery_status": "BLOCKED"}
)

try:
    build_governed_export_manifest(blocked)
    raise AssertionError("BLOCKED package must not export.")
except ValueError:
    pass


unapproved = package.model_copy(
    update={"approval_status": "CONDITIONAL"}
)

try:
    build_governed_export_manifest(unapproved)
    raise AssertionError("Unapproved package must not export.")
except ValueError:
    pass


missing_artifacts = package.model_copy(
    update={"delivery_artifacts": []}
)

try:
    build_governed_export_manifest(missing_artifacts)
    raise AssertionError("Package without delivery artifacts must not export.")
except ValueError:
    pass


print("GOVERNED EXPORTER CONTRACT: PASS")

from studio_command.exporter import complete_governed_delivery
from studio_command.models import (
    GovernedProductionRuntimeState,
    ProductionMemorySnapshot,
    ProductionWorkflowState,
)


class FakeDeliveryPersistence(FakePersistence):
    def __init__(self, fail_upload=False):
        super().__init__()
        self.fail_upload = fail_upload
        self.saved_runtime = None

    def upload_artifact_bytes(
        self,
        *,
        production_name,
        artifact_name,
        data,
        content_type,
    ):
        if self.fail_upload:
            raise RuntimeError("simulated storage failure")
        return super().upload_artifact_bytes(
            production_name=production_name,
            artifact_name=artifact_name,
            data=data,
            content_type=content_type,
        )

    def save_runtime_state(self, runtime_state):
        self.saved_runtime = runtime_state


workflow_state = ProductionWorkflowState.model_construct(
    production_name=package.production_name,
    status="APPROVED",
    active_conditions=[],
    corrective_action_required=False,
    production_may_advance=True,
    production_stopped=False,
    next_stage="DOWNSTREAM_PRODUCTION",
)

memory_snapshot = ProductionMemorySnapshot.model_construct(
    production_name=package.production_name,
)

runtime_state = GovernedProductionRuntimeState.model_construct(
    production_name=package.production_name,
    workflow_state=workflow_state,
    decision_history=package.decision_history,
    memory_snapshot=memory_snapshot,
    change_impact=None,
    impact_brief=None,
    execution_authorized=True,
    corrective_cycle_active=False,
    current_stage="DOWNSTREAM_PRODUCTION",
)

delivery_persistence = FakeDeliveryPersistence()

delivery_result = complete_governed_delivery(
    final_package=package,
    runtime_state=runtime_state,
    persistence=delivery_persistence,
)

assert delivery_result.receipt.delivery_status == "READY_FOR_DELIVERY"
assert delivery_result.runtime_state.current_stage == "DELIVERED"
assert delivery_result.runtime_state.execution_authorized is False
assert delivery_result.runtime_state.workflow_state.next_stage == "DELIVERED"
assert delivery_result.runtime_state.workflow_state.production_may_advance is False

assert delivery_persistence.saved_runtime is not None
assert delivery_persistence.saved_runtime.current_stage == "DELIVERED"

# Original runtime must remain unchanged.
assert runtime_state.current_stage == "DOWNSTREAM_PRODUCTION"
assert runtime_state.execution_authorized is True

# Storage failure must not persist a delivered runtime.
failed_persistence = FakeDeliveryPersistence(fail_upload=True)

try:
    complete_governed_delivery(
        final_package=package,
        runtime_state=runtime_state,
        persistence=failed_persistence,
    )
    raise AssertionError("Storage failure must block delivery completion.")
except RuntimeError:
    pass

assert failed_persistence.saved_runtime is None
assert runtime_state.current_stage == "DOWNSTREAM_PRODUCTION"

# Cross-production runtime/package mixing must be blocked.
wrong_runtime = runtime_state.model_copy(
    update={"production_name": "Different Production"}
)

try:
    complete_governed_delivery(
        final_package=package,
        runtime_state=wrong_runtime,
        persistence=FakeDeliveryPersistence(),
    )
    raise AssertionError("Cross-production delivery must be rejected.")
except ValueError:
    pass

print("GOVERNED DELIVERY TRANSITION: PASS")
