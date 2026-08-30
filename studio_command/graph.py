from __future__ import annotations

from .access import require_access
from .accountability import STUDIO_HEAD, ai_actor
from .models import (
    AccountabilityActor,
    AccountabilityMetadata,
    ProductionGraphNode,
    ProductionGraphState,
    ProductionPlan,
    ProductionSchedule,
)


def build_production_graph(
    *,
    production_plan: ProductionPlan,
    production_schedule: ProductionSchedule,
) -> ProductionGraphState:
    if production_plan.production_name != production_schedule.production_name:
        raise ValueError(
            "Production plan and schedule must belong to the same production."
        )

    plan_tasks = {
        task.task_name: task
        for task in production_plan.tasks
    }

    schedule_tasks = {
        task.task_name: task
        for task in production_schedule.scheduled_tasks
    }

    if set(plan_tasks) != set(schedule_tasks):
        raise ValueError(
            "Production plan tasks and scheduled tasks must match exactly."
        )

    nodes: list[ProductionGraphNode] = []

    for task_name, plan_task in plan_tasks.items():
        scheduled_task = schedule_tasks[task_name]

        dependencies = list(
            dict.fromkeys(
                scheduled_task.depends_on
                or plan_task.dependencies
            )
        )

        missing_dependencies = [
            dependency
            for dependency in dependencies
            if dependency not in plan_tasks
        ]

        if missing_dependencies:
            raise ValueError(
                f"Task {task_name} references unknown dependencies: "
                f"{missing_dependencies}"
            )

        nodes.append(
            ProductionGraphNode(
                node_id=task_name,
                task_name=task_name,
                responsible_role=plan_task.responsible_role,
                dependencies=dependencies,
                dependents=[],
                status="PENDING",
                can_run_in_parallel_with=list(
                    dict.fromkeys(
                        scheduled_task.can_run_in_parallel_with
                    )
                ),
                approval_required=plan_task.approval_required,
                stale_reason=None,
                accountability=AccountabilityMetadata(
                    human_owner=STUDIO_HEAD,
                    ai_agent_responsible=ai_actor(
                        plan_task.responsible_role.lower().replace(" ", "_"),
                        plan_task.responsible_role,
                    ),
                    current_status="PENDING",
                    human_final_authority=True,
                ),
            )
        )

    node_map = {
        node.node_id: node
        for node in nodes
    }

    dependent_map: dict[str, list[str]] = {
        node.node_id: []
        for node in nodes
    }

    for node in nodes:
        for dependency in node.dependencies:
            dependent_map[dependency].append(
                node.node_id
            )

    finalized_nodes: list[ProductionGraphNode] = []

    for node in nodes:
        ready = not node.dependencies

        finalized_nodes.append(
            node.model_copy(
                update={
                    "dependents": dependent_map[node.node_id],
                    "status": "READY" if ready else "PENDING",
                }
            )
        )

    ready_nodes = [
        node.node_id
        for node in finalized_nodes
        if node.status == "READY"
    ]

    return ProductionGraphState(
        production_name=production_plan.production_name,
        nodes=finalized_nodes,
        ready_nodes=ready_nodes,
        running_nodes=[],
        completed_nodes=[],
        blocked_nodes=[],
        stale_nodes=[],
        graph_complete=False,
    )


def propagate_graph_change(
    *,
    graph_state: ProductionGraphState,
    changed_node_ids: list[str],
    reason: str,
) -> ProductionGraphState:
    if not changed_node_ids:
        raise ValueError(
            "Change propagation requires at least one changed node."
        )

    if not reason.strip():
        raise ValueError(
            "Change propagation requires a clear stale reason."
        )

    node_map = {
        node.node_id: node
        for node in graph_state.nodes
    }

    unknown_nodes = [
        node_id
        for node_id in changed_node_ids
        if node_id not in node_map
    ]

    if unknown_nodes:
        raise ValueError(
            f"Unknown production graph nodes: {unknown_nodes}"
        )

    impacted: set[str] = set(changed_node_ids)
    queue = list(changed_node_ids)

    while queue:
        current_id = queue.pop(0)
        current = node_map[current_id]

        for dependent in current.dependents:
            if dependent not in impacted:
                impacted.add(dependent)
                queue.append(dependent)

    updated_nodes = []

    for node in graph_state.nodes:
        if node.node_id in impacted:
            updated_nodes.append(
                node.model_copy(
                    update={
                        "status": "STALE",
                        "stale_reason": reason.strip(),
                    }
                )
            )
        else:
            updated_nodes.append(node)

    stale_nodes = list(
        dict.fromkeys(
            graph_state.stale_nodes
            + [
                node.node_id
                for node in graph_state.nodes
                if node.node_id in impacted
            ]
        )
    )

    ready_nodes = [
        node_id
        for node_id in graph_state.ready_nodes
        if node_id not in impacted
    ]

    running_nodes = [
        node_id
        for node_id in graph_state.running_nodes
        if node_id not in impacted
    ]

    completed_nodes = [
        node_id
        for node_id in graph_state.completed_nodes
        if node_id not in impacted
    ]

    blocked_nodes = [
        node_id
        for node_id in graph_state.blocked_nodes
        if node_id not in impacted
    ]

    return graph_state.model_copy(
        update={
            "nodes": updated_nodes,
            "ready_nodes": ready_nodes,
            "running_nodes": running_nodes,
            "completed_nodes": completed_nodes,
            "blocked_nodes": blocked_nodes,
            "stale_nodes": stale_nodes,
            "graph_complete": False,
        }
    )




