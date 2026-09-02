import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from studio_command.accountability import human_actor
from studio_command.auth import SESSION_COOKIE, SessionError, issue_session, resolve_crew_identity, verify_session
from studio_command.models import (
    AccountabilityMetadata, CrewMember, CrewProductionAssignment,
    ProductionAssetRegistry,
)
from studio_command.runtime_config import RuntimeConfig, SecretConfigurationError, load_runtime_config

SECRET = "session-test-secret-that-is-at-least-32-bytes"
PRODUCTION = "Luxury Wellness Campaign"


def member(subject="crew-1", name="Taylor", *, role="Editor", head=False):
    return CrewMember(
        user_id=f"user-{subject}", auth_subject=subject, display_name=name,
        organization_id="kevaro-studios",
        assignments=[CrewProductionAssignment(
            production_name=PRODUCTION, roles=[role],
            owned_node_ids=["Asset & Media"],
            reviewer_node_ids=["Asset & Media"] if role == "Reviewer" else [],
            studio_head=head,
        )],
    )


class CrewStore:
    def __init__(self, members):
        self.members = {item.auth_subject: item for item in members}
        self.registry = None

    def load_crew_member(self, subject):
        return self.members.get(subject)

    def load_runtime_state(self, production_name):
        return None

    def upload_production_asset_bytes(self, **kwargs):
        return "gs://test/safe/asset.mov"

    def save_asset_registry(self, registry):
        self.registry = registry

    def load_asset_registry(self, production_name):
        return self.registry


def configure(monkeypatch, store):
    import studio_command.service as service
    config = RuntimeConfig(
        "local", "test", "local-environment",
        session_signing_secret=SECRET, local_auth_enabled=True,
    )
    monkeypatch.setattr(service.app.state, "runtime_config", config, raising=False)
    monkeypatch.setattr(service, "production_persistence", store)
    return service, TestClient(service.app)


def signed_client(client, subject):
    client.cookies.set(SESSION_COOKIE, issue_session(subject, SECRET))
    return client


def test_valid_session_resolves_stable_crew_identity():
    store = CrewStore([member()])
    identity = resolve_crew_identity(
        token=issue_session("crew-1", SECRET), secret=SECRET,
        persistence=store, production_name=PRODUCTION,
    )
    assert identity.member.user_id == "user-crew-1"
    assert identity.actor.name == "Taylor"
    assert identity.actor.role == "Editor"


def test_tampered_and_expired_sessions_are_rejected():
    token = issue_session("crew-1", SECRET, now=100)
    with pytest.raises(SessionError):
        verify_session(token + "tampered", SECRET, now=101)
    with pytest.raises(SessionError, match="expired"):
        verify_session(token, SECRET, now=100 + 8 * 60 * 60)


