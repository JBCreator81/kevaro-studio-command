from studio_command.decisions import (
    build_governed_production_runtime_state,
    build_production_decision_history_entry,
    derive_production_workflow_state,
    record_studio_head_decision,
)
from studio_command.models import StudioHeadDecisionPackage
from studio_command.persistence import (
    ProductionPersistence,
    ProductionPersistenceConfig,
)


class FakeDocumentSnapshot:
    def __init__(self, payload=None):
        self._payload = payload
        self.exists = payload is not None

    def to_dict(self):
        return self._payload


class FakeDocument:
    def __init__(self, store, path):
        self.store = store
        self.path = path

    def set(self, payload, merge=False):
        if merge and self.path in self.store:
            current = dict(self.store[self.path])
            current.update(payload)
            self.store[self.path] = current
        else:
            self.store[self.path] = payload

    def get(self):
        return FakeDocumentSnapshot(
            self.store.get(self.path)
        )

    def collection(self, name):
        return FakeCollection(
            self.store,
            f"{self.path}/{name}",
        )


class FakeCollection:
    def __init__(self, store, path):
        self.store = store
        self.path = path

    def document(self, name):
        return FakeDocument(
            self.store,
            f"{self.path}/{name}",
        )


class FakeFirestoreClient:
    def __init__(self):
        self.store = {}

    def collection(self, name):
        return FakeCollection(
            self.store,
            name,
        )


class FakeBlob:
    def __init__(self, uploads, name):
        self.uploads = uploads
        self.name = name

    def upload_from_string(self, data, content_type=None):
        self.uploads[self.name] = {
            "data": data,
            "content_type": content_type,
        }


class FakeBucket:
    def __init__(self, uploads):
        self.uploads = uploads

    def blob(self, name):
        return FakeBlob(
            self.uploads,
            name,
        )


class FakeStorageClient:
    def __init__(self):
        self.uploads = {}

    def bucket(self, name):
        return FakeBucket(
            self.uploads,
        )


def make_package():
    return StudioHeadDecisionPackage(
        production_name="Luxury Wellness Campaign",
        executive_summary="Milestone 18 persistence test.",
        qa_decision="PASS",
        readiness_score=100,
        clearance_status="CLEAR TO PROCEED",
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


decision = record_studio_head_decision(
    production_name="Luxury Wellness Campaign",
    decision="APPROVE",
    conditions=[],
    decision_notes="Approved for Milestone 18 test.",
    decided_by="Studio Head",
    decision_package=make_package(),
    unresolved_risks_acknowledged=[],
)

workflow_state = derive_production_workflow_state(
    decision
)

history = build_production_decision_history_entry(
    sequence=1,
    decision_record=decision,
    workflow_state=workflow_state,
)

runtime = build_governed_production_runtime_state(
    workflow_state=workflow_state,
    decision_history=[history],
    preserved_artifacts=[
        "Audience Research",
        "Campaign Strategy",
        "Hero Edit",
    ],
)

fake_firestore = FakeFirestoreClient()
fake_storage = FakeStorageClient()

persistence = ProductionPersistence(
    config=ProductionPersistenceConfig(
        project_id="test-project",
        bucket_name="test-bucket",
        productions_collection="productions",
    ),
    firestore_client=fake_firestore,
    storage_client=fake_storage,
)

# Save current runtime state
persistence.save_runtime_state(runtime)

assert persistence.production_exists(
    "Luxury Wellness Campaign"
) is True

loaded = persistence.load_runtime_state(
    "Luxury Wellness Campaign"
)

assert loaded is not None
assert loaded.production_name == runtime.production_name
assert loaded.current_stage == runtime.current_stage
assert loaded.execution_authorized is True
assert loaded.memory_snapshot.active_decision_sequence == 1

# Save known-good recovery snapshot
snapshot_id = persistence.save_known_good_snapshot(
    runtime
)

assert snapshot_id == "decision-1"

known_good = persistence.load_known_good_snapshot(
    production_name="Luxury Wellness Campaign",
    snapshot_id=snapshot_id,
)

assert known_good is not None
assert known_good.production_name == runtime.production_name
assert known_good.execution_authorized is True

# Simulate a damaged current state
damaged_runtime = runtime.model_copy(
    update={
        "execution_authorized": False,
        "current_stage": "DAMAGED_TEST_STATE",
    }
)

persistence.save_runtime_state(
    damaged_runtime
)

damaged_loaded = persistence.load_runtime_state(
    "Luxury Wellness Campaign"
)

assert damaged_loaded is not None
assert damaged_loaded.execution_authorized is False
assert damaged_loaded.current_stage == "DAMAGED_TEST_STATE"

# Restore known-good state
restored = persistence.restore_known_good_snapshot(
    production_name="Luxury Wellness Campaign",
    snapshot_id=snapshot_id,
)

assert restored.execution_authorized is True
assert restored.current_stage == "DOWNSTREAM_PRODUCTION"

restored_loaded = persistence.load_runtime_state(
    "Luxury Wellness Campaign"
)

assert restored_loaded is not None
assert restored_loaded.execution_authorized is True
assert restored_loaded.current_stage == "DOWNSTREAM_PRODUCTION"

# Artifact upload must produce a Cloud Storage URI
artifact_uri = persistence.upload_artifact_bytes(
    production_name="Luxury Wellness Campaign",
    artifact_name="hero-edit.mp4",
    data=b"test-video-bytes",
    content_type="video/mp4",
)

assert artifact_uri == (
    "gs://test-bucket/"
    "productions/Luxury Wellness Campaign/"
    "artifacts/hero-edit.mp4"
)

uploaded = fake_storage.uploads[
    "productions/Luxury Wellness Campaign/artifacts/hero-edit.mp4"
]

assert uploaded["data"] == b"test-video-bytes"
assert uploaded["content_type"] == "video/mp4"

# Missing production returns None
assert persistence.load_runtime_state(
    "Unknown Production"
) is None

# Missing recovery snapshot raises during restore
try:
    persistence.restore_known_good_snapshot(
        production_name="Luxury Wellness Campaign",
        snapshot_id="missing-snapshot",
    )
    raise AssertionError(
        "Missing known-good snapshot should fail."
    )
except ValueError:
    pass


print("MILESTONE 18 PERSISTENT PRODUCTION MEMORY VALIDATION: PASS")
