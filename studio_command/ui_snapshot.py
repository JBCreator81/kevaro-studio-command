from __future__ import annotations

from typing import Any

from .identity import require_production_identity
from .models import (
    FinalProductionPackage,
    GovernedProductionRuntimeState,
    ProductionGraphState,
)


def _node_intelligence(
    artifact_source: dict[str, Any],
    package_data: dict[str, Any] | None,
) -> dict[str, Any]:
    def artifact(key: str) -> Any:
        if key in artifact_source:
            return artifact_source[key]
        if package_data is not None:
            return package_data.get(key)
        return None

    return {
        "Production Brief": artifact("production_brief"),
        "Research": artifact("research_packet"),
        "Creative Development": artifact("creative_treatment"),
        "Production Planning": artifact("production_plan"),
        "Scheduling": artifact("production_schedule"),
        "Asset & Media": artifact("asset_media_plan"),
        "Clearance & Compliance": (
            artifact("clearance_report")
            or artifact("clearance_compliance_report")
        ),
        "Verification QA": (
            artifact("verification_report")
            or artifact("verification_qa_report")
        ),
        "Studio Head Decision": (
            artifact_source.get("decision_package")
            or artifact_source.get("studio_head_decision_package")
            or (
                package_data.get("decision_history")
                if package_data is not None
                else None
            )
        ),
        "Final Package": package_data,
    }


def _graph_snapshot(
    graph_state: ProductionGraphState,
    node_intelligence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ready_nodes": graph_state.ready_nodes,
        "running_nodes": graph_state.running_nodes,
        "completed_nodes": graph_state.completed_nodes,
        "blocked_nodes": graph_state.blocked_nodes,
        "stale_nodes": graph_state.stale_nodes,
        "graph_complete": graph_state.graph_complete,
        "nodes": [
            {
                "node_id": node.node_id,
                "task_name": node.task_name,
                "responsible_role": node.responsible_role,
                "dependencies": node.dependencies,
                "dependents": node.dependents,
                "status": node.status,
                "parallel_with": node.can_run_in_parallel_with,
                "approval_required": node.approval_required,
                "stale_reason": node.stale_reason,
                "artifact": node_intelligence.get(node.node_id),
            }
            for node in graph_state.nodes
        ],
    }


def build_pending_studio_command_snapshot(
    *,
    production_name: str,
    graph_state: ProductionGraphState,
    review_bundle: dict[str, Any],
) -> dict[str, Any]:
    canonical_name = require_production_identity(
        production_name,
        graph_state.production_name,
        review_bundle["production_plan"]["production_name"],
        review_bundle["production_schedule"]["production_name"],
        review_bundle["studio_head_decision_package"]["production_name"],
    )
    node_intelligence = _node_intelligence(review_bundle, None)

    return {
        "production_name": canonical_name,
        "current_stage": "STUDIO_HEAD_REVIEW",
        "approval_status": "PENDING_STUDIO_HEAD_REVIEW",
        "decision_sequence": 0,
        "execution_authorized": False,
        "corrective_cycle_active": False,
        "active_conditions": [],
        "preserved_artifacts": [],
        "stale_artifacts": [],
        "graph": _graph_snapshot(graph_state, node_intelligence),
        "node_intelligence": node_intelligence,
        "production_package": None,
        "delivery": None,
    }


def build_studio_command_snapshot(
    *,
    runtime_state: GovernedProductionRuntimeState,
    graph_state: ProductionGraphState,
    final_package: FinalProductionPackage | None = None,
    approved_artifacts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_production_identity(
        runtime_state.production_name,
        graph_state.production_name,
        *(
            [final_package.production_name]
            if final_package is not None
            else []
        ),
    )

    latest_history = runtime_state.decision_history[-1]
    package_data = (
        final_package.model_dump(mode="json")
        if final_package is not None
        else None
    )
    node_intelligence = _node_intelligence(approved_artifacts or {}, package_data)

    return {
        "production_name": runtime_state.production_name,
        "current_stage": runtime_state.current_stage,
        "approval_status": runtime_state.workflow_state.status,
        "decision_sequence": latest_history.sequence,
        "execution_authorized": runtime_state.execution_authorized,
        "corrective_cycle_active": runtime_state.corrective_cycle_active,
        "active_conditions": runtime_state.workflow_state.active_conditions,
        "preserved_artifacts": runtime_state.memory_snapshot.preserved_artifacts,
        "stale_artifacts": runtime_state.memory_snapshot.stale_artifacts,
        "graph": _graph_snapshot(graph_state, node_intelligence),
        "node_intelligence": node_intelligence,
        "production_package": package_data,
        "delivery": (
            {
                "status": final_package.delivery_status,
                "readiness_score": final_package.readiness_score,
                "delivery_artifacts": final_package.delivery_artifacts,
                "final_notes": final_package.final_notes,
            }
            if final_package is not None
            else None
        ),
    }