def test_browser_role_claim_cannot_escalate_and_crew_cannot_impersonate_head(monkeypatch):
    service, client = configure(monkeypatch, CrewStore([member()]))
    response = signed_client(client, "crew-1").post(
        f"/api/productions/{PRODUCTION}/finalize",
        params={"actor_name": "Taylor", "actor_role": "Studio Head"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["reason_code"] == "HUMAN_STUDIO_HEAD_REQUIRED"


def test_explicit_studio_head_reaches_governed_mutation(monkeypatch):
    service, client = configure(
        monkeypatch, CrewStore([member("head-1", "Morgan", role="Producer", head=True)])
    )
    response = signed_client(client, "head-1").post(
        f"/api/productions/{PRODUCTION}/finalize"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Governed production runtime was not found."


def test_unauthorized_and_unassigned_users_receive_401_and_403(monkeypatch):
    service, client = configure(monkeypatch, CrewStore([member()]))
    missing = client.get(f"/api/productions/{PRODUCTION}/assets")
    assert missing.status_code == 401
    other = member("other", "Other")
    other.assignments[0].production_name = "Another Production"
    service, client = configure(monkeypatch, CrewStore([other]))
    denied = signed_client(client, "other").get(f"/api/productions/{PRODUCTION}/assets")
    assert denied.status_code == 403


def test_local_auth_requires_explicit_non_deployed_mode(monkeypatch):
    store = CrewStore([member()])
    service, client = configure(monkeypatch, store)
    response = client.post("/api/auth/local", json={"auth_subject": "crew-1"})
    assert response.status_code == 200
    assert SESSION_COOKIE in response.cookies
    monkeypatch.setattr(
        service.app.state, "runtime_config",
        RuntimeConfig("local", "test", "local-environment", session_signing_secret=SECRET),
    )
    assert client.post("/api/auth/local", json={"auth_subject": "crew-1"}).status_code == 404
    monkeypatch.setattr(
        service.app.state, "runtime_config",
        RuntimeConfig("cloud", "test", "google-secret-manager", session_signing_secret=SECRET, local_auth_enabled=True),
    )
    assert client.post("/api/auth/local", json={"auth_subject": "crew-1"}).status_code == 404


def test_deployed_mode_fails_closed_without_session_configuration():
    class Provider:
        def access(self, *, project_id, secret_id):
            return {"parallel-api-key": "parallel", "kevaro-internal-auth-token": "internal"}.get(secret_id, "")
    with pytest.raises(SecretConfigurationError, match="session"):
        load_runtime_config(
            environment={"KEVARO_RUNTIME_MODE": "cloud", "KEVARO_GOOGLE_AUTH_CLIENT_ID": "client"},
            secret_provider=Provider(),
        )


def test_asset_registration_uses_authenticated_owner_and_refreshable_registry(monkeypatch):
    owner = member()
    store = CrewStore([owner])
    service, client = configure(monkeypatch, store)
    metadata = AccountabilityMetadata(
        human_owner=human_actor("Taylor", "Editor"), current_status="READY"
    )
    monkeypatch.setattr(
        service, "_asset_node",
        lambda production_name, node_id: SimpleNamespace(
            node_id=node_id, accountability=metadata, status="READY"
        ),
    )
    response = signed_client(client, "crew-1").post(
        f"/api/productions/{PRODUCTION}/assets/register",
        json={
            "node_id": "Asset & Media", "asset_category": "VIDEO",
            "filename": "hero.mov", "display_name": "Hero",
            "media_document_type": "video/quicktime",
            "content_base64": "Y29udGVudA==", "content_type": "video/quicktime",
            "provenance": {"source": "crew upload"},
        },
    )
    assert response.status_code == 200
    assert response.json()["accountability"]["last_changed_by"]["name"] == "Taylor"
    assert store.registry.assets[0].version_number == 1


def test_reality_shift_uses_authenticated_head_and_ignores_body_authority(monkeypatch):
    store = CrewStore([member("head", "Morgan", head=True)])
    service, client = configure(monkeypatch, store)
    response = signed_client(client, "head").post(
        "/api/reality-shift",
        json={"changed_node_ids": ["Scheduling"], "reason": "Deadline moved."},
    )
    assert response.status_code == 200
    assert "stale_nodes" in response.json()


def test_session_secret_and_token_never_appear_in_public_or_serialized_data():
    token = issue_session("crew-1", SECRET)
    config = RuntimeConfig(
        "cloud", "test", "google-secret-manager",
        session_signing_secret=SECRET, google_auth_client_id="client",
    )
    serialized = json.dumps(config.public_status()) + repr(config) + json.dumps(member().model_dump(mode="json"))
    assert SECRET not in serialized
    assert token not in serialized


def test_google_sign_in_is_explicit_and_reports_all_interaction_states():
    source = (Path(__file__).parent / "frontend/src/GoogleCrewSignIn.jsx").read_text()
    assert "Continue with Google" in source
    assert 'type="button"' in source
    assert "disabled=" in source
    assert "aria-busy=" in source
    for state in ("loading", "signing-in", "success", "error", "unavailable"):
        assert state in source


def test_missing_google_oauth_config_keeps_disabled_action_with_explanation():
    source = (Path(__file__).parent / "frontend/src/GoogleCrewSignIn.jsx").read_text()
    assert 'config?.provider !== "google" || !config.google_client_id' in source
    assert "Google sign-in is temporarily unavailable" in source
    assert 'role={displayState === "error" || displayState === "unavailable" ? "alert" : "status"}' in source


def test_required_actions_follow_visible_semantic_control_rule():
    rule = (Path(__file__).parent / "frontend/INTERACTION_RULES.md").read_text()
    for action in ("Add Details", "Enter Information", "Register Asset", "External Tool Handoff", "Submit Change", "Review", "Approve", "Request Changes"):
        assert action in rule
    assert "visible, semantic CTA or labeled form control" in rule
    assert "placeholder-only instructions" in rule


def test_google_auth_accepts_identity_credential_only_and_fails_closed_without_config(monkeypatch):
    service, client = configure(monkeypatch, CrewStore([member()]))
    unavailable = client.post("/api/auth/google", json={"credential": "google-token"})
    assert unavailable.status_code == 503
    bypass = client.post(
        "/api/auth/google",
        json={"credential": "google-token", "actor_role": "Studio Head", "studio_head": True},
    )
    assert bypass.status_code == 503
    assert set(service.SignInRequest.model_fields) == {"credential"}
