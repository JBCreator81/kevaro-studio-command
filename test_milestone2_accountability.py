from studio_command.accountability import (
    add_human_approval,
    add_pending_accountability,
)
from studio_command.decisions import approve_governed_production
from studio_command.models import ProductionPlan
from studio_command.persistence import (
    ProductionPersistence,
    ProductionPersistenceConfig,
)
from studio_command.service import live_studio_snapshot
from test_governed_approval_bridge import FakePersistence, package
from test_milestone1_identity import Firestore, Storage, review_bundle
from test_milestone19 import production_plan
from test_milestone22 import runtime


PRODUCTION = "Luxury Wellness Campaign"


def persistence():
    return ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test"),
        firestore_client=Firestore(),
        storage_client=Storage(),
    )


def test_accountability_serializes_and_persists():
    store = persistence()
    bundle = add_pending_accountability(review_bundle())

    store.save_pending_review_bundle(
        production_name=PRODUCTION,
        review_bundle=bundle,
    )

    loaded = store.load_pending_review_bundle(PRODUCTION)
    accountability = loaded["research_packet"]["accountability"]
    assert accountability["ai_agent_responsible"]["name"] == "research_agent"
    assert accountability["created_at"].endswith("Z")
    assert accountability["action_history"][0]["action"] == "CREATED_FOR_REVIEW"


def test_legacy_artifact_without_accountability_remains_valid():
    legacy = production_plan.model_dump(mode="json", exclude={"accountability"})
    restored = ProductionPlan.model_validate(legacy)
    assert restored.accountability is None


def test_pending_review_node_intelligence_exposes_accountability(monkeypatch):
    bundle = add_pending_accountability(review_bundle())

    class PendingPersistence:
        def load_runtime_state(self, production_name):
            return None

        def load_pending_review_bundle(self, production_name):
            return bundle

    import studio_command.service as service
    monkeypatch.setattr(service, "production_persistence", PendingPersistence())

    snapshot = live_studio_snapshot(PRODUCTION)
    research = snapshot["accountability"]["Research"]
    assert research["human_owner"]["role"] == "Studio Head"
    assert research["ai_agent_responsible"]["name"] == "research_agent"
    assert research["approved_by"] is None
    assert research["human_final_authority"] is True


def test_approved_runtime_node_intelligence_exposes_human_approval(monkeypatch):
    bundle = review_bundle()
    bundle["clearance_report"] = bundle.pop("clearance_compliance_report")
    bundle["verification_report"] = bundle.pop("verification_qa_report")
    bundle["decision_package"] = bundle.pop("studio_head_decision_package")
    artifacts = add_human_approval(
        add_pending_accountability(bundle),
        decided_by="Morgan Lee",
        status="APPROVED",
    )

    class ApprovedPersistence:
        def load_runtime_state(self, production_name):
            return runtime

        def load_approved_artifacts(self, production_name):
            return artifacts

        def load_final_package(self, production_name):
            return None

    import studio_command.service as service
    monkeypatch.setattr(service, "production_persistence", ApprovedPersistence())

    snapshot = live_studio_snapshot(PRODUCTION)
    qa = snapshot["accountability"]["Verification QA"]
    assert qa["reviewer_verifier"]["name"] == "verification_qa_agent"
    assert qa["approved_by"] == {
        "name": "Morgan Lee", "actor_type": "HUMAN", "role": "Studio Head"
    }
    assert qa["last_changed_by"]["name"] == "Morgan Lee"
    assert qa["action_history"][-1]["action"] == "STUDIO_HEAD_DECISION"


def test_human_approval_authority_remains_explicit():
    store = FakePersistence()
    governed = approve_governed_production(
        production_name="Bridge Test",
        decision="APPROVE",
        conditions=[],
        decision_notes="Human approval.",
        decided_by="Morgan Lee",
        decision_package=package(),
        unresolved_risks_acknowledged=[],
        approved_artifacts={"research_packet": {"status": "approved"}},
        preserved_artifacts=["research_packet"],
        persistence=store,
    )

    assert governed.accountability.approved_by.actor_type == "HUMAN"
    assert governed.decision_history[0].decided_by == "Morgan Lee"
    artifact = store.artifacts["approved_artifacts"]["research_packet"]
    assert artifact["accountability"]["approved_by"]["actor_type"] == "HUMAN"
    assert artifact["accountability"]["human_final_authority"] is True


def test_graph_snapshot_contains_compact_role_accountability(monkeypatch):
    bundle = add_pending_accountability(review_bundle())

    class PendingPersistence:
        def load_runtime_state(self, production_name):
            return None

        def load_pending_review_bundle(self, production_name):
            return bundle

    import studio_command.service as service
    monkeypatch.setattr(service, "production_persistence", PendingPersistence())

    node = live_studio_snapshot(PRODUCTION)["graph"]["nodes"][0]
    assert node["accountability"]["responsible_role"] == node["responsible_role"]
    assert node["accountability"]["ai_agent_responsible"] is None
    assert node["accountability"]["current_status"] == node["status"]
    assert node["accountability"]["human_final_authority"] is True
