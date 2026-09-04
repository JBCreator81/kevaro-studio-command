from __future__ import annotations

import hmac
import base64
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from studio_command.access import AuthorizationDenied, require_access
from studio_command.auth import (SESSION_COOKIE, SessionError, issue_session, resolve_crew_identity, verify_session)
from studio_command.accountability import human_actor
from studio_command.accountability import ai_actor
from studio_command.assets import (
    approved_asset_references,
    asset_snapshot,
    create_asset_version,
    handoff_asset,
    latest_asset,
    reconcile_external_return,
    register_asset,
    review_asset,
    submit_asset_for_review,
)
from studio_command.exporter import complete_governed_delivery
from studio_command.decisions import (
    build_production_execution_authorization,
    finalize_production_package,
)
from studio_command.models import (
    AssetMediaPlan,
    ClearanceComplianceReport,
    CreativeTreatment,
    ProductionBrief,
    ProductionPlan,
    ProductionSchedule,
    ResearchPacket,
    VerificationQAReport,
    AssetStorageReference,
)
from studio_command.persistence import ProductionPersistence
from studio_command.decisions import approve_governed_production
from studio_command.models import StudioHeadDecisionPackage
from studio_command.identity import canonical_production_name
from studio_command.runtime_config import SecretConfigurationError, load_runtime_config

SERVICE_NAME = os.getenv("K_SERVICE", "kevaro-studio-command")
REVISION = os.getenv("K_REVISION", "local")
STARTED_AT = time.time()

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = ROOT / "frontend" / "dist"
SNAPSHOT_PATH = FRONTEND_DIST / "studio-snapshot.json"

app = FastAPI(
    title="Kevaro Studio Command",
    version="23.0",
)

production_persistence = ProductionPersistence()

PROTECTED_MUTATION_SUFFIXES = ("/decision", "/finalize", "/deliver")
ALLOWED_ASSET_CONTENT_TYPES = {
    "application/msword",
    "application/pdf",
    "application/rtf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "text/markdown",
    "text/plain",
}
ALLOWED_ASSET_CONTENT_PREFIXES = ("audio/", "image/", "video/")


class AssetRegistrationRequest(BaseModel):
    node_id: str
    task_id: str | None = None
    asset_category: str
    filename: str
    display_name: str
    media_document_type: str
    storage: AssetStorageReference | None = None
    content_base64: str | None = None
    content_type: str = "application/octet-stream"
    external_source_tool: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    expected_deliverable: str | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    preview_metadata: dict[str, Any] = Field(default_factory=dict)
    clearance_state: str | None = None


class AssetVersionRequest(BaseModel):
    filename: str
    storage: AssetStorageReference | None = None
    content_base64: str | None = None
    content_type: str = "application/octet-stream"
    external_source_tool: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    preview_metadata: dict[str, Any] = Field(default_factory=dict)


class AssetHandoffRequest(BaseModel):
    target_tool: str
    brief: str
    requirements: list[str] = Field(default_factory=list)
    evidence_context: list[str] = Field(default_factory=list)
    due_date: str | None = None
    approval_context: str | None = None
    expected_deliverable: str


class AssetReturnRequest(BaseModel):
    handoff_id: str
    base_version_id: str
    node_id: str
    filename: str
    storage: AssetStorageReference | None = None
    content_base64: str | None = None
    content_type: str = "application/octet-stream"
    return_metadata: dict[str, Any] = Field(default_factory=dict)


class AssetReviewRequest(BaseModel):
    version_id: str
    decision: str
    notes: str | None = None
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    comparison_version_id: str | None = None


class StudioHeadDecisionRequest(BaseModel):
    decision: str
    conditions: list[str] = Field(default_factory=list)
    decision_notes: str = ""
    unresolved_risks_acknowledged: list[str] = Field(default_factory=list)


def _requires_crew_session(request: Request) -> bool:
    path = request.url.path
    if path == "/api/reality-shift":
        return request.method == "POST"
    return path.startswith("/api/productions/") and (
        request.method == "GET" or request.method == "POST"
    )


def _boundary_denial(status_code: int, reason_code: str, reason: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": {
        "error": "ACCESS_DENIED", "allowed": False,
        "reason_code": reason_code, "reason": reason,
    }})


