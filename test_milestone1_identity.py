import pytest

from studio_command.identity import canonical_production_name
from studio_command.persistence import ProductionPersistence, ProductionPersistenceConfig
from studio_command.service import live_studio_snapshot
from test_milestone19 import production_plan, production_schedule
from test_milestone22 import runtime


PRODUCTION = "Luxury Wellness Campaign"


class Snapshot:
    def __init__(self, payload):
        self.payload = payload
        self.exists = payload is not None

    def to_dict(self):
        return self.payload


class Document:
    def __init__(self, store, key):
        self.store = store
        self.key = key

    def set(self, payload, merge=False):
        current = dict(self.store.get(self.key, {})) if merge else {}
        current.update(payload)
        self.store[self.key] = current

    def get(self):
        return Snapshot(self.store.get(self.key))


class Collection:
    def __init__(self, store, name):
        self.store = store
        self.name = name

    def document(self, name):
        return Document(self.store, f"{self.name}/{name}")


class Firestore:
    def __init__(self):
        self.store = {}

    def collection(self, name):
        return Collection(self.store, name)


class Storage:
    pass


def review_bundle():
    return {
        "production_brief": {"production_title": PRODUCTION, "objective": "Ship."},
        "research_packet": {"overall_summary": "Evidence is available."},
        "creative_treatment": {"script_direction": "Restrained."},
        "production_plan": production_plan.model_dump(mode="json"),
        "production_schedule": production_schedule.model_dump(mode="json"),
        "asset_media_plan": {"asset_requirements": []},
        "clearance_compliance_report": {"clearance_decision": "CLEAR"},
        "verification_qa_report": {"qa_decision": "PASS"},
        "studio_head_decision_package": {
            "production_name": PRODUCTION,
            "recommended_decision": "APPROVE",
        },
    }


def test_pending_identity_is_explicit_and_resolves_legacy_documents():
    firestore = Firestore()
    persistence = ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test"),
        firestore_client=firestore,
        storage_client=Storage(),
    )
    bundle = review_bundle()

    persistence.save_pending_review_bundle(
        production_name=f"  {PRODUCTION}  ",
        review_bundle=bundle,
    )
    raw = persistence.get_raw_production_document(PRODUCTION)

    assert canonical_production_name(f" {PRODUCTION} ") == PRODUCTION
    assert raw["production_name"] == PRODUCTION
    assert persistence.load_pending_review_bundle(PRODUCTION) == bundle

    raw.pop("production_name")
    assert persistence.load_pending_review_bundle(PRODUCTION) == bundle


def test_mismatched_pending_identity_is_rejected():
    persistence = ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test"),
        firestore_client=Firestore(),
        storage_client=Storage(),
    )
    bundle = review_bundle()
    bundle["production_schedule"]["production_name"] = "Different Production"

    with pytest.raises(ValueError, match="canonical production"):
        persistence.save_pending_review_bundle(
            production_name=PRODUCTION,
            review_bundle=bundle,
        )


def test_pending_node_intelligence_is_available_before_approval(monkeypatch):
    bundle = review_bundle()

    class PendingPersistence:
        def load_runtime_state(self, production_name):
            return None

        def load_pending_review_bundle(self, production_name):
            assert production_name == PRODUCTION
            return bundle

    import studio_command.service as service
    monkeypatch.setattr(service, "production_persistence", PendingPersistence())

    snapshot = live_studio_snapshot(PRODUCTION)

    assert snapshot["approval_status"] == "PENDING_STUDIO_HEAD_REVIEW"
    assert snapshot["execution_authorized"] is False
    assert snapshot["node_intelligence"]["Research"] == bundle["research_packet"]
    assert snapshot["node_intelligence"]["Studio Head Decision"] == bundle[
        "studio_head_decision_package"
    ]


def test_approved_runtime_node_intelligence_is_preserved(monkeypatch):
    artifacts = review_bundle()
    artifacts["clearance_report"] = artifacts.pop("clearance_compliance_report")
    artifacts["verification_report"] = artifacts.pop("verification_qa_report")
    artifacts["decision_package"] = artifacts.pop("studio_head_decision_package")

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

    assert snapshot["approval_status"] == "APPROVED"
    assert snapshot["execution_authorized"] is True
    assert snapshot["node_intelligence"]["Research"] == artifacts["research_packet"]
