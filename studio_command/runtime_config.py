from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping, Protocol

DEFAULT_GOOGLE_CLOUD_PROJECT = "kevaro-studio-command"
PARALLEL_SECRET_ID = "parallel-api-key"
INTERNAL_AUTH_SECRET_ID = "kevaro-internal-auth-token"


class SecretConfigurationError(RuntimeError):
    """A required runtime secret could not be configured safely."""


class SecretProvider(Protocol):
    def access(self, *, project_id: str, secret_id: str) -> str: ...


class GoogleSecretManagerProvider:
    def __init__(self, client=None) -> None:
        if client is None:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
        self._client = client

    def access(self, *, project_id: str, secret_id: str) -> str:
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = self._client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8").strip()


@dataclass(frozen=True)
class RuntimeConfig:
    deployment_mode: str
    google_cloud_project: str
    secret_source: str
    parallel_api_key: str | None = field(default=None, repr=False)
    internal_auth_token: str | None = field(default=None, repr=False)
    studio_head_name: str = "Studio Head"

    @property
    def deployed(self) -> bool:
        return self.deployment_mode == "cloud"

    def public_status(self) -> dict[str, str]:
        return {
            "google_cloud_runtime": "configured" if self.deployed else "unavailable",
            "secret_manager": "configured" if self.secret_source == "google-secret-manager" else "unavailable",
            "parallel_credential": "configured" if self.parallel_api_key else "unavailable",
            "protected_mutation_auth_boundary": "enabled" if self.internal_auth_token else "disabled",
        }


def _cloud_mode(environment: Mapping[str, str]) -> bool:
    explicit = environment.get("KEVARO_RUNTIME_MODE", "").strip().casefold()
    if explicit in {"cloud", "deployed", "production"}:
        return True
    if explicit in {"local", "development", "test"}:
        return False
    return bool(environment.get("K_SERVICE"))


def _secret(provider: SecretProvider, *, project_id: str, secret_id: str) -> str | None:
    try:
        value = provider.access(project_id=project_id, secret_id=secret_id)
    except Exception as exc:
        raise SecretConfigurationError(f"Required deployed secret '{secret_id}' is unavailable.") from exc
    return value or None


def load_runtime_config(*, environment: Mapping[str, str] | None = None, secret_provider: SecretProvider | None = None) -> RuntimeConfig:
    environment = environment if environment is not None else os.environ
    deployed = _cloud_mode(environment)
    project_id = environment.get("GOOGLE_CLOUD_PROJECT") or environment.get("GCP_PROJECT") or DEFAULT_GOOGLE_CLOUD_PROJECT
    studio_head_name = environment.get("KEVARO_STUDIO_HEAD_NAME", "Studio Head")
    if deployed:
        provider = secret_provider or GoogleSecretManagerProvider()
        parallel_secret_id = environment.get("KEVARO_PARALLEL_SECRET_ID", PARALLEL_SECRET_ID)
        auth_secret_id = environment.get("KEVARO_INTERNAL_AUTH_SECRET_ID", INTERNAL_AUTH_SECRET_ID)
        parallel_key = _secret(provider, project_id=project_id, secret_id=parallel_secret_id)
        internal_token = _secret(provider, project_id=project_id, secret_id=auth_secret_id)
        if not parallel_key or not internal_token:
            missing = [name for name, value in ((parallel_secret_id, parallel_key), (auth_secret_id, internal_token)) if not value]
            raise SecretConfigurationError("Required deployed secrets are empty: " + ", ".join(missing))
        return RuntimeConfig("cloud", project_id, "google-secret-manager", parallel_key, internal_token, studio_head_name)
    return RuntimeConfig(
        "local", project_id, "local-environment",
        environment.get("PARALLEL_API_KEY") or None,
        environment.get("KEVARO_INTERNAL_AUTH_TOKEN") or None,
        studio_head_name,
    )
