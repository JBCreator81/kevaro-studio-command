import json
from datetime import datetime, timezone
from hashlib import sha256

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import studio_command.service as service
from studio_command.auth import SESSION_COOKIE, issue_session
from studio_command.models import CrewMember, CrewProductionAssignment
from studio_command.persistence import ProductionPersistence
from studio_command.runtime_config import RuntimeConfig
from test_milestone1_identity import review_bundle
from test_milestone19 import production_plan, production_schedule
from test_milestone22 import runtime
from test_milestone25_live_evidence import SAFE_URL, packet


STATIC_PRODUCTION = "Luxury Wellness Campaign"
GOVERNED_PRODUCTION = "Governed Bootstrap Test Production"


def _replace_identity(value, production_name):
    if isinstance(value, dict):
        return {
            key: _replace_identity(item, production_name)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_identity(item, production_name) for item in value]
    return production_name if value == STATIC_PRODUCTION else value


def _governed_payload(production_name=GOVERNED_PRODUCTION):
    payload = _replace_identity(runtime.model_dump(mode="json"), production_name)
    bundle = _replace_identity(review_bundle(), production_name)
    bundle["decision_package"] = bundle.pop("studio_head_decision_package")
    payload["approved_artifacts"] = bundle
    return payload


class Snapshot:
    def __init__(self, production_name, payload, update_time, document_id=None):
        self.id = document_id or sha256(production_name.encode("utf-8")).hexdigest()
        self._payload = payload
        self.update_time = update_time

    def to_dict(self):
        return self._payload


class Collection:
    def __init__(self, snapshots):
        self.snapshots = snapshots

    def stream(self):
        return iter(self.snapshots)


class Firestore:
    def __init__(self, snapshots):
        self.snapshots = snapshots

    def collection(self, _name):
        return Collection(self.snapshots)


class Storage:
    pass


def _persistence(*snapshots):
    return ProductionPersistence(
        firestore_client=Firestore(snapshots), storage_client=Storage()
    )


def test_governed_persisted_production_is_selected_over_static_fallback(
    monkeypatch, tmp_path
):
    persisted = Snapshot(
        GOVERNED_PRODUCTION,
        _governed_payload(),
        datetime(2026, 9, 3, tzinfo=timezone.utc),
    )
    fallback = tmp_path / "studio-snapshot.json"
    fallback.write_text(json.dumps({"production_name": STATIC_PRODUCTION}))
    monkeypatch.setattr(service, "production_persistence", _persistence(persisted))
    monkeypatch.setattr(service, "SNAPSHOT_PATH", fallback)

    bootstrap = service.studio_snapshot()

    assert bootstrap == {
        "production_name": GOVERNED_PRODUCTION,
        "bootstrap_source": "GOVERNED_RUNTIME",
    }


def test_legacy_partial_record_is_ignored_before_governed_runtime(monkeypatch):
    timestamp = datetime(2026, 9, 3, tzinfo=timezone.utc)
    legacy = Snapshot(
        "Legacy Pending Production",
        {"production_name": "Legacy Pending Production", "runtime_state": None},
        timestamp,
    )
    governed = Snapshot(GOVERNED_PRODUCTION, _governed_payload(), timestamp)
    monkeypatch.setattr(
        service, "production_persistence", _persistence(legacy, governed)
    )

    assert service.studio_snapshot() == {
        "production_name": GOVERNED_PRODUCTION,
        "bootstrap_source": "GOVERNED_RUNTIME",
    }


def test_multiple_legacy_partial_records_are_ignored():
    timestamp = datetime(2026, 9, 3, tzinfo=timezone.utc)
    snapshots = [
        Snapshot("Legacy Runtime", {"workflow_state": {}}, timestamp),
        Snapshot(
            "Legacy Artifacts",
            {"approved_artifacts": {"production_plan": {}}},
            timestamp,
        ),
        Snapshot(
            "Legacy Missing Decision",
            {
                "approved_artifacts": {
                    "production_plan": {},
                    "production_schedule": {},
                }
            },
            timestamp,
        ),
        Snapshot(
            "Legacy Incomplete Approved Artifacts",
            {
                "approved_artifacts": {
                    "decision_package": {
                        "production_name": "Legacy Incomplete Approved Artifacts"
                    }
                }
            },
            timestamp,
        ),
    ]

    assert _persistence(*snapshots).current_governed_production_name() is None


