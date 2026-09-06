from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import studio_command.persistence as persistence_module
import studio_command.service as service
from studio_command.accountability import human_actor
from studio_command.auth import SESSION_COOKIE, issue_session
from studio_command.decisions import (
    apply_verified_evidence_amendment,
    build_governed_production_runtime_state,
    build_production_execution_authorization,
    derive_production_workflow_state,
    evidence_amendment_stale_artifacts,
    record_studio_head_decision,
    build_production_decision_history_entry,
)
from studio_command.models import (
    CrewMember,
    CrewProductionAssignment,
    EvidenceSourceReference,
    GovernedEvidenceAmendment,
)
from studio_command.persistence import ProductionPersistence
from studio_command.runtime_config import RuntimeConfig
from test_milestone10 import make_package

TARGET = "Aurelian Parallel E2E Certification 20260903-B"
SOURCE = "Aurelian Renewal Retreat Campaign"
PLATFORM = "Missing Client/Studio Head Input: Specific Target Social Media Platforms"
REMAINING = [
    "Missing Client/Studio Head Input: Detailed Brand Guidelines",
    "Missing Client/Studio Head Input: Content Upload Methods",
    "Missing Client/Studio Head Input: Detailed Budget Constraints",
    "Missing Client/Studio Head Input: Product Usage Permission (for prop)",
    "Unresolved Licensing for Key Assets (Talent, Locations, Music, Fonts, SFX)",
]
CONDITIONS = [PLATFORM, *REMAINING]
PLATFORM_VALUE = "Technical delivery: Platform-safe versions for Instagram Reels, YouTube Shorts, and web/social"


def runtime():
    package = make_package(blockers=CONDITIONS, recommendation="APPROVE WITH CONDITIONS").model_copy(
        update={"production_name": TARGET}
    )
    decision = record_studio_head_decision(
        production_name=TARGET,
        decision="APPROVE WITH CONDITIONS",
        conditions=CONDITIONS,
        decision_notes="Preserve material blockers.",
        decided_by="Morgan Lee",
        decision_package=package,
        unresolved_risks_acknowledged=CONDITIONS,
    )
    workflow = derive_production_workflow_state(decision)
    history = build_production_decision_history_entry(
        sequence=1, decision_record=decision, workflow_state=workflow
    )
    return build_governed_production_runtime_state(
        workflow_state=workflow,
        decision_history=[history],
        preserved_artifacts=[
            "production_brief", "research_packet", "creative_treatment",
            "production_plan", "production_schedule", "asset_media_plan",
            "clearance_report", "verification_report", "decision_package",
        ],
    )


def amendment(condition=PLATFORM, actor=None):
    return GovernedEvidenceAmendment(
        production_name=TARGET,
        resolved_condition=condition,
        resolution_summary="Persisted scenario explicitly identifies the delivery platforms.",
        amended_artifact="production_brief",
        source_references=[EvidenceSourceReference(
            source_production_name=SOURCE,
            artifact_key="production_brief",
            field_path=["production_constraints", 0],
            verified_value=PLATFORM_VALUE,
        )],
        stale_artifacts=evidence_amendment_stale_artifacts("production_brief"),
        recorded_by=actor or human_actor("Morgan Lee"),
        recorded_at="2026-09-06T00:00:00Z",
    )


def test_exact_condition_preserves_five_history_and_appends_provenance():
    before = runtime()
    original_history = before.decision_history
    updated = apply_verified_evidence_amendment(runtime_state=before, amendment=amendment())
    assert updated.workflow_state.active_conditions == REMAINING
    assert updated.decision_history == original_history
    assert len(updated.evidence_amendments) == 1
    assert updated.evidence_amendments[0].source_references[0].verified_value == PLATFORM_VALUE
    assert updated.current_stage == "EVIDENCE_REFRESH_REQUIRED"
    assert updated.execution_authorized is False
    assert updated.corrective_cycle_active is True
    assert updated.memory_snapshot.stale_artifacts == [
        "research_packet", "creative_treatment", "production_plan",
        "production_schedule", "asset_media_plan", "clearance_report",
        "verification_report", "decision_package",
    ]
    assert updated.memory_snapshot.preserved_artifacts == ["production_brief"]
    authorization = build_production_execution_authorization(
        runtime_state=updated, requested_actions=["Finalize production"]
    )
    assert authorization.may_execute is False
    assert "Corrective work or re-verification is still active." in authorization.blockers


