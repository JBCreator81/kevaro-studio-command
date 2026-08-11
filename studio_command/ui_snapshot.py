from __future__ import annotations

from typing import Any

from .models import (
    FinalProductionPackage,
    GovernedProductionRuntimeState,
    ProductionGraphState,
)


def build_studio_command_snapshot(
    *,
    runtime_state: GovernedProductionRuntimeState,
    graph_state: ProductionGraphState,
    final_package: FinalProductionPackage | None = None,
) -> dict[str, Any]:
    if graph_state.production_name != runtime_state.production_name:
        raise ValueError(
            "Graph state and governed runtime must belong to the same production."
        )

    if (
        final_package is not None
        and final_package.production_name != runtime_state.production_name
    ):
        raise ValueError(
            "Final package and governed runtime must belong to the same production."
        )

    latest_history = runtime_state.decision_history[-1]

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
        "graph": {
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
                }
                for node in graph_state.nodes
            ],
        },
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
