from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256

import pytest

import studio_command.persistence as persistence_module
from studio_command.decisions import apply_verified_evidence_amendment
from studio_command.persistence import ProductionPersistence
from studio_command.refresh import REFRESH_ORDER, apply_selective_refresh
from test_evidence_amendment import TARGET, REMAINING, amendment, runtime, Document, FirestoreClient


def amended_runtime():
    return apply_verified_evidence_amendment(runtime_state=runtime(), amendment=amendment())


def rebuilt_bundle():
    return {key: {"production_name": TARGET, "key": key} for key in REFRESH_ORDER}


def approved_bundle():
    return {"production_brief": {"immutable": ["original"]}, "delivery_artifacts": ["master.mov"], **rebuilt_bundle()}


def test_selective_refresh_preserves_history_conditions_and_unaffected_artifacts():
    before = amended_runtime(); approved = approved_bundle(); original = deepcopy(approved["production_brief"])
    updated, merged = apply_selective_refresh(
        runtime_state=before, rebuilt_artifacts=rebuilt_bundle(),
        approved_artifacts=approved, refreshed_at=datetime(2026, 9, 6, tzinfo=timezone.utc),
    )
    assert updated.workflow_state.active_conditions == REMAINING
    assert updated.decision_history == before.decision_history
    assert updated.evidence_amendments == before.evidence_amendments
    assert updated.memory_snapshot.stale_artifacts == []
    assert updated.artifact_refreshes[-1].rebuilt_artifacts == list(REFRESH_ORDER)
    assert updated.artifact_refreshes[-1].active_conditions == REMAINING
    assert merged["production_brief"] == original
    assert updated.execution_authorized is False
    assert updated.current_stage == "CONDITIONS_BLOCK_EXECUTION"


def test_partial_or_reordered_refresh_fails_closed():
    before = amended_runtime(); rebuilt = rebuilt_bundle(); rebuilt.pop("decision_package")
    with pytest.raises(ValueError, match="every stale artifact"):
        apply_selective_refresh(runtime_state=before, rebuilt_artifacts=rebuilt, approved_artifacts=approved_bundle())
    reordered = dict(reversed(list(rebuilt_bundle().items())))
    with pytest.raises(ValueError, match="exact graph order"):
        apply_selective_refresh(runtime_state=before, rebuilt_artifacts=reordered, approved_artifacts=approved_bundle())


def test_transaction_installs_runtime_and_artifacts_in_one_write(monkeypatch):
    monkeypatch.setattr(persistence_module.firestore, "transactional", lambda fn: fn)
    before = amended_runtime(); approved = approved_bundle()
    doc = Document({**before.model_dump(mode="json"), "approved_artifacts": approved})
    client = FirestoreClient({sha256(TARGET.encode()).hexdigest(): doc})
    store = ProductionPersistence.__new__(ProductionPersistence)
    store.config = persistence_module.ProductionPersistenceConfig()
    store.firestore_client = client; store.storage_client = object()
    monkeypatch.setattr(persistence_module, "rebuild_platform_amendment_artifacts", lambda **kwargs: rebuilt_bundle())
    updated, merged = store.refresh_stale_artifacts(production_name=TARGET)
    assert len(client.last_transaction.writes) == 1
    written = client.last_transaction.writes[0][1]
    assert written["memory_snapshot"]["stale_artifacts"] == []
    assert written["artifact_refreshes"][-1]["active_conditions"] == REMAINING
    assert written["approved_artifacts"]["production_brief"] == approved["production_brief"]
    assert updated.memory_snapshot.stale_artifacts == []
    assert merged["decision_package"]["key"] == "decision_package"


def test_transaction_validation_failure_performs_no_write(monkeypatch):
    monkeypatch.setattr(persistence_module.firestore, "transactional", lambda fn: fn)
    before = amended_runtime(); doc = Document({**before.model_dump(mode="json"), "approved_artifacts": approved_bundle()})
    client = FirestoreClient({sha256(TARGET.encode()).hexdigest(): doc})
    store = ProductionPersistence.__new__(ProductionPersistence); store.config = persistence_module.ProductionPersistenceConfig(); store.firestore_client = client; store.storage_client = object()
    monkeypatch.setattr(persistence_module, "rebuild_platform_amendment_artifacts", lambda **kwargs: (_ for _ in ()).throw(ValueError("validation failed")))
    with pytest.raises(ValueError, match="validation failed"):
        store.refresh_stale_artifacts(production_name=TARGET)
    assert client.last_transaction.writes == []


def test_refresh_endpoint_requires_studio_head(monkeypatch):
    from test_evidence_amendment import client
    test_client, persistence = client(monkeypatch, head=False)
    response = test_client.post(f"/api/productions/{TARGET}/refresh-stale-artifacts")
    assert response.status_code == 403
    assert persistence.called is False
