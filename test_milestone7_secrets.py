import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from studio_command.runtime_config import (
    RuntimeConfig,
    SecretConfigurationError,
    load_runtime_config,
)
from studio_command.tools import search_web

PARALLEL_VALUE = "parallel-test-value-not-a-real-secret"
AUTH_VALUE = "auth-test-value-not-a-real-secret"
SESSION_VALUE = "session-test-value-at-least-thirty-two-bytes"


class Provider:
    def __init__(self, values=None, failure=False):
        self.values = values or {}
        self.failure = failure
        self.requests = []

    def access(self, *, project_id, secret_id):
        self.requests.append((project_id, secret_id))
        if self.failure:
            raise PermissionError("provider denied access")
        return self.values.get(secret_id, "")


def cloud_environment():
    return {"KEVARO_RUNTIME_MODE": "cloud", "GOOGLE_CLOUD_PROJECT": "kevaro-studio-command", "KEVARO_GOOGLE_AUTH_CLIENT_ID": "google-client"}


def test_secret_manager_backed_loading_uses_project_and_both_required_secrets():
    provider = Provider({
        "parallel-api-key": PARALLEL_VALUE,
        "kevaro-internal-auth-token": AUTH_VALUE,
        "kevaro-session-signing-secret": SESSION_VALUE,
    })
    config = load_runtime_config(environment=cloud_environment(), secret_provider=provider)
    assert config.parallel_api_key == PARALLEL_VALUE
    assert config.internal_auth_token == AUTH_VALUE
    assert config.secret_source == "google-secret-manager"
    assert provider.requests == [
        ("kevaro-studio-command", "parallel-api-key"),
        ("kevaro-studio-command", "kevaro-internal-auth-token"),
        ("kevaro-studio-command", "kevaro-session-signing-secret"),
    ]


def test_local_environment_fallback_is_permitted_without_provider_access():
    provider = Provider(failure=True)
    config = load_runtime_config(
        environment={"KEVARO_RUNTIME_MODE": "local", "PARALLEL_API_KEY": PARALLEL_VALUE},
        secret_provider=provider,
    )
    assert config.parallel_api_key == PARALLEL_VALUE
    assert config.internal_auth_token is None
    assert provider.requests == []


def test_cloud_mode_does_not_fallback_to_environment_secrets():
    environment = cloud_environment() | {
        "PARALLEL_API_KEY": PARALLEL_VALUE,
        "KEVARO_INTERNAL_AUTH_TOKEN": AUTH_VALUE,
    }
    with pytest.raises(SecretConfigurationError, match="parallel-api-key"):
        load_runtime_config(environment=environment, secret_provider=Provider(failure=True))


def test_cloud_mode_fails_closed_for_empty_required_secret():
    provider = Provider({"parallel-api-key": PARALLEL_VALUE})
    with pytest.raises(SecretConfigurationError, match="kevaro-internal-auth-token"):
        load_runtime_config(environment=cloud_environment(), secret_provider=provider)


def test_public_status_and_repr_never_contain_secret_values():
    config = RuntimeConfig(
        "cloud", "kevaro-studio-command", "google-secret-manager",
        PARALLEL_VALUE, AUTH_VALUE, "Morgan Lee",
    )
    serialized = json.dumps(config.public_status()) + repr(config)
    assert PARALLEL_VALUE not in serialized
    assert AUTH_VALUE not in serialized
    assert config.public_status() == {
        "google_cloud_runtime": "configured",
        "secret_manager": "configured",
        "parallel_credential": "configured",
        "protected_mutation_auth_boundary": "enabled",
        "crew_session_auth": "disabled",
    }


def test_health_exposes_only_non_secret_runtime_configuration(monkeypatch):
    import studio_command.service as service
    config = RuntimeConfig("cloud", "kevaro-studio-command", "google-secret-manager", PARALLEL_VALUE, AUTH_VALUE)
    monkeypatch.setattr(service.app.state, "runtime_config", config, raising=False)
    payload = TestClient(service.app).get("/health").json()
    serialized = json.dumps(payload)
    assert payload["runtime_configuration"]["secret_manager"] == "configured"
    assert PARALLEL_VALUE not in serialized
    assert AUTH_VALUE not in serialized


def test_parallel_receives_credential_from_secret_provider_config(monkeypatch):
    response = SimpleNamespace(search_id="s1", session_id="session1", results=[], usage=[], warnings=[])
    class Client:
        def __init__(self, api_key):
            assert api_key == PARALLEL_VALUE
        def search(self, **kwargs):
            return response
    monkeypatch.setattr("studio_command.tools.Parallel", Client)
    config = load_runtime_config(
        environment=cloud_environment(),
        secret_provider=Provider({"parallel-api-key": PARALLEL_VALUE, "kevaro-internal-auth-token": AUTH_VALUE, "kevaro-session-signing-secret": SESSION_VALUE}),
    )
    result = search_web("bounded objective", ["bounded query"], runtime_config=config)
    assert result["status"] == "success"
    assert PARALLEL_VALUE not in json.dumps(result)


def test_public_mutation_identity_is_server_bound_even_with_valid_token(monkeypatch):
    import studio_command.service as service
    config = RuntimeConfig("cloud", "kevaro-studio-command", "google-secret-manager", PARALLEL_VALUE, AUTH_VALUE, "Morgan Lee", SESSION_VALUE, "google-client")
    monkeypatch.setattr(service.app.state, "runtime_config", config, raising=False)
    response = TestClient(service.app).post(
        "/api/productions/Production/assets/register",
        params={"actor_name": "Attacker", "actor_role": "Studio Head"},
        headers={"x-kevaro-internal-token": AUTH_VALUE},
        json={},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["reason_code"] == "AUTHENTICATED_SESSION_REQUIRED"