@app.middleware("http")
async def require_authenticated_crew_session(request: Request, call_next):
    """Resolve browser identity only from a signed HttpOnly session."""
    if not _requires_crew_session(request):
        return await call_next(request)
    config = getattr(request.app.state, "runtime_config", None)
    if config is None:
        try:
            config = load_runtime_config()
        except SecretConfigurationError:
            return _boundary_denial(503, "AUTH_CONFIGURATION_UNAVAILABLE", "Authentication is unavailable.")
    secret = config.session_signing_secret or ""
    if not secret:
        return _boundary_denial(503, "AUTH_CONFIGURATION_UNAVAILABLE", "Crew session authentication is not configured.")
    token = request.cookies.get(SESSION_COOKIE, "")
    if not token:
        return _boundary_denial(401, "AUTHENTICATED_SESSION_REQUIRED", "Sign in with an assigned crew account.")
    try:
        request.state.auth_subject = verify_session(token, secret)
    except SessionError:
        return _boundary_denial(401, "INVALID_AUTHENTICATED_SESSION", "The crew session is invalid or expired.")
    return await call_next(request)


def _crew_identity(request: Request, production_name: str):
    config = getattr(request.app.state, "runtime_config", None) or load_runtime_config()
    try:
        return resolve_crew_identity(
            token=request.cookies.get(SESSION_COOKIE, ""),
            secret=config.session_signing_secret or "",
            persistence=production_persistence, production_name=production_name,
        )
    except SessionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _asset_actor(name: str, role: str, actor_type: str):
    if actor_type.strip().upper() == "AI_AGENT":
        return ai_actor(name, role)
    if actor_type.strip().upper() != "HUMAN":
        raise HTTPException(status_code=422, detail="actor_type must be HUMAN or AI_AGENT.")
    return human_actor(name, role)


def _load_asset_graph(production_name: str):
    from studio_command.graph import build_production_graph
    bundle = production_persistence.load_pending_review_bundle(production_name)
    if bundle is None:
        bundle = production_persistence.load_approved_artifacts(production_name)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Production was not found.")
    try:
        return build_production_graph(
            production_plan=ProductionPlan.model_validate(bundle["production_plan"]),
            production_schedule=ProductionSchedule.model_validate(bundle["production_schedule"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail="Production graph is invalid.") from exc


def _asset_node(production_name: str, node_id: str):
    graph = _load_asset_graph(production_name)
    node = next((item for item in graph.nodes if item.node_id == node_id), None)
    if node is None:
        raise HTTPException(status_code=409, detail="Asset node does not belong to production.")
    return node


def _decode_asset_content(content: str | None) -> bytes | None:
    if content is None:
        return None
    try:
        data = base64.b64decode(content, validate=True)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="Asset content_base64 is invalid.") from exc
    maximum = int(os.getenv("KEVARO_MAX_ASSET_UPLOAD_BYTES", str(100 * 1024 * 1024)))
    if len(data) > maximum:
        raise HTTPException(status_code=413, detail="Asset upload exceeds the configured limit.")
    return data


def _validated_asset_content_type(content_type: str) -> str:
    normalized = content_type.strip().casefold()
    if normalized == "image/svg+xml" or not (
        normalized in ALLOWED_ASSET_CONTENT_TYPES
        or normalized.startswith(ALLOWED_ASSET_CONTENT_PREFIXES)
    ):
        raise HTTPException(
            status_code=415, detail="Asset content type is not supported."
        )
    return normalized


def _asset_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AuthorizationDenied):
        return HTTPException(status_code=403, detail=exc.as_detail())
    return HTTPException(status_code=409, detail=str(exc))


def log_event(
    message: str,
    *,
    severity: str = "INFO",
    **fields: Any,
) -> None:
    print(
        json.dumps(
            {
                "severity": severity,
                "message": message,
                "service": SERVICE_NAME,
                "revision": REVISION,
                **fields,
            }
        ),
        flush=True,
    )


class SignInRequest(BaseModel):
    credential: str


class LocalSignInRequest(BaseModel):
    auth_subject: str


def _set_session_cookie(response: Response, token: str, *, secure: bool) -> None:
    response.set_cookie(SESSION_COOKIE, token, max_age=8 * 60 * 60, httponly=True, secure=secure, samesite="lax", path="/")


@app.get("/api/auth/config")
def auth_config() -> dict[str, Any]:
    config = getattr(app.state, "runtime_config", None) or load_runtime_config()
    return {
        "provider": "google" if config.deployed else "local",
        "google_client_id": config.google_auth_client_id if config.deployed else None,
        "local_auth_enabled": bool(config.local_auth_enabled and not config.deployed),
    }


