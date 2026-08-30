import pytest
from fastapi.testclient import TestClient

from studio_command.access import AuthorizationDenied
from studio_command.accountability import human_actor
from studio_command.assets import (
    approved_asset_references,
    asset_snapshot,
    create_asset_version,
    handoff_asset,
    reconcile_external_return,
    register_asset,
    review_asset,
    submit_asset_for_review,
)
from studio_command.exporter import build_governed_export_manifest
from studio_command.graph import build_production_graph
from studio_command.models import (
    AccountabilityMetadata,
    AssetStorageReference,
)
from studio_command.persistence import ProductionPersistence, ProductionPersistenceConfig
from studio_command.ui_snapshot import (
    build_pending_studio_command_snapshot,
    build_studio_command_snapshot,
)
from test_governed_exporter import make_package
from test_milestone1_identity import Firestore, Storage, review_bundle
from test_milestone19 import production_plan, production_schedule
from test_milestone22 import runtime


PRODUCTION = "Luxury Wellness Campaign"
OWNER = human_actor("Avery", "Editor")
REVIEWER = human_actor("Riley", "Reviewer")
HEAD = human_actor("Morgan Lee", "Studio Head")
OUTSIDER = human_actor("Taylor", "Crew")


class MemoryAssets:
    def __init__(self):
        self.registry = None

    def load_asset_registry(self, production_name):
        return self.registry.model_copy(deep=True) if self.registry else None

    def save_asset_registry(self, registry):
        self.registry = registry.model_copy(deep=True)


def metadata():
    return AccountabilityMetadata(
        human_owner=OWNER, reviewer_verifier=REVIEWER,
        current_status="IN_PROGRESS",
    )


def location(name="v1.mov"):
    return AssetStorageReference(
        location_type="GCS_URI",
        reference=f"gs://test-bucket/production-assets/{name}",
        content_type="video/quicktime",
    )


def registered(store=None, category="VIDEO", display_name="Hero Cut"):
    store = store or MemoryAssets()
    asset = register_asset(
        persistence=store, production_name=PRODUCTION,
        node_id=production_plan.tasks[0].task_name,
        actor=OWNER, node_accountability=metadata(),
        asset_category=category, filename="hero-v1.mov",
        display_name=display_name, media_document_type="video/quicktime",
        storage=location(), provenance={"source": "editor upload"},
        expected_deliverable="Approved hero cut",
        acceptance_criteria=["Matches approved treatment"],
        preview_metadata={"duration_seconds": 30, "poster_frame": "00:00:03"},
    )
    return store, asset


@pytest.mark.parametrize("category", [
    "VIDEO", "AUDIO", "IMAGE", "SCRIPT_DOCUMENT", "STORYBOARD",
    "GRAPHIC", "OTHER_PRODUCTION_FILE",
])
def test_registration_supports_required_asset_categories(category):
    store, asset = registered(category=category)
    assert asset.production_identity == PRODUCTION
    assert asset.accountability.last_changed_by == OWNER
    assert asset.version_number == 1
    assert store.registry.assets[0].asset_category == category


def test_version_two_preserves_version_one_and_lineage():
    store, first = registered()
    second = create_asset_version(
        persistence=store, production_name=PRODUCTION,
        asset_id=first.asset_id, actor=OWNER, storage=location("v2.mov"),
        filename="hero-v2.mov", provenance={"change": "notes addressed"},
    )
    assert len(store.registry.assets) == 2
    assert store.registry.assets[0].storage.reference.endswith("v1.mov")
    assert second.version_number == 2
    assert second.parent_version_id == first.version_id
    assert second.accountability.last_changed_by == OWNER


