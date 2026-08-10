from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from google.cloud import firestore
from google.cloud import storage

from .models import GovernedProductionRuntimeState


DEFAULT_PROJECT_ID = "kevaro-studio-command"
DEFAULT_BUCKET_NAME = "kevaro-studio-command-production-artifacts"
DEFAULT_PRODUCTIONS_COLLECTION = "productions"


@dataclass(frozen=True)
class ProductionPersistenceConfig:
    project_id: str = DEFAULT_PROJECT_ID
    bucket_name: str = DEFAULT_BUCKET_NAME
    productions_collection: str = DEFAULT_PRODUCTIONS_COLLECTION


class ProductionPersistence:
    def __init__(
        self,
        *,
        config: ProductionPersistenceConfig | None = None,
        firestore_client: firestore.Client | None = None,
        storage_client: storage.Client | None = None,
    ) -> None:
        self.config = config or ProductionPersistenceConfig()

        self.firestore_client = firestore_client or firestore.Client(
            project=self.config.project_id
        )

        self.storage_client = storage_client or storage.Client(
            project=self.config.project_id
        )

    def _production_document(self, production_name: str):
        normalized_name = production_name.strip()

        if not normalized_name:
            raise ValueError(
                "Production name must not be empty."
            )

        document_id = sha256(
            normalized_name.encode("utf-8")
        ).hexdigest()

        return (
            self.firestore_client
            .collection(self.config.productions_collection)
            .document(document_id)
        )

    def save_runtime_state(
        self,
        runtime_state: GovernedProductionRuntimeState,
    ) -> None:
        payload = runtime_state.model_dump(mode="json")

        payload["production_name"] = runtime_state.production_name
        payload["active_decision_sequence"] = (
            runtime_state.memory_snapshot.active_decision_sequence
        )
        payload["current_stage"] = runtime_state.current_stage

        self._production_document(
            runtime_state.production_name
        ).set(
            payload,
            merge=True,
        )

    def load_runtime_state(
        self,
        production_name: str,
    ) -> GovernedProductionRuntimeState | None:
        snapshot = self._production_document(
            production_name
        ).get()

        if not snapshot.exists:
            return None

        payload = snapshot.to_dict()

        if payload is None:
            return None

        return GovernedProductionRuntimeState.model_validate(
            payload
        )

    def save_known_good_snapshot(
        self,
        runtime_state: GovernedProductionRuntimeState,
    ) -> str:
        sequence = (
            runtime_state
            .memory_snapshot
            .active_decision_sequence
        )

        snapshot_id = f"decision-{sequence}"

        payload = runtime_state.model_dump(mode="json")

        (
            self._production_document(
                runtime_state.production_name
            )
            .collection("known_good_snapshots")
            .document(snapshot_id)
            .set(payload)
        )

        return snapshot_id

    def load_known_good_snapshot(
        self,
        *,
        production_name: str,
        snapshot_id: str,
    ) -> GovernedProductionRuntimeState | None:
        snapshot = (
            self._production_document(production_name)
            .collection("known_good_snapshots")
            .document(snapshot_id)
            .get()
        )

        if not snapshot.exists:
            return None

        payload = snapshot.to_dict()

        if payload is None:
            return None

        return GovernedProductionRuntimeState.model_validate(
            payload
        )

    def restore_known_good_snapshot(
        self,
        *,
        production_name: str,
        snapshot_id: str,
    ) -> GovernedProductionRuntimeState:
        restored_state = self.load_known_good_snapshot(
            production_name=production_name,
            snapshot_id=snapshot_id,
        )

        if restored_state is None:
            raise ValueError(
                "Requested known-good production snapshot does not exist."
            )

        self.save_runtime_state(restored_state)

        return restored_state

    def upload_artifact_bytes(
        self,
        *,
        production_name: str,
        artifact_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        if not artifact_name.strip():
            raise ValueError(
                "Artifact name must not be empty."
            )

        bucket = self.storage_client.bucket(
            self.config.bucket_name
        )

        object_name = (
            f"productions/"
            f"{production_name.strip()}/"
            f"artifacts/"
            f"{artifact_name.strip()}"
        )

        blob = bucket.blob(object_name)

        blob.upload_from_string(
            data,
            content_type=content_type,
        )

        return f"gs://{self.config.bucket_name}/{object_name}"

    def production_exists(
        self,
        production_name: str,
    ) -> bool:
        return self._production_document(
            production_name
        ).get().exists

    def get_raw_production_document(
        self,
        production_name: str,
    ) -> dict[str, Any] | None:
        snapshot = self._production_document(
            production_name
        ).get()

        if not snapshot.exists:
            return None

        return snapshot.to_dict()