def start_graph_node(
    *,
    graph_state: ProductionGraphState,
    node_id: str,
    actor: AccountabilityActor | None = None,
) -> ProductionGraphState:
    node_map = {
        node.node_id: node
        for node in graph_state.nodes
    }

    if node_id not in node_map:
        raise ValueError(
            f"Unknown production graph node: {node_id}"
        )

    node = node_map[node_id]

    if actor is not None:
        require_access(
            actor=actor,
            action="START",
            accountability=node.accountability,
            status=node.status,
        )

    if node.status != "READY":
        raise ValueError(
            f"Node {node_id} is not ready to start."
        )

    updated_nodes = []

    for current in graph_state.nodes:
        if current.node_id == node_id:
            updated_nodes.append(
                current.model_copy(
                    update={"status": "RUNNING"}
                )
            )
        else:
            updated_nodes.append(current)

    return graph_state.model_copy(
        update={
            "nodes": updated_nodes,
            "ready_nodes": [
                item
                for item in graph_state.ready_nodes
                if item != node_id
            ],
            "running_nodes": list(
                dict.fromkeys(
                    graph_state.running_nodes + [node_id]
                )
            ),
        }
    )


def complete_graph_node(
    *,
    graph_state: ProductionGraphState,
    node_id: str,
    actor: AccountabilityActor | None = None,
) -> ProductionGraphState:
    node_map = {
        node.node_id: node
        for node in graph_state.nodes
    }

    if node_id not in node_map:
        raise ValueError(
            f"Unknown production graph node: {node_id}"
        )

    node = node_map[node_id]

    if actor is not None:
        require_access(
            actor=actor,
            action="COMPLETE",
            accountability=node.accountability,
            status=node.status,
        )

    if node.status != "RUNNING":
        raise ValueError(
            f"Node {node_id} must be running before it can complete."
        )

    completed_nodes = list(
        dict.fromkeys(
            graph_state.completed_nodes + [node_id]
        )
    )

    updated_nodes = []

    for current in graph_state.nodes:
        if current.node_id == node_id:
            updated_nodes.append(
                current.model_copy(
                    update={"status": "COMPLETED"}
                )
            )
        else:
            updated_nodes.append(current)

    refreshed_nodes = []
    newly_ready = []
    completed_set = set(completed_nodes)

    for current in updated_nodes:
        if current.status == "PENDING":
            dependencies_satisfied = all(
                dependency in completed_set
                for dependency in current.dependencies
            )

            if dependencies_satisfied:
                refreshed_nodes.append(
                    current.model_copy(
                        update={"status": "READY"}
                    )
                )
                newly_ready.append(current.node_id)
                continue

        refreshed_nodes.append(current)

    ready_nodes = list(
        dict.fromkeys(
            graph_state.ready_nodes + newly_ready
        )
    )

    running_nodes = [
        item
        for item in graph_state.running_nodes
        if item != node_id
    ]

    graph_complete = all(
        current.status == "COMPLETED"
        for current in refreshed_nodes
    )

    return graph_state.model_copy(
        update={
            "nodes": refreshed_nodes,
            "ready_nodes": ready_nodes,
            "running_nodes": running_nodes,
            "completed_nodes": completed_nodes,
            "graph_complete": graph_complete,
        }
    )


def resume_stale_graph_nodes(
    *,
    graph_state: ProductionGraphState,
) -> ProductionGraphState:
    if not graph_state.stale_nodes:
        return graph_state

    completed_set = set(
        graph_state.completed_nodes
    )

    updated_nodes = []
    resumed_nodes = []

    for node in graph_state.nodes:
        if node.status == "STALE":
            dependencies_satisfied = all(
                dependency in completed_set
                for dependency in node.dependencies
            )

            if dependencies_satisfied:
                updated_nodes.append(
                    node.model_copy(
                        update={
                            "status": "READY",
                            "stale_reason": None,
                        }
                    )
                )
                resumed_nodes.append(node.node_id)
                continue

        updated_nodes.append(node)

    remaining_stale = [
        node_id
        for node_id in graph_state.stale_nodes
        if node_id not in resumed_nodes
    ]

    ready_nodes = list(
        dict.fromkeys(
            graph_state.ready_nodes
            + resumed_nodes
        )
    )

    return graph_state.model_copy(
        update={
            "nodes": updated_nodes,
            "ready_nodes": ready_nodes,
            "stale_nodes": remaining_stale,
            "graph_complete": False,
        }
    )
