from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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


@app.on_event("startup")
async def startup_event() -> None:
    log_event(
        "Kevaro Studio Command service started",
        frontend_available=FRONTEND_DIST.exists(),
        snapshot_available=SNAPSHOT_PATH.exists(),
    )


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "revision": REVISION,
        "uptime_seconds": round(time.time() - STARTED_AT, 2),
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
    if not SNAPSHOT_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Studio Command snapshot is unavailable.",
        )

    return json.loads(SNAPSHOT_PATH.read_text())


if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )


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
def reality_shift(request: RealityShiftRequest) -> dict[str, Any]:
    snapshot = studio_snapshot()

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
        changed_node_ids=request.changed_node_ids,
        reason=request.reason,
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