@app.post("/api/auth/google")
def google_sign_in(request: SignInRequest, response: Response) -> dict[str, Any]:
    config = getattr(app.state, "runtime_config", None) or load_runtime_config()
    if not config.deployed or not config.google_auth_client_id or not config.session_signing_secret:
        raise HTTPException(status_code=503, detail="Google crew sign-in is not configured.")
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token
        claims = id_token.verify_oauth2_token(request.credential, GoogleRequest(), config.google_auth_client_id)
        subject = claims["sub"]
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Google identity credential is invalid.") from exc
    member = production_persistence.load_crew_member(subject)
    if member is None or not member.active:
        raise HTTPException(status_code=403, detail="Google account is not assigned to active crew.")
    _set_session_cookie(response, issue_session(subject, config.session_signing_secret), secure=True)
    return {"signed_in": True, "display_name": member.display_name}


@app.post("/api/auth/local")
def local_sign_in(request: LocalSignInRequest, response: Response) -> dict[str, Any]:
    config = getattr(app.state, "runtime_config", None) or load_runtime_config()
    if config.deployed or not config.local_auth_enabled:
        raise HTTPException(status_code=404, detail="Local authentication is disabled.")
    if not config.session_signing_secret:
        raise HTTPException(status_code=503, detail="Local session signing is not configured.")
    member = production_persistence.load_crew_member(request.auth_subject)
    if member is None or not member.active:
        raise HTTPException(status_code=403, detail="Local identity is not assigned to active crew.")
    _set_session_cookie(response, issue_session(request.auth_subject, config.session_signing_secret), secure=False)
    return {"signed_in": True, "display_name": member.display_name}


@app.post("/api/auth/sign-out")
def sign_out(response: Response) -> dict[str, bool]:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax")
    return {"signed_in": False}


@app.get("/api/auth/session")
def current_session(request: Request, production_name: str) -> dict[str, Any]:
    return {"signed_in": True, "crew": _crew_identity(request, production_name).public_dict()}


@app.on_event("startup")
async def startup_event() -> None:
    try:
        app.state.runtime_config = load_runtime_config()
    except SecretConfigurationError as exc:
        log_event(
            "Kevaro deployed secret configuration failed",
            severity="CRITICAL", error_type=type(exc).__name__,
        )
        raise RuntimeError(
            "Kevaro cannot start without required deployed secret configuration."
        ) from exc
    log_event(
        "Kevaro Studio Command service started",
        frontend_available=FRONTEND_DIST.exists(),
        snapshot_available=SNAPSHOT_PATH.exists(),
        runtime_configuration=app.state.runtime_config.public_status(),
    )


@app.get("/health")
def health() -> dict[str, Any]:
    config = getattr(app.state, "runtime_config", None) or load_runtime_config()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "revision": REVISION,
        "uptime_seconds": round(time.time() - STARTED_AT, 2),
        "runtime_configuration": config.public_status(),
    }


@app.get("/ready")
def ready() -> dict[str, Any]:
    frontend_ready = FRONTEND_DIST.exists()
    snapshot_ready = SNAPSHOT_PATH.exists()

    if not frontend_ready or not snapshot_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "frontend_ready": frontend_ready,
                "snapshot_ready": snapshot_ready,
            },
        )

    return {
        "status": "ready",
        "frontend_ready": True,
        "snapshot_ready": True,
    }


@app.get("/api/studio-snapshot")
def studio_snapshot() -> Any:
    try:
        select_current = getattr(
            production_persistence, "current_governed_production_name", None
        )
        production_name = select_current() if select_current is not None else None
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=409,
            detail="Current governed production identity is invalid.",
        ) from exc

    if production_name is not None:
        return {
            "production_name": production_name,
            "bootstrap_source": "GOVERNED_RUNTIME",
        }

    if not SNAPSHOT_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Studio Command snapshot is unavailable.",
        )

    snapshot = json.loads(SNAPSHOT_PATH.read_text())
    canonical_production_name(snapshot["production_name"])
    snapshot["bootstrap_source"] = "STATIC_FALLBACK"
    return snapshot