def test_wrong_target_production_is_rejected():
    wrong = amendment().model_copy(update={"production_name": SOURCE})
    with pytest.raises(ValueError, match="Production identity"):
        apply_verified_evidence_amendment(runtime_state=runtime(), amendment=wrong)


def test_similar_condition_and_non_studio_head_are_rejected():
    with pytest.raises(ValueError, match="exact active condition"):
        apply_verified_evidence_amendment(
            runtime_state=runtime(), amendment=amendment("Specific Target Social Media Platforms")
        )
    with pytest.raises(ValueError, match="Studio Head authority"):
        apply_verified_evidence_amendment(
            runtime_state=runtime(), amendment=amendment(actor=human_actor("Editor", "Editor"))
        )


class Snapshot:
    def __init__(self, payload):
        self.payload = payload
        self.exists = payload is not None
    def to_dict(self):
        return deepcopy(self.payload)


class Document:
    def __init__(self, payload):
        self.payload = payload
    def get(self, transaction=None):
        return Snapshot(self.payload)


class Collection:
    def __init__(self, documents):
        self.documents = documents
    def document(self, document_id):
        return self.documents.setdefault(document_id, Document(None))


class Transaction:
    def __init__(self):
        self.writes = []
    def set(self, document, payload, merge=False):
        self.writes.append((document, deepcopy(payload), merge))
        document.payload = deepcopy(payload)


class FirestoreClient:
    def __init__(self, documents):
        self.documents = documents
        self.last_transaction = None
    def collection(self, name):
        return Collection(self.documents)
    def transaction(self):
        self.last_transaction = Transaction()
        return self.last_transaction


def source_bundle(source_name=SOURCE):
    return {
        "production_brief": {"production_constraints": [PLATFORM_VALUE]},
        "production_plan": {"production_name": source_name},
        "production_schedule": {"production_name": source_name},
        "studio_head_decision_package": {"production_name": source_name},
    }


def store(monkeypatch, source_name=SOURCE):
    monkeypatch.setattr(persistence_module.firestore, "transactional", lambda fn: fn)
    target_id = ProductionPersistence.__new__(ProductionPersistence)
    target_id.config = persistence_module.ProductionPersistenceConfig()
    from hashlib import sha256
    documents = {
        sha256(TARGET.encode()).hexdigest(): Document(runtime().model_dump(mode="json")),
        sha256(SOURCE.encode()).hexdigest(): Document({
            "pending_review_bundle": source_bundle(source_name)
        }),
    }
    client = FirestoreClient(documents)
    target_id.firestore_client = client
    target_id.storage_client = object()
    return target_id, client


def reconcile(store, expected_value=PLATFORM_VALUE, path=None, source_name=SOURCE):
    return store.reconcile_condition_with_evidence(
        production_name=TARGET,
        condition=PLATFORM,
        resolution_summary="Verified exact platforms from the persisted source brief.",
        amended_artifact="production_brief",
        source_references=[{
            "source_production_name": source_name,
            "artifact_key": "production_brief",
            "field_path": path or ["production_constraints", 0],
            "expected_value": expected_value,
        }],
        recorded_by=human_actor("Morgan Lee"),
    )


def test_transaction_verifies_source_and_performs_one_atomic_write(monkeypatch):
    persistence, client = store(monkeypatch)
    updated = reconcile(persistence)
    assert updated.workflow_state.active_conditions == REMAINING
    assert len(client.last_transaction.writes) == 1
    written = client.last_transaction.writes[0][1]
    assert written["evidence_amendments"][0]["source_references"][0]["verified_value"] == PLATFORM_VALUE
    assert len(written["decision_history"]) == 1
    assert written["decision_history"][0]["active_conditions"] == CONDITIONS


