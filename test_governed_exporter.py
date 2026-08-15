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