@app.get("/api/productions/{production_name}/studio-snapshot")
def live_studio_snapshot(
    production_name: str, request: Request = None, guidance_level: str = "Standard",
) -> Any:
    """Build UI state from pending review or the governed runtime."""
    from studio_command.graph import build_production_graph
    from studio_command.ui_snapshot import (
        build_pending_studio_command_snapshot,
        build_studio_command_snapshot,
    )

    canonical_name = canonical_production_name(production_name)
    actor = (_crew_identity(request, canonical_name).actor if request is not None else human_actor("Studio Head", "Studio Head"))
    runtime_state = production_persistence.load_runtime_state(canonical_name)
    load_registry = getattr(production_persistence, "load_asset_registry", None)
    asset_registry = load_registry(canonical_name) if load_registry else None

    if runtime_state is None:
        try:
            review_bundle = production_persistence.load_pending_review_bundle(
                canonical_name
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        if review_bundle is None:
            raise HTTPException(
                status_code=404,
                detail="Production was not found.",
            )

        try:
            production_plan = ProductionPlan.model_validate(
                review_bundle["production_plan"]
            )
            production_schedule = ProductionSchedule.model_validate(
                review_bundle["production_schedule"]
            )
            graph_state = build_production_graph(
                production_plan=production_plan,
                production_schedule=production_schedule,
            )
            return build_pending_studio_command_snapshot(
                production_name=canonical_name,
                graph_state=graph_state,
                review_bundle=review_bundle,
                actor=actor,
                guidance_level=guidance_level,
                asset_registry=asset_registry,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=409,
                detail="Pending production state is invalid for Studio Command.",
            ) from exc

    approved_artifacts = production_persistence.load_approved_artifacts(
        canonical_name
    )

    if approved_artifacts is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Governed approved production artifacts are not available "
                "for Studio Command."
            ),
        )

    try:
        production_plan = ProductionPlan.model_validate(
            approved_artifacts["production_plan"]
        )
        production_schedule = ProductionSchedule.model_validate(
            approved_artifacts["production_schedule"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "Approved production state does not contain a valid "
                "production plan and schedule."
            ),
        ) from exc

    graph_state = build_production_graph(
        production_plan=production_plan,
        production_schedule=production_schedule,
    )
    final_package = production_persistence.load_final_package(canonical_name)

    return build_studio_command_snapshot(
        runtime_state=runtime_state,
        graph_state=graph_state,
        final_package=final_package,
        approved_artifacts=approved_artifacts,
        actor=actor,
        guidance_level=guidance_level,
        asset_registry=asset_registry,
    )


@app.get("/api/productions/{production_name}/assets")
def list_production_assets(production_name: str, request: Request) -> dict[str, Any]:
    canonical_name = canonical_production_name(production_name)
    _crew_identity(request, canonical_name)
    if not production_persistence.production_exists(canonical_name):
        raise HTTPException(status_code=404, detail="Production was not found.")
    return asset_snapshot(production_persistence.load_asset_registry(canonical_name))


def _resolved_storage(
    *, production_name: str, asset_id: str, version_number: int,
    filename: str, storage: AssetStorageReference | None,
    content_base64: str | None, content_type: str,
) -> AssetStorageReference:
    data = _decode_asset_content(content_base64)
    if (storage is None) == (data is None):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of storage or content_base64.",
        )
    if storage is not None:
        return storage
    content_type = _validated_asset_content_type(content_type)
    uri = production_persistence.upload_production_asset_bytes(
        production_name=production_name, asset_id=asset_id,
        version_number=version_number, filename=filename, data=data,
        content_type=content_type,
    )
    return AssetStorageReference(
        location_type="GCS_URI", reference=uri, content_type=content_type,
        size_bytes=len(data), checksum_sha256=hashlib.sha256(data).hexdigest(),
    )


