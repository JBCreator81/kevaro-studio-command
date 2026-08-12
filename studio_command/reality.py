from __future__ import annotations

from dataclasses import dataclass

from studio_command.graph import propagate_graph_change
from studio_command.models import ProductionGraphState


@dataclass(frozen=True)
class RealityShiftResult:
    graph_state: ProductionGraphState
    changed_nodes: list[str]
    stale_nodes: list[str]
    preserved_nodes: list[str]
    reason: str
    human_decision_required: bool


def apply_reality_shift(
    *,
    graph_state: ProductionGraphState,
    changed_node_ids: list[str],
    reason: str,
) -> RealityShiftResult:
    previous_completed = set(graph_state.completed_nodes)

    updated = propagate_graph_change(
        graph_state=graph_state,
        changed_node_ids=changed_node_ids,
        reason=reason,
    )

    stale = list(updated.stale_nodes)

    preserved = [
        node_id
        for node_id in previous_completed
        if node_id not in stale
    ]

    return RealityShiftResult(
        graph_state=updated,
        changed_nodes=list(changed_node_ids),
        stale_nodes=stale,
        preserved_nodes=preserved,
        reason=reason.strip(),
        human_decision_required=bool(stale),
    )
