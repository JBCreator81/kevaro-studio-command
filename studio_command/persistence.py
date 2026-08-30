from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from google.cloud import firestore
from google.cloud import storage

from .identity import canonical_production_name, require_production_identity
from .models import (
    FinalProductionPackage,
    GovernedProductionRuntimeState,
    CrewMember,
    ProductionAssetRegistry,
)
from fastapi.encoders import jsonable_encoder


_FIRESTORE_NESTED_LIST_MARKER = "_kevaro_nested_list"


def _firestore_encode(value, *, inside_list=False):
    """Convert JSON-safe values into Firestore-safe values.

    Firestore does not permit an array to directly contain another array.
    Nested lists are therefore wrapped in a map and restored on read.
    """
    if isinstance(value, dict):
        return {
            key: _firestore_encode(item, inside_list=False)
            for key, item in value.items()
        }

    if isinstance(value, list):
        encoded = [
            _firestore_encode(item, inside_list=True)
            for item in value
        ]

        if inside_list:
            return {_FIRESTORE_NESTED_LIST_MARKER: encoded}

        return encoded

    return value


def _firestore_decode(value):
    """Restore Kevaro nested-list wrappers after Firestore reads."""
    if isinstance(value, dict):
        if (
            set(value.keys()) == {_FIRESTORE_NESTED_LIST_MARKER}
            and isinstance(value[_FIRESTORE_NESTED_LIST_MARKER], list)
        ):
            return [
                _firestore_decode(item)
                for item in value[_FIRESTORE_NESTED_LIST_MARKER]
            ]

        return {
            key: _firestore_decode(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_firestore_decode(item) for item in value]

    return value



DEFAULT_PROJECT_ID = "kevaro-studio-command"
DEFAULT_BUCKET_NAME = "kevaro-studio-command-production-artifacts"
DEFAULT_PRODUCTIONS_COLLECTION = "productions"
DEFAULT_CREW_COLLECTION = "crew_members"


@dataclass(frozen=True)
class ProductionPersistenceConfig:
    project_id: str = DEFAULT_PROJECT_ID
    bucket_name: str = DEFAULT_BUCKET_NAME
    productions_collection: str = DEFAULT_PRODUCTIONS_COLLECTION
    crew_collection: str = DEFAULT_CREW_COLLECTION


def _runtime_identity(runtime_state: GovernedProductionRuntimeState) -> str:
    return require_production_identity(
        runtime_state.production_name,
        runtime_state.workflow_state.production_name,
        runtime_state.memory_snapshot.production_name,
        *(entry.production_name for entry in runtime_state.decision_history),
    )


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
        normalized_name = canonical_production_name(production_name)

        document_id = sha256(
            normalized_name.encode("utf-8")
        ).hexdigest()

        return (
            self.firestore_client
            .collection(self.config.productions_collection)
            .document(document_id)
        )

    def _crew_document(self, auth_subject: str):
        if not auth_subject.strip():
            raise ValueError("Authentication subject must not be empty.")
        document_id = sha256(auth_subject.encode("utf-8")).hexdigest()
        return self.firestore_client.collection(self.config.crew_collection).document(document_id)

    def save_crew_member(self, member: CrewMember) -> None:
        """Provision crew authorization; public sign-in never writes this record."""
        self._crew_document(member.auth_subject).set(
            _firestore_encode(jsonable_encoder(member.model_dump(mode="json")))
        )

    def load_crew_member(self, auth_subject: str) -> CrewMember | None:
        snapshot = self._crew_document(auth_subject).get()
        if not snapshot.exists:
            return None
        payload = snapshot.to_dict()
        if not isinstance(payload, dict):
            return None
        member = CrewMember.model_validate(_firestore_decode(payload))
        if member.auth_subject != auth_subject:
            raise ValueError("Persisted crew authentication subject is invalid.")
        return member

    def save_runtime_state(
        self,
        runtime_state: GovernedProductionRuntimeState,
    ) -> None:
        canonical_name = _runtime_identity(runtime_state)
        payload = _firestore_encode(
            runtime_state.model_dump(mode="json")
        )

        payload["production_name"] = canonical_name
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

    def save_final_package(
        self,
        final_package: FinalProductionPackage,
    ) -> None:
        payload = final_package.model_dump(mode="json")

        firestore_safe_final_package = _firestore_encode(
            jsonable_encoder(payload)
        )

        self._production_document(
            final_package.production_name
        ).set(
            {"final_package": firestore_safe_final_package},
            merge=True,
        )

    def load_final_package(
        self,
        production_name: str,
    ) -> FinalProductionPackage | None:
        snapshot = self._production_document(
            production_name
        ).get()

        if not snapshot.exists:
            return None

        payload = snapshot.to_dict()

        if payload is None:
            return None

        payload = _firestore_decode(payload)

        final_package_payload = payload.get("final_package")

        if final_package_payload is None:
            return None

        return FinalProductionPackage.model_validate(
            final_package_payload
        )

    def save_approved_artifacts(
        self,
        *,
        production_name: str,
        approved_artifacts: dict[str, Any],
    ) -> None:
        if not production_name.strip():
            raise ValueError("Production name must not be empty.")

        if not approved_artifacts:
            raise ValueError("Approved artifact bundle must not be empty.")

        firestore_safe_artifacts = _firestore_encode(
            jsonable_encoder(approved_artifacts)
        )

        self._production_document(
            production_name
        ).set(
            {"approved_artifacts": firestore_safe_artifacts},
            merge=True,
        )

    def load_approved_artifacts(
        self,
        production_name: str,
    ) -> dict[str, Any] | None:
        snapshot = self._production_document(
            production_name
        ).get()

        if not snapshot.exists:
            return None

        payload = snapshot.to_dict()

        if payload is None:
            return None

        approved_artifacts = payload.get("approved_artifacts")

        if not isinstance(approved_artifacts, dict):
            return None

        return _firestore_decode(approved_artifacts)

    def save_pending_review_bundle(
        self,
        *,
        production_name: str,
        review_bundle: dict[str, Any],
    ) -> None:
        if not review_bundle:
            raise ValueError("Pending Studio Head review bundle must not be empty.")

        required_keys = {
            "production_brief",
            "research_packet",
            "creative_treatment",
            "production_plan",
            "production_schedule",
            "asset_media_plan",
            "clearance_compliance_report",
            "verification_qa_report",
            "studio_head_decision_package",
        }

        missing = sorted(required_keys - set(review_bundle))

        if missing:
            raise ValueError(
                f"Pending Studio Head review bundle is incomplete: {missing}"
            )

        try:
            canonical_name = require_production_identity(
                production_name,
                review_bundle["production_plan"]["production_name"],
                review_bundle["production_schedule"]["production_name"],
                review_bundle["studio_head_decision_package"]["production_name"],
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(
                "Pending Studio Head review bundle has invalid production identity."
            ) from exc

        firestore_safe_review_bundle = _firestore_encode(
            jsonable_encoder(review_bundle)
        )

        self._production_document(
            canonical_name
        ).set(
            {
                "production_name": canonical_name,
                "pending_review_bundle": firestore_safe_review_bundle,
            },
            merge=True,
        )

    def load_pending_review_bundle(
        self,
        production_name: str,
    ) -> dict[str, Any] | None:
        snapshot = self._production_document(
            production_name
        ).get()

        if not snapshot.exists:
            return None

        payload = snapshot.to_dict()

        if payload is None:
            return None

        review_bundle = payload.get("pending_review_bundle")

        if not isinstance(review_bundle, dict):
            return None

        review_bundle = _firestore_decode(review_bundle)
        persisted_name = payload.get("production_name")

        try:
            identity_names = [
                review_bundle["production_plan"]["production_name"],
                review_bundle["production_schedule"]["production_name"],
                review_bundle["studio_head_decision_package"]["production_name"],
            ]
            if persisted_name is not None:
                identity_names.append(persisted_name)
            require_production_identity(production_name, *identity_names)
        except (KeyError, TypeError) as exc:
            raise ValueError(
                "Pending Studio Head review bundle has invalid production identity."
            ) from exc

        return review_bundle

    def load_pending_decision_package(
        self,
        production_name: str,
    ) -> dict[str, Any] | None:
        review_bundle = self.load_pending_review_bundle(
            production_name
        )

        if review_bundle is None:
            return None

        pending_package = review_bundle.get(
            "studio_head_decision_package"
        )

        if not isinstance(pending_package, dict):
            return None

        return pending_package

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

        required_runtime_fields = {
            "production_name",
            "workflow_state",
            "decision_history",
            "memory_snapshot",
            "execution_authorized",
            "corrective_cycle_active",
            "current_stage",
        }

        if not required_runtime_fields.issubset(payload):
            return None

        runtime_state = GovernedProductionRuntimeState.model_validate(
            payload
        )
        require_production_identity(
            production_name,
            _runtime_identity(runtime_state),
        )
        return runtime_state

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

    def save_asset_registry(self, registry: ProductionAssetRegistry) -> None:
        canonical_name = require_production_identity(registry.production_identity)
        payload = _firestore_encode(
            jsonable_encoder(registry.model_dump(mode="json"))
        )
        self._production_document(canonical_name).set(
            {"production_asset_registry": payload}, merge=True,
        )

    def load_asset_registry(
        self, production_name: str,
    ) -> ProductionAssetRegistry | None:
        snapshot = self._production_document(production_name).get()
        if not snapshot.exists:
            return None
        payload = snapshot.to_dict() or {}
        raw = payload.get("production_asset_registry")
        if not isinstance(raw, dict):
            return None
        registry = ProductionAssetRegistry.model_validate(
            _firestore_decode(raw)
        )
        require_production_identity(
            production_name, registry.production_identity,
        )
        return registry

    def upload_production_asset_bytes(
        self,
        *,
        production_name: str,
        asset_id: str,
        version_number: int,
        filename: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload to a server-derived object key, never a client path."""
        canonical_name = require_production_identity(production_name)
        if not asset_id.startswith("asset-") or not asset_id[6:].isalnum():
            raise ValueError("Asset ID is not valid for storage.")
        if version_number < 1:
            raise ValueError("Asset version must be positive.")
        from .assets import safe_filename
        safe_name = safe_filename(filename)
        production_key = sha256(canonical_name.encode("utf-8")).hexdigest()
        object_name = (
            f"productions/{production_key}/production-assets/{asset_id}/"
            f"v{version_number}/{safe_name}"
        )
        blob = self.storage_client.bucket(self.config.bucket_name).blob(object_name)
        blob.upload_from_string(data, content_type=content_type)
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