@app.post("/api/productions/{production_name}/assets/register")
def register_production_asset(
    production_name: str, request: AssetRegistrationRequest, http_request: Request,
) -> dict[str, Any]:
    canonical_name = canonical_production_name(production_name)
    node = _asset_node(canonical_name, request.node_id)
    actor = _crew_identity(http_request, canonical_name).actor
    asset_id = f"asset-{uuid4().hex}"
    try:
        require_access(
            actor=actor, action="EDIT", accountability=node.accountability,
            scope=request.task_id, status=node.status,
        )
        storage = _resolved_storage(
            production_name=canonical_name, asset_id=asset_id, version_number=1,
            filename=request.filename, storage=request.storage,
            content_base64=request.content_base64, content_type=request.content_type,
        )
        asset = register_asset(
            persistence=production_persistence, production_name=canonical_name,
            node_id=node.node_id, task_id=request.task_id, actor=actor,
            node_accountability=node.accountability,
            asset_category=request.asset_category, filename=request.filename,
            display_name=request.display_name,
            media_document_type=request.media_document_type, storage=storage,
            external_source_tool=request.external_source_tool,
            provenance=request.provenance,
            expected_deliverable=request.expected_deliverable,
            acceptance_criteria=request.acceptance_criteria,
            preview_metadata=request.preview_metadata,
            clearance_state=request.clearance_state, asset_id=asset_id,
        )
        return asset.model_dump(mode="json")
    except (ValueError, AuthorizationDenied) as exc:
        raise _asset_error(exc) from exc


@app.post("/api/productions/{production_name}/assets/{asset_id}/versions")
def create_production_asset_version(
    production_name: str, asset_id: str, request: AssetVersionRequest, http_request: Request,
) -> dict[str, Any]:
    canonical_name = canonical_production_name(production_name)
    actor = _crew_identity(http_request, canonical_name).actor
    try:
        registry = production_persistence.load_asset_registry(canonical_name)
        versions = [item for item in registry.assets if item.asset_id == asset_id]
        if not versions:
            raise ValueError("Production asset was not found.")
        prior = latest_asset(registry, asset_id)
        require_access(
            actor=actor, action="EDIT", accountability=prior.accountability,
            status=prior.status,
        )
        next_version = max(item.version_number for item in versions) + 1
        storage = _resolved_storage(
            production_name=canonical_name, asset_id=asset_id,
            version_number=next_version, filename=request.filename,
            storage=request.storage, content_base64=request.content_base64,
            content_type=request.content_type,
        )
        asset = create_asset_version(
            persistence=production_persistence, production_name=canonical_name,
            asset_id=asset_id, actor=actor, storage=storage,
            filename=request.filename, provenance=request.provenance,
            external_source_tool=request.external_source_tool,
            preview_metadata=request.preview_metadata,
        )
        return asset.model_dump(mode="json")
    except (AttributeError, ValueError, AuthorizationDenied) as exc:
        raise _asset_error(exc) from exc


@app.post("/api/productions/{production_name}/assets/{asset_id}/submit-review")
def submit_production_asset_review(
    production_name: str, asset_id: str, version_id: str, request: Request,
) -> dict[str, Any]:
    try:
        asset = submit_asset_for_review(
            persistence=production_persistence,
            production_name=canonical_production_name(production_name),
            asset_id=asset_id, version_id=version_id,
            actor=_crew_identity(http_request, production_name).actor,
        )
        return asset.model_dump(mode="json")
    except (ValueError, AuthorizationDenied) as exc:
        raise _asset_error(exc) from exc


@app.post("/api/productions/{production_name}/assets/{asset_id}/handoff")
def handoff_production_asset(
    production_name: str, asset_id: str, request: AssetHandoffRequest, http_request: Request,
) -> dict[str, Any]:
    try:
        handoff = handoff_asset(
            persistence=production_persistence,
            production_name=canonical_production_name(production_name),
            asset_id=asset_id, actor=_crew_identity(http_request, production_name).actor,
            target_tool=request.target_tool, brief=request.brief,
            requirements=request.requirements, evidence_context=request.evidence_context,
            due_date=request.due_date, approval_context=request.approval_context,
            expected_deliverable=request.expected_deliverable,
        )
        return handoff.model_dump(mode="json")
    except (ValueError, AuthorizationDenied) as exc:
        raise _asset_error(exc) from exc