def test_owner_access_reviewer_separation_and_studio_head_authority():
    store, asset = registered()
    with pytest.raises(AuthorizationDenied):
        create_asset_version(
            persistence=store, production_name=PRODUCTION,
            asset_id=asset.asset_id, actor=OUTSIDER,
            storage=location("bad.mov"), filename="bad.mov",
        )
    submitted = submit_asset_for_review(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, version_id=asset.version_id, actor=OWNER,
    )
    changed = review_asset(
        persistence=store, production_name=PRODUCTION, asset_id=asset.asset_id,
        version_id=submitted.version_id, actor=REVIEWER,
        decision="REQUEST_CHANGES", notes="Trim at 00:00:12.",
        annotations=[{"timecode": "00:00:12", "type": "trim"}],
    )
    assert changed.review_state == "CHANGES_REQUESTED"
    with pytest.raises(AuthorizationDenied, match="outside"):
        create_asset_version(
            persistence=store, production_name=PRODUCTION,
            asset_id=asset.asset_id, actor=REVIEWER,
            storage=location("reviewer.mov"), filename="reviewer.mov",
        )
    revised = create_asset_version(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, actor=OWNER,
        storage=location("v2.mov"), filename="hero-v2.mov",
    )
    submit_asset_for_review(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, version_id=revised.version_id, actor=OWNER,
    )
    approved = review_asset(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, version_id=revised.version_id,
        actor=HEAD, decision="APPROVE",
        comparison_version_id=asset.version_id,
    )
    assert approved.review_state == "APPROVED"
    assert approved.accountability.approved_by == HEAD


def test_external_handoff_preserves_context_and_return_reconciles():
    store, asset = registered()
    handoff = handoff_asset(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, actor=OWNER, target_tool="Adobe Premiere Pro",
        brief="Conform the approved hero edit.",
        requirements=["4K ProRes", "30 seconds"],
        evidence_context=["research:citation-7"], due_date="2026-09-02",
        approval_context="Treatment approved; final asset pending review.",
        expected_deliverable="4K hero master",
    )
    assert handoff.owner == OWNER
    assert handoff.base_version_id == asset.version_id
    assert handoff.requirements == ["4K ProRes", "30 seconds"]
    returned = reconcile_external_return(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, handoff_id=handoff.handoff_id,
        base_version_id=asset.version_id, node_id=asset.node_id,
        actor=OWNER, storage=location("returned.mov"), filename="returned.mov",
        return_metadata={"external_job_id": "premiere-job-42"},
    )
    assert returned.version_number == 2
    assert returned.parent_version_id == asset.version_id
    assert returned.review_state == "PENDING_REVIEW"
    persisted_handoff = store.registry.assets[0].handoffs[0]
    assert persisted_handoff.status == "RETURNED"
    assert persisted_handoff.returned_version_id == returned.version_id


def test_mismatched_external_return_fails_closed_without_new_version():
    store, asset = registered()
    handoff = handoff_asset(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, actor=OWNER, target_tool="Frame.io",
        brief="Review export", requirements=[], evidence_context=[], due_date=None,
        approval_context=None, expected_deliverable="Review export",
    )
    with pytest.raises(ValueError, match="production and node"):
        reconcile_external_return(
            persistence=store, production_name=PRODUCTION,
            asset_id=asset.asset_id, handoff_id=handoff.handoff_id,
            base_version_id=asset.version_id, node_id="Wrong Node", actor=OWNER,
            storage=location("wrong.mov"), filename="wrong.mov",
        )
    assert len(store.registry.assets) == 1


def test_node_intelligence_and_guidance_expose_asset_state():
    store, asset = registered(display_name="Hero Cut")
    submit_asset_for_review(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, version_id=asset.version_id, actor=OWNER,
    )
    graph = build_production_graph(
        production_plan=production_plan, production_schedule=production_schedule,
    )
    bundle = review_bundle()
    bundle["asset_media_plan"] = {
        "asset_requirements": [
            {"asset_name": "Hero Cut"}, {"asset_name": "Audio Master"}
        ]
    }
    snapshot = build_pending_studio_command_snapshot(
        production_name=PRODUCTION, graph_state=graph,
        review_bundle=bundle, asset_registry=store.registry,
    )
    workflow = snapshot["production_assets"]
    assert workflow["assets"][0]["latest_version"]["version_id"] == asset.version_id
    assert workflow["assets"][0]["review_state"] == "PENDING_REVIEW"
    assert workflow["missing_deliverables"] == ["Audio Master"]
    assert snapshot["asset_guidance"]["next_best_action"]["action_type"] == (
        "REGISTER_MISSING_ASSET"
    )
    node = next(item for item in snapshot["graph"]["nodes"]
                if item["node_id"] == asset.node_id)
    assert node["production_assets"][0]["asset_id"] == asset.asset_id