def test_no_governed_production_falls_back_safely(monkeypatch, tmp_path):
    fallback = tmp_path / "studio-snapshot.json"
    fallback.write_text(json.dumps({"production_name": STATIC_PRODUCTION}))
    monkeypatch.setattr(service, "production_persistence", _persistence())
    monkeypatch.setattr(service, "SNAPSHOT_PATH", fallback)

    bootstrap = service.studio_snapshot()

    assert bootstrap["production_name"] == STATIC_PRODUCTION
    assert bootstrap["bootstrap_source"] == "STATIC_FALLBACK"


@pytest.mark.parametrize(
    "corruption", ["document_id", "artifact_identity", "ambiguous"]
)
def test_corrupt_or_ambiguous_governed_identity_fails_closed(monkeypatch, corruption):
    timestamp = datetime(2026, 9, 3, tzinfo=timezone.utc)
    first = Snapshot(GOVERNED_PRODUCTION, _governed_payload(), timestamp)
    if corruption == "document_id":
        first.id = sha256(b"Wrong Production").hexdigest()
        snapshots = [first]
    elif corruption == "artifact_identity":
        first._payload["approved_artifacts"]["production_plan"][
            "production_name"
        ] = "Wrong Production"
        snapshots = [first]
    else:
        other = "Other Governed Production"
        snapshots = [
            first,
            Snapshot(other, _governed_payload(other), timestamp),
        ]
    monkeypatch.setattr(service, "production_persistence", _persistence(*snapshots))

    with pytest.raises(HTTPException) as exc_info:
        service.studio_snapshot()

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Current governed production identity is invalid."


def test_authenticated_snapshot_retains_persisted_parallel_projection(monkeypatch):
    production_name = STATIC_PRODUCTION
    approved = {
        "research_packet": packet(),
        "production_plan": production_plan.model_dump(mode="json"),
        "production_schedule": production_schedule.model_dump(mode="json"),
    }
    member = CrewMember(
        user_id="head",
        auth_subject="head-subject",
        display_name="Studio Head",
        organization_id="kevaro",
        assignments=[CrewProductionAssignment(
            production_name=production_name,
            roles=["Producer"],
            studio_head=True,
        )],
    )

    class Persistence:
        def load_crew_member(self, subject):
            return member if subject == member.auth_subject else None

        def load_runtime_state(self, requested_name):
            assert requested_name == production_name
            return runtime

        def load_approved_artifacts(self, requested_name):
            assert requested_name == production_name
            return approved

        def load_final_package(self, _production_name):
            return None

        def load_asset_registry(self, _production_name):
            return None

    secret = "bootstrap-test-session-secret-at-least-32-bytes"
    monkeypatch.setattr(service, "production_persistence", Persistence())
    monkeypatch.setattr(
        service.app.state,
        "runtime_config",
        RuntimeConfig(
            "local",
            "test",
            "local-environment",
            session_signing_secret=secret,
        ),
        raising=False,
    )
    client = TestClient(service.app)
    client.cookies.set(SESSION_COOKIE, issue_session(member.auth_subject, secret))

    response = client.get(
        f"/api/productions/{production_name}/studio-snapshot"
    )

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["production_name"] == production_name
    citation = snapshot["evidence_summary"]["most_relevant_citations"][0]
    assert citation["citation_id"] == "parallel:live-search:1"
    assert citation["url"] == SAFE_URL
    assert (
        snapshot["node_intelligence"]["Research"]["evidence"][0]["sources"][0]["url"]
        == SAFE_URL
    )