@app.post("/api/productions/{production_name}/assets/{asset_id}/return")
def return_production_asset(
    production_name: str, asset_id: str, request: AssetReturnRequest, http_request: Request,
) -> dict[str, Any]:
    canonical_name = canonical_production_name(production_name)
    actor = _crew_identity(http_request, canonical_name).actor
    try:
        registry = production_persistence.load_asset_registry(canonical_name)
        versions = [item for item in registry.assets if item.asset_id == asset_id]
        if not versions:
            raise ValueError("Production asset was not found.")
        base = latest_asset(registry, asset_id)
        require_access(
            actor=actor, action="EDIT", accountability=base.accountability,
            status=base.status,
        )
        if base.production_identity != canonical_name or base.node_id != request.node_id:
            raise ValueError("External return does not match its production and node.")
        open_handoff = next(
            (item for item in base.handoffs if item.handoff_id == request.handoff_id),
            None,
        )
        if (
            open_handoff is None
            or open_handoff.status != "WAITING_FOR_RETURN"
            or open_handoff.base_version_id != request.base_version_id
            or base.version_id != request.base_version_id
        ):
            raise ValueError("External return does not match the current open handoff.")
        next_version = max(item.version_number for item in versions) + 1
        storage = _resolved_storage(
            production_name=canonical_name, asset_id=asset_id,
            version_number=next_version, filename=request.filename,
            storage=request.storage, content_base64=request.content_base64,
            content_type=request.content_type,
        )
        asset = reconcile_external_return(
            persistence=production_persistence, production_name=canonical_name,
            asset_id=asset_id, handoff_id=request.handoff_id,
            base_version_id=request.base_version_id, node_id=request.node_id,
            actor=actor, storage=storage, filename=request.filename,
            return_metadata=request.return_metadata,
        )
        return asset.model_dump(mode="json")
    except (AttributeError, ValueError, AuthorizationDenied) as exc:
        raise _asset_error(exc) from exc


@app.post("/api/productions/{production_name}/assets/{asset_id}/review")
def review_production_asset(
    production_name: str, asset_id: str, request: AssetReviewRequest, http_request: Request,
) -> dict[str, Any]:
    try:
        asset = review_asset(
            persistence=production_persistence,
            production_name=canonical_production_name(production_name),
            asset_id=asset_id, version_id=request.version_id,
            actor=_crew_identity(http_request, production_name).actor,
            decision=request.decision, notes=request.notes,
            annotations=request.annotations,
            comparison_version_id=request.comparison_version_id,
        )
        return asset.model_dump(mode="json")
    except (ValueError, AuthorizationDenied) as exc:
        raise _asset_error(exc) from exc


if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )





