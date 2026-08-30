from __future__ import annotations

from datetime import datetime, timezone
from pathlib import PurePath
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from .access import require_access
from .identity import require_production_identity
from .models import (
    AccountabilityAction,
    AccountabilityActor,
    AccountabilityMetadata,
    AssetComment,
    AssetHandoff,
    AssetReviewRecord,
    AssetStorageReference,
    ProductionAsset,
    ProductionAssetRegistry,
)


_SENSITIVE_METADATA_KEYS = {
    "api_key", "apikey", "authorization", "cookie", "credential",
    "credentials", "password", "secret", "token",
}


def validate_secret_safe_metadata(value: Any, *, field_name: str) -> None:
    """Reject secret-shaped metadata before it reaches governed persistence."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().casefold().replace("-", "_")
            if normalized in _SENSITIVE_METADATA_KEYS or any(
                normalized.endswith(f"_{suffix}")
                for suffix in ("password", "secret", "token")
            ):
                raise ValueError(
                    f"{field_name} must not contain secret or token material."
                )
            validate_secret_safe_metadata(item, field_name=field_name)
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_secret_safe_metadata(item, field_name=field_name)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def validate_storage_reference(storage: AssetStorageReference) -> None:
    reference = storage.reference.strip()
    if not reference or "\x00" in reference:
        raise ValueError("Asset storage reference must not be empty.")
    parsed = urlsplit(reference)
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Asset storage reference must not contain secrets or query tokens.")
    if storage.location_type == "GCS_URI" and (
        parsed.scheme != "gs" or not parsed.netloc or not parsed.path.strip("/")
    ):
        raise ValueError("GCS asset references must be canonical gs:// object URIs.")
    if storage.location_type == "REGISTERED_URI" and parsed.scheme not in {
        "https", "gs"
    }:
        raise ValueError("Registered asset URIs must use https:// or gs://.")
    if storage.location_type == "EXTERNAL_REFERENCE" and (
        reference.startswith(("/", "\\", "."))
        or parsed.scheme == "file"
        or (len(reference) > 1 and reference[1] == ":")
    ):
        raise ValueError("External asset references cannot be filesystem paths.")


def safe_filename(filename: str) -> str:
    name = PurePath(filename.strip()).name
    if not name or name in {".", ".."} or "\x00" in name:
        raise ValueError("Asset filename must be a safe basename.")
    cleaned = "".join(
        character if character.isalnum() or character in "._-" else "-"
        for character in name
    ).strip(".-")
    if not cleaned:
        raise ValueError("Asset filename must contain a safe basename.")
    return cleaned[:180]


def _validate_ingress_storage(persistence: Any, storage: AssetStorageReference) -> None:
    validate_storage_reference(storage)
    configured_bucket = getattr(getattr(persistence, "config", None), "bucket_name", None)
    if storage.location_type == "GCS_URI" and configured_bucket:
        if urlsplit(storage.reference).netloc != configured_bucket:
            raise ValueError("GCS asset reference must use the configured production bucket.")


def _registry(persistence: Any, production_name: str) -> ProductionAssetRegistry:
    loaded = persistence.load_asset_registry(production_name)
    if loaded is None:
        return ProductionAssetRegistry(production_identity=production_name)
    require_production_identity(production_name, loaded.production_identity)
    return loaded


def _versions(registry: ProductionAssetRegistry, asset_id: str) -> list[ProductionAsset]:
    versions = [item for item in registry.assets if item.asset_id == asset_id]
    return sorted(versions, key=lambda item: item.version_number)


def latest_asset(registry: ProductionAssetRegistry, asset_id: str) -> ProductionAsset:
    versions = _versions(registry, asset_id)
    if not versions:
        raise ValueError("Production asset was not found.")
    return versions[-1]


def register_asset(
    *,
    persistence: Any,
    production_name: str,
    node_id: str,
    actor: AccountabilityActor,
    node_accountability: AccountabilityMetadata,
    asset_category: str,
    filename: str,
    display_name: str,
    media_document_type: str,
    storage: AssetStorageReference,
    task_id: str | None = None,
    external_source_tool: str | None = None,
    provenance: dict[str, Any] | None = None,
    expected_deliverable: str | None = None,
    acceptance_criteria: list[str] | None = None,
    preview_metadata: dict[str, Any] | None = None,
    clearance_state: str | None = None,
    asset_id: str | None = None,
) -> ProductionAsset:
    production_name = require_production_identity(production_name)
    if not node_id.strip():
        raise ValueError("Asset node association is required.")
    require_access(
        actor=actor, action="EDIT", accountability=node_accountability,
        scope=task_id, status=node_accountability.current_status,
    )
    _validate_ingress_storage(persistence, storage)
    validate_secret_safe_metadata(provenance or {}, field_name="Asset provenance")
    validate_secret_safe_metadata(
        preview_metadata or {}, field_name="Asset preview metadata"
    )
    filename = safe_filename(filename)
    if not display_name.strip() or not media_document_type.strip():
        raise ValueError("Asset display name and media/document type are required.")
    registry = _registry(persistence, production_name)
    stable_id = asset_id or f"asset-{uuid4().hex}"
    if _versions(registry, stable_id):
        raise ValueError("Existing asset IDs require creation of a new version.")
    timestamp = _now()
    accountability = node_accountability.model_copy(deep=True)
    accountability.last_changed_by = actor
    accountability.created_at = timestamp
    accountability.last_changed_at = timestamp
    accountability.current_status = "REGISTERED"
    accountability.action_history.append(AccountabilityAction(
        action="ASSET_REGISTERED", actor=actor, timestamp=timestamp,
        status="REGISTERED", details=f"Registered {filename} at {node_id}.",
    ))
    asset = ProductionAsset(
        asset_id=stable_id, version_id=f"{stable_id}:v1",
        production_identity=production_name, node_id=node_id, task_id=task_id,
        asset_category=asset_category, filename=filename,
        display_name=display_name.strip(),
        media_document_type=media_document_type.strip(), storage=storage,
        external_source_tool=external_source_tool, version_number=1,
        created_at=timestamp, last_changed_at=timestamp,
        clearance_state=clearance_state, provenance=provenance or {},
        expected_deliverable=expected_deliverable,
        acceptance_criteria=acceptance_criteria or [],
        preview_metadata=preview_metadata or {}, accountability=accountability,
    )
    registry.assets.append(asset)
    persistence.save_asset_registry(registry)
    return asset


def create_asset_version(
    *, persistence: Any, production_name: str, asset_id: str,
    actor: AccountabilityActor, storage: AssetStorageReference, filename: str,
    provenance: dict[str, Any] | None = None,
    external_source_tool: str | None = None,
    preview_metadata: dict[str, Any] | None = None,
    status: str = "REGISTERED",
) -> ProductionAsset:
    production_name = require_production_identity(production_name)
    registry = _registry(persistence, production_name)
    prior = latest_asset(registry, asset_id)
    require_production_identity(production_name, prior.production_identity)
    require_access(
        actor=actor, action="EDIT", accountability=prior.accountability,
        status=prior.status,
    )
    _validate_ingress_storage(persistence, storage)
    validate_secret_safe_metadata(provenance or {}, field_name="Asset provenance")
    validate_secret_safe_metadata(
        preview_metadata or {}, field_name="Asset preview metadata"
    )
    timestamp = _now()
    version_number = prior.version_number + 1
    accountability = prior.accountability.model_copy(deep=True)
    accountability.last_changed_by = actor
    accountability.last_changed_at = timestamp
    accountability.current_status = status
    accountability.action_history.append(AccountabilityAction(
        action="ASSET_VERSION_CREATED", actor=actor, timestamp=timestamp,
        status=status, details=f"Created version {version_number} from {prior.version_id}.",
    ))
    version = prior.model_copy(deep=True, update={
        "version_id": f"{asset_id}:v{version_number}",
        "version_number": version_number,
        "parent_version_id": prior.version_id,
        "filename": safe_filename(filename), "storage": storage,
        "external_source_tool": external_source_tool,
        "created_at": timestamp, "last_changed_at": timestamp,
        "status": status, "review_state": "NOT_SUBMITTED",
        "provenance": provenance or {}, "preview_metadata": preview_metadata or {},
        "comments": [], "reviews": [], "handoffs": [],
        "accountability": accountability,
    })
    registry.assets.append(version)
    persistence.save_asset_registry(registry)
    return version


def handoff_asset(
    *, persistence: Any, production_name: str, asset_id: str,
    actor: AccountabilityActor, target_tool: str, brief: str,
    requirements: list[str], evidence_context: list[str], due_date: str | None,
    approval_context: str | None, expected_deliverable: str,
) -> AssetHandoff:
    registry = _registry(persistence, require_production_identity(production_name))
    asset = latest_asset(registry, asset_id)
    require_access(actor=actor, action="EDIT", accountability=asset.accountability,
                   status=asset.status)
    if not target_tool.strip() or not brief.strip() or not expected_deliverable.strip():
        raise ValueError("Handoff target, brief, and expected deliverable are required.")
    timestamp = _now()
    handoff = AssetHandoff(
        handoff_id=f"handoff-{uuid4().hex}", target_tool=target_tool.strip(),
        brief=brief.strip(), requirements=requirements,
        evidence_context=evidence_context,
        owner=asset.accountability.human_owner or actor, due_date=due_date,
        approval_context=approval_context,
        expected_deliverable=expected_deliverable.strip(), handed_off_by=actor,
        handed_off_at=timestamp, status="WAITING_FOR_RETURN",
        base_version_id=asset.version_id,
    )
    asset.handoffs.append(handoff)
    asset.status = "EXTERNAL_HANDOFF"
    asset.last_changed_at = timestamp
    asset.accountability.last_changed_by = actor
    asset.accountability.last_changed_at = timestamp
    asset.accountability.current_status = asset.status
    asset.accountability.action_history.append(AccountabilityAction(
        action="ASSET_HANDOFF", actor=actor, timestamp=timestamp,
        status=asset.status, details=f"Handed off to {target_tool.strip()}.",
    ))
    persistence.save_asset_registry(registry)
    return handoff


def reconcile_external_return(
    *, persistence: Any, production_name: str, asset_id: str,
    handoff_id: str, base_version_id: str, node_id: str,
    actor: AccountabilityActor, storage: AssetStorageReference, filename: str,
    return_metadata: dict[str, Any] | None = None,
) -> ProductionAsset:
    validate_secret_safe_metadata(
        return_metadata or {}, field_name="Handoff return metadata"
    )
    production_name = require_production_identity(production_name)
    registry = _registry(persistence, production_name)
    base = latest_asset(registry, asset_id)
    if base.production_identity != production_name or base.node_id != node_id:
        raise ValueError("External return does not match its production and node.")
    handoff = next((item for item in base.handoffs if item.handoff_id == handoff_id), None)
    if handoff is None or handoff.status != "WAITING_FOR_RETURN":
        raise ValueError("External return does not match an open handoff.")
    if handoff.base_version_id != base_version_id or base.version_id != base_version_id:
        raise ValueError("External return does not match the current handed-off version.")
    returned = create_asset_version(
        persistence=persistence, production_name=production_name,
        asset_id=asset_id, actor=actor, storage=storage, filename=filename,
        external_source_tool=handoff.target_tool,
        provenance={"handoff_id": handoff_id, "base_version_id": base_version_id},
        status="RETURNED_PENDING_REVIEW",
    )
    registry = _registry(persistence, production_name)
    original = next(item for item in registry.assets if item.version_id == base_version_id)
    persisted_return = next(
        item for item in registry.assets if item.version_id == returned.version_id
    )
    persisted_handoff = next(item for item in original.handoffs if item.handoff_id == handoff_id)
    timestamp = _now()
    persisted_handoff.status = "RETURNED"
    persisted_handoff.returned_version_id = returned.version_id
    persisted_handoff.returned_at = timestamp
    persisted_handoff.return_metadata = return_metadata or {}
    persisted_return.review_state = "PENDING_REVIEW"
    persistence.save_asset_registry(registry)
    return persisted_return


def review_asset(
    *, persistence: Any, production_name: str, asset_id: str,
    version_id: str, actor: AccountabilityActor, decision: str,
    notes: str | None = None, annotations: list[dict[str, Any]] | None = None,
    comparison_version_id: str | None = None,
) -> ProductionAsset:
    registry = _registry(persistence, require_production_identity(production_name))
    asset = latest_asset(registry, asset_id)
    if asset.version_id != version_id:
        raise ValueError("Review must target the current asset version.")
    normalized = decision.strip().upper()
    if normalized not in {"COMMENT", "REQUEST_CHANGES", "APPROVE"}:
        raise ValueError("Asset review decision is invalid.")
    require_access(
        actor=actor, action="APPROVE" if normalized == "APPROVE" else "REVIEW",
        accountability=asset.accountability, status=asset.status,
    )
    if comparison_version_id and not any(
        item.version_id == comparison_version_id and item.asset_id == asset_id
        for item in registry.assets
    ):
        raise ValueError("Comparison version is outside this asset lineage.")
    timestamp = _now()
    asset.reviews.append(AssetReviewRecord(
        reviewer=actor, decision=normalized, timestamp=timestamp, notes=notes,
        annotations=annotations or [], comparison_version_id=comparison_version_id,
    ))
    if notes:
        asset.comments.append(AssetComment(
            comment_id=f"comment-{uuid4().hex}", author=actor, body=notes,
            created_at=timestamp,
            annotation={"items": annotations or []},
        ))
    asset.review_state = {
        "COMMENT": "PENDING_REVIEW", "REQUEST_CHANGES": "CHANGES_REQUESTED",
        "APPROVE": "APPROVED",
    }[normalized]
    asset.status = {
        "COMMENT": "PENDING_REVIEW", "REQUEST_CHANGES": "REVISION_REQUESTED",
        "APPROVE": "APPROVED",
    }[normalized]
    asset.last_changed_at = timestamp
    asset.accountability.last_changed_by = actor
    asset.accountability.last_changed_at = timestamp
    asset.accountability.current_status = asset.status
    if normalized == "APPROVE":
        asset.accountability.approved_by = actor
    asset.accountability.action_history.append(AccountabilityAction(
        action=f"ASSET_REVIEW_{normalized}", actor=actor, timestamp=timestamp,
        status=asset.status, details=notes,
    ))
    persistence.save_asset_registry(registry)
    return asset


def submit_asset_for_review(
    *, persistence: Any, production_name: str, asset_id: str,
    version_id: str, actor: AccountabilityActor,
) -> ProductionAsset:
    registry = _registry(persistence, require_production_identity(production_name))
    asset = latest_asset(registry, asset_id)
    if asset.version_id != version_id:
        raise ValueError("Review submission must target the current asset version.")
    require_access(
        actor=actor, action="EDIT", accountability=asset.accountability,
        status=asset.status,
    )
    timestamp = _now()
    asset.review_state = "PENDING_REVIEW"
    asset.status = "PENDING_REVIEW"
    asset.last_changed_at = timestamp
    asset.accountability.last_changed_by = actor
    asset.accountability.last_changed_at = timestamp
    asset.accountability.current_status = asset.status
    asset.accountability.action_history.append(AccountabilityAction(
        action="ASSET_SUBMITTED_FOR_REVIEW", actor=actor,
        timestamp=timestamp, status=asset.status,
    ))
    persistence.save_asset_registry(registry)
    return asset


def asset_snapshot(
    registry: ProductionAssetRegistry | None,
    required_deliverables: list[str] | None = None,
) -> dict[str, Any]:
    assets = registry.assets if registry else []
    grouped: dict[str, list[ProductionAsset]] = {}
    for asset in assets:
        grouped.setdefault(asset.asset_id, []).append(asset)
    summaries = []
    for asset_id, versions in grouped.items():
        versions.sort(key=lambda item: item.version_number)
        latest = versions[-1]
        open_handoff = next(
            (item for item in reversed(latest.handoffs)
             if item.status == "WAITING_FOR_RETURN"), None
        )
        summaries.append({
            "asset_id": asset_id, "node_id": latest.node_id,
            "task_id": latest.task_id, "display_name": latest.display_name,
            "asset_category": latest.asset_category,
            "latest_version": latest.model_dump(mode="json"),
            "version_count": len(versions),
            "version_history": [{
                "version_id": item.version_id,
                "version_number": item.version_number,
                "parent_version_id": item.parent_version_id,
                "changed_by": (
                    item.accountability.last_changed_by.model_dump(mode="json")
                    if item.accountability and item.accountability.last_changed_by else None
                ),
                "created_at": item.created_at.isoformat(),
                "status": item.status, "review_state": item.review_state,
            } for item in versions],
            "owner": (
                latest.accountability.human_owner.model_dump(mode="json")
                if latest.accountability and latest.accountability.human_owner else None
            ),
            "review_state": latest.review_state,
            "handoff_state": open_handoff.status if open_handoff else "NONE",
        })
    actions = []
    for item in summaries:
        latest = item["latest_version"]
        if item["handoff_state"] == "WAITING_FOR_RETURN":
            action = "WAIT_FOR_EXTERNAL_RETURN"
        elif item["review_state"] == "CHANGES_REQUESTED":
            action = "CREATE_REQUESTED_REVISION"
        elif item["review_state"] == "PENDING_REVIEW":
            action = "REVIEW_ASSET"
        elif item["review_state"] == "NOT_SUBMITTED":
            action = "SUBMIT_ASSET_FOR_REVIEW"
        else:
            continue
        actions.append({"asset_id": item["asset_id"], "node_id": item["node_id"],
                        "action_type": action, "status": latest["status"]})
    registered_names = {
        item["display_name"].strip().casefold() for item in summaries
    }
    missing = [
        name for name in (required_deliverables or [])
        if name.strip().casefold() not in registered_names
    ]
    if missing:
        actions.insert(0, {
            "asset_id": None, "node_id": "Asset & Media",
            "action_type": "REGISTER_MISSING_ASSET",
            "missing_deliverables": missing,
        })
    return {
        "assets": summaries, "asset_count": len(summaries),
        "approved_asset_count": sum(
            item["review_state"] == "APPROVED" for item in summaries
        ),
        "missing_deliverables": missing,
        "next_required_asset_action": actions[0] if actions else None,
        "asset_actions": actions,
    }


def approved_asset_references(registry: ProductionAssetRegistry | None) -> list[dict[str, Any]]:
    snapshot = asset_snapshot(registry)
    return [{
        "asset_id": item["asset_id"],
        "version_id": item["latest_version"]["version_id"],
        "node_id": item["node_id"], "display_name": item["display_name"],
        "storage": item["latest_version"]["storage"],
        "review_state": item["review_state"],
    } for item in snapshot["assets"] if item["review_state"] == "APPROVED"]