@pytest.mark.parametrize("kwargs, message", [
    ({"expected_value": "TikTok"}, "does not match"),
    ({"path": ["missing"]}, "does not exist exactly"),
])
def test_forged_or_missing_evidence_rejected_without_write(monkeypatch, kwargs, message):
    persistence, client = store(monkeypatch)
    with pytest.raises(ValueError, match=message):
        reconcile(persistence, **kwargs)
    assert client.last_transaction.writes == []


def test_empty_or_ambiguous_evidence_rejected_without_write(monkeypatch):
    persistence, client = store(monkeypatch)
    with pytest.raises(ValueError, match="verified source evidence"):
        persistence.reconcile_condition_with_evidence(
            production_name=TARGET, condition=PLATFORM,
            resolution_summary="Missing evidence.", amended_artifact="production_brief",
            source_references=[], recorded_by=human_actor("Morgan Lee"),
        )
    assert client.last_transaction.writes == []

    reference = {
        "source_production_name": SOURCE, "artifact_key": "production_brief",
        "field_path": ["production_constraints", 0], "expected_value": PLATFORM_VALUE,
    }
    with pytest.raises(ValueError, match="unambiguous and unique"):
        persistence.reconcile_condition_with_evidence(
            production_name=TARGET, condition=PLATFORM,
            resolution_summary="Duplicate evidence.", amended_artifact="production_brief",
            source_references=[reference, reference], recorded_by=human_actor("Morgan Lee"),
        )
    assert client.last_transaction.writes == []


def test_wrong_source_identity_rejected_without_write(monkeypatch):
    persistence, client = store(monkeypatch, source_name="Wrong Production")
    with pytest.raises(ValueError, match="Production identity"):
        reconcile(persistence)
    assert client.last_transaction.writes == []


SECRET = "evidence-amendment-test-secret-at-least-32-bytes"


class ServiceStore:
    def __init__(self, member):
        self.member = member
        self.called = False
    def load_crew_member(self, subject):
        return self.member if subject == self.member.auth_subject else None
    def reconcile_condition_with_evidence(self, **kwargs):
        self.called = True
        return apply_verified_evidence_amendment(
            runtime_state=runtime(), amendment=amendment(actor=kwargs["recorded_by"])
        )


def client(monkeypatch, head):
    member = CrewMember(
        user_id="crew", auth_subject="subject", display_name="Morgan Lee",
        organization_id="kevaro", assignments=[CrewProductionAssignment(
            production_name=TARGET, roles=["Producer"], studio_head=head,
        )],
    )
    persistence = ServiceStore(member)
    monkeypatch.setattr(service, "production_persistence", persistence)
    monkeypatch.setattr(
        service.app.state, "runtime_config",
        RuntimeConfig("local", "test", "local-environment", session_signing_secret=SECRET),
        raising=False,
    )
    test_client = TestClient(service.app)
    test_client.cookies.set(SESSION_COOKIE, issue_session("subject", SECRET))
    return test_client, persistence


def request_body():
    return {
        "resolved_condition": PLATFORM,
        "resolution_summary": "Verified exact platforms.",
        "amended_artifact": "production_brief",
        "source_references": [{
            "source_production_name": SOURCE,
            "artifact_key": "production_brief",
            "field_path": ["production_constraints", 0],
            "expected_value": PLATFORM_VALUE,
        }],
    }


def test_endpoint_requires_authenticated_studio_head(monkeypatch):
    test_client, persistence = client(monkeypatch, head=False)
    response = test_client.post(
        f"/api/productions/{TARGET}/evidence-amendments", json=request_body()
    )
    assert response.status_code == 403
    assert persistence.called is False


def test_endpoint_returns_governed_result_for_studio_head(monkeypatch):
    test_client, persistence = client(monkeypatch, head=True)
    response = test_client.post(
        f"/api/productions/{TARGET}/evidence-amendments", json=request_body()
    )
    assert response.status_code == 200
    assert response.json()["active_conditions"] == REMAINING
    assert persistence.called is True