@app.post("/api/productions/{production_name}/decision")
def studio_head_decision(
    production_name: str,
    decision_request: StudioHeadDecisionRequest,
    request: Request,
) -> dict[str, Any]:
    identity = _crew_identity(request, production_name)
    decided_by = identity.member.display_name
    try:
        require_access(
            actor=identity.actor, action="APPROVE",
            accountability=None,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=403, detail=exc.as_detail()) from exc
    runtime_state = production_persistence.load_runtime_state(production_name)

    if runtime_state is not None:
        raise HTTPException(
            status_code=409,
            detail="A governed runtime already exists for this production.",
        )

    decision_package_payload = production_persistence.load_pending_decision_package(
        production_name
    )

    if decision_package_payload is None:
        raise HTTPException(
            status_code=404,
            detail="Pending Studio Head decision package was not found.",
        )

    review_bundle = production_persistence.load_pending_review_bundle(
        production_name
    )

    if review_bundle is None:
        raise HTTPException(
            status_code=404,
            detail="Pending Studio Head review bundle was not found.",
        )

    production_brief_payload = review_bundle.get("production_brief")

    if not isinstance(production_brief_payload, dict):
        raise HTTPException(
            status_code=409,
            detail="Pending production brief is missing or invalid.",
        )

    delivery_artifacts = production_brief_payload.get("required_deliverables")

    if not isinstance(delivery_artifacts, list) or not delivery_artifacts:
        raise HTTPException(
            status_code=409,
            detail=(
                "Approved production requires at least one concrete "
                "delivery artifact."
            ),
        )

    approved_artifacts = {
        "production_brief": review_bundle["production_brief"],
        "research_packet": review_bundle["research_packet"],
        "creative_treatment": review_bundle["creative_treatment"],
        "production_plan": review_bundle["production_plan"],
        "production_schedule": review_bundle["production_schedule"],
        "asset_media_plan": review_bundle["asset_media_plan"],
        "clearance_report": review_bundle["clearance_compliance_report"],
        "verification_report": review_bundle["verification_qa_report"],
        "delivery_artifacts": delivery_artifacts,
        "decision_package": decision_package_payload,
    }

    try:
        decision_package = StudioHeadDecisionPackage.model_validate(
            decision_package_payload
        )

        runtime_state = approve_governed_production(
            production_name=production_name,
            decision=decision_request.decision,
            conditions=decision_request.conditions,
            decision_notes=decision_request.decision_notes,
            decided_by=decided_by,
            decision_package=decision_package,
            unresolved_risks_acknowledged=(
                decision_request.unresolved_risks_acknowledged
            ),
            approved_artifacts=approved_artifacts,
            preserved_artifacts=list(approved_artifacts.keys()),
            persistence=production_persistence,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        log_event(
            "Studio Head governed decision failed",
            severity="ERROR",
            production_name=production_name,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Studio Head decision failed before governed runtime was persisted.",
        ) from exc

    return {
        "status": runtime_state.workflow_state.status,
        "production_name": runtime_state.production_name,
        "current_stage": runtime_state.current_stage,
        "execution_authorized": runtime_state.execution_authorized,
        "active_conditions": runtime_state.workflow_state.active_conditions,
        "decision_sequence": runtime_state.memory_snapshot.active_decision_sequence,
    }


@app.post("/api/productions/{production_name}/finalize")
def finalize_production(production_name: str, request: Request) -> dict[str, Any]:
    try:
        require_access(
            actor=_crew_identity(request, production_name).actor, action="FINALIZE",
            accountability=None,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=403, detail=exc.as_detail()) from exc
    runtime_state = production_persistence.load_runtime_state(
        production_name
    )

    if runtime_state is None:
        raise HTTPException(
            status_code=404,
            detail="Governed production runtime was not found.",
        )

    approved_artifacts = production_persistence.load_approved_artifacts(
        production_name
    )

    if approved_artifacts is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Governed approved production artifacts are not available "
                "for finalization."
            ),
        )

    required_artifacts = (
        "production_brief",
        "research_packet",
        "creative_treatment",
        "production_plan",
        "production_schedule",
        "asset_media_plan",
        "clearance_report",
        "verification_report",
        "delivery_artifacts",
    )

    missing = [
        name
        for name in required_artifacts
        if name not in approved_artifacts
    ]

    if missing:
        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Approved production artifact bundle is incomplete."
                ),
                "missing_artifacts": missing,
            },
        )

    try:
        production_brief = ProductionBrief.model_validate(
            approved_artifacts["production_brief"]
        )
        research_packet = ResearchPacket.model_validate(
            approved_artifacts["research_packet"]
        )
        creative_treatment = CreativeTreatment.model_validate(
            approved_artifacts["creative_treatment"]
        )
        production_plan = ProductionPlan.model_validate(
            approved_artifacts["production_plan"]
        )
        production_schedule = ProductionSchedule.model_validate(
            approved_artifacts["production_schedule"]
        )
        asset_media_plan = AssetMediaPlan.model_validate(
            approved_artifacts["asset_media_plan"]
        )
        clearance_report = ClearanceComplianceReport.model_validate(
            approved_artifacts["clearance_report"]
        )
        verification_report = VerificationQAReport.model_validate(
            approved_artifacts["verification_report"]
        )

        delivery_artifacts = list(
            approved_artifacts["delivery_artifacts"]
        )
        final_notes = list(
            approved_artifacts.get("final_notes") or []
        )

        authorization = build_production_execution_authorization(
            runtime_state=runtime_state,
            requested_actions=["FINALIZE_PRODUCTION_PACKAGE"],
        )

        final_package = finalize_production_package(
            runtime_state=runtime_state,
            execution_authorization=authorization,
            production_brief=production_brief,
            research_packet=research_packet,
            creative_treatment=creative_treatment,
            production_plan=production_plan,
            production_schedule=production_schedule,
            asset_media_plan=asset_media_plan,
            clearance_report=clearance_report,
            verification_report=verification_report,
            delivery_artifacts=delivery_artifacts,
            persistence=production_persistence,
            final_notes=final_notes,
            production_assets=approved_asset_references(
                production_persistence.load_asset_registry(production_name)
            ) if hasattr(production_persistence, "load_asset_registry") else [],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        log_event(
            "Governed production finalization failed",
            severity="ERROR",
            production_name=production_name,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Governed production finalization failed before "
                "the final package was persisted."
            ),
        ) from exc

    return {
        "status": "READY_FOR_DELIVERY",
        "production_name": production_name,
        "decision_sequence": final_package.decision_sequence,
        "approval_status": final_package.approval_status,
        "delivery_status": final_package.delivery_status,
        "readiness_score": final_package.readiness_score,
        "authorized_actions": final_package.authorized_actions,
        "delivery_artifacts": final_package.delivery_artifacts,
    }