def test_approved_runtime_asset_reference_flows_to_export():
    store, asset = registered()
    submit_asset_for_review(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, version_id=asset.version_id, actor=OWNER,
    )
    review_asset(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, version_id=asset.version_id,
        actor=HEAD, decision="APPROVE",
    )
    references = approved_asset_references(store.registry)
    package = make_package().model_copy(update={"production_assets": references})
    manifest = build_governed_export_manifest(package)
    assert manifest["delivery"]["production_assets"] == references


def test_approved_runtime_snapshot_exposes_asset_workflow():
    store, asset = registered()
    submit_asset_for_review(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, version_id=asset.version_id, actor=OWNER,
    )
    approved = review_asset(
        persistence=store, production_name=PRODUCTION,
        asset_id=asset.asset_id, version_id=asset.version_id,
        actor=HEAD, decision="APPROVE",
    )
    graph = build_production_graph(
        production_plan=production_plan, production_schedule=production_schedule,
    )
    bundle = review_bundle()
    bundle["clearance_report"] = bundle.pop("clearance_compliance_report")
    bundle["verification_report"] = bundle.pop("verification_qa_report")
    bundle["decision_package"] = bundle.pop("studio_head_decision_package")
    snapshot = build_studio_command_snapshot(
        runtime_state=runtime, graph_state=graph,
        approved_artifacts=bundle, asset_registry=store.registry,
    )
    assert snapshot["approval_status"] == "APPROVED"
    assert snapshot["production_assets"]["approved_asset_count"] == 1
    assert snapshot["production_assets"]["assets"][0]["latest_version"][
        "version_id"
    ] == approved.version_id


def test_legacy_production_without_assets_loads_without_fake_history():
    persistence = ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test"),
        firestore_client=Firestore(), storage_client=Storage(),
    )
    bundle = review_bundle()
    persistence.save_pending_review_bundle(
        production_name=PRODUCTION, review_bundle=bundle,
    )
    assert persistence.load_asset_registry(PRODUCTION) is None
    assert asset_snapshot(None) == {
        "assets": [], "asset_count": 0, "approved_asset_count": 0,
        "missing_deliverables": [], "next_required_asset_action": None,
        "asset_actions": [],
    }


class Blob:
    def __init__(self, name):
        self.name = name
        self.data = None

    def upload_from_string(self, data, content_type):
        self.data = data


class Bucket:
    def __init__(self):
        self.last_blob = None

    def blob(self, name):
        self.last_blob = Blob(name)
        return self.last_blob


class GCS:
    def __init__(self):
        self.value = Bucket()

    def bucket(self, name):
        return self.value


def test_binary_ingress_uses_server_derived_safe_object_key():
    gcs = GCS()
    persistence = ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test", bucket_name="safe"),
        firestore_client=Firestore(), storage_client=gcs,
    )
    uri = persistence.upload_production_asset_bytes(
        production_name=PRODUCTION, asset_id="asset-abc123", version_number=2,
        filename="../../unsafe hero.mov", data=b"content", content_type="video/quicktime",
    )
    assert uri.startswith("gs://safe/productions/")
    assert "Luxury Wellness Campaign" not in uri
    assert ".." not in uri
    assert uri.endswith("/asset-abc123/v2/unsafe-hero.mov")


def test_public_asset_mutation_requires_trusted_context(monkeypatch):
    monkeypatch.delenv("KEVARO_INTERNAL_AUTH_TOKEN", raising=False)
    from studio_command.service import app
    response = TestClient(app).post(
        f"/api/productions/{PRODUCTION}/assets/register",
        json={},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["reason_code"] == (
        "TRUSTED_ACTOR_CONTEXT_UNAVAILABLE"
    )