@app.post("/api/productions/{production_name}/deliver")
def deliver_production(production_name: str, request: Request) -> dict[str, Any]:
    try:
        require_access(
            actor=_crew_identity(request, production_name).actor, action="DELIVER",
            accountability=None,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=403, detail=exc.as_detail()) from exc
    runtime_state = production_persistence.load_runtime_state(production_name)

    if runtime_state is None:
        raise HTTPException(
            status_code=404,
            detail="Governed production runtime was not found.",
        )

    final_package = production_persistence.load_final_package(
        production_name
    )

    if final_package is None:
        raise HTTPException(
            status_code=404,
            detail="Governed final production package was not found.",
        )

    if final_package.production_name != production_name:
        raise HTTPException(
            status_code=409,
            detail="Persisted final package does not belong to the requested production.",
        )

    if runtime_state.production_name != production_name:
        raise HTTPException(
            status_code=409,
            detail="Persisted runtime does not belong to the requested production.",
        )

    try:
        result = complete_governed_delivery(
            final_package=final_package,
            runtime_state=runtime_state,
            persistence=production_persistence,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        log_event(
            "Governed delivery failed",
            severity="ERROR",
            production_name=production_name,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Governed delivery failed before terminal state was persisted.",
        ) from exc

    log_event(
        "Governed delivery completed",
        production_name=production_name,
        delivery_status=result.receipt.delivery_status,
        current_stage=result.runtime_state.current_stage,
    )

    return {
        "status": "DELIVERED",
        "production_name": production_name,
        "current_stage": result.runtime_state.current_stage,
        "execution_authorized": result.runtime_state.execution_authorized,
        "receipt": result.receipt.__dict__,
    }


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
def frontend(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404)

    candidate = FRONTEND_DIST / full_path

    if full_path and candidate.exists() and candidate.is_file():
        return FileResponse(candidate)

    index = FRONTEND_DIST / "index.html"

    if not index.exists():
        raise HTTPException(
            status_code=503,
            detail="Frontend build unavailable.",
        )

    return FileResponse(index)


from pydantic import BaseModel

from studio_command.graph import build_production_graph
from studio_command.reality import apply_reality_shift


class RealityShiftRequest(BaseModel):
    changed_node_ids: list[str]
    reason: str


@app.post("/api/reality-shift")
def reality_shift(payload: RealityShiftRequest, request: Request) -> dict[str, Any]:
    snapshot = studio_snapshot()
    identity = _crew_identity(request, snapshot["production_name"])
    try:
        require_access(
            actor=identity.actor, action="REALITY_SHIFT", accountability=None,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=403, detail=exc.as_detail()) from exc
    from studio_command.models import ProductionGraphNode, ProductionGraphState

    from studio_command.models import ProductionGraphNode, ProductionGraphState

    graph_data = snapshot["graph"]

    graph_nodes = [
        ProductionGraphNode(
            node_id=node["node_id"],
            task_name=node["task_name"],
            responsible_role=node["responsible_role"],
            dependencies=list(node["dependencies"]),
            dependents=list(node["dependents"]),
            status=node["status"],
            can_run_in_parallel_with=list(node.get("parallel_with", [])),
            approval_required=node["approval_required"],
            stale_reason=node.get("stale_reason"),
        )
        for node in graph_data["nodes"]
    ]

    graph_state = ProductionGraphState(
        production_name=snapshot["production_name"],
        nodes=graph_nodes,
        ready_nodes=list(graph_data["ready_nodes"]),
        running_nodes=list(graph_data["running_nodes"]),
        completed_nodes=list(graph_data["completed_nodes"]),
        blocked_nodes=list(graph_data["blocked_nodes"]),
        stale_nodes=list(graph_data["stale_nodes"]),
        graph_complete=graph_data["graph_complete"],
    )

    result = apply_reality_shift(
        graph_state=graph_state,
        changed_node_ids=payload.changed_node_ids,
        reason=payload.reason,
    )

    return {
        "status": "REALITY_SHIFT_DETECTED",
        "reason": result.reason,
        "changed_nodes": result.changed_nodes,
        "stale_nodes": result.stale_nodes,
        "preserved_nodes": result.preserved_nodes,
        "safe_to_continue": result.preserved_nodes,
        "human_decision_required": result.human_decision_required,
        "message": (
            "Production reality changed. Kevaro preserved valid work "
            "and invalidated only the affected downstream production path."
        ),
    }
