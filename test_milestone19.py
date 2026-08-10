from studio_command.graph import (
    build_production_graph,
    complete_graph_node,
    propagate_graph_change,
    resume_stale_graph_nodes,
    start_graph_node,
)
from studio_command.models import (
    ProductionPlan,
    ProductionSchedule,
    ProductionTask,
    ScheduledTask,
)


PRODUCTION = "Luxury Wellness Campaign"


production_plan = ProductionPlan(
    production_name=PRODUCTION,
    execution_summary="Milestone 19 live production graph validation.",
    tasks=[
        ProductionTask(
            task_name="Production Brief",
            responsible_role="Executive Producer",
            deliverable="Approved production brief.",
            dependencies=[],
            completion_criteria=[
                "Production goals and requirements captured."
            ],
            approval_required=False,
            risk_notes=[],
        ),
        ProductionTask(
            task_name="Research",
            responsible_role="Research Agent",
            deliverable="Evidence-backed research packet.",
            dependencies=["Production Brief"],
            completion_criteria=[
                "Required evidence gathered and summarized."
            ],
            approval_required=False,
            risk_notes=[],
        ),
        ProductionTask(
            task_name="Creative Development",
            responsible_role="Creative Development Agent",
            deliverable="Creative treatment.",
            dependencies=["Production Brief"],
            completion_criteria=[
                "Creative direction is production-ready."
            ],
            approval_required=False,
            risk_notes=[],
        ),
        ProductionTask(
            task_name="Final Assembly",
            responsible_role="Production Manager",
            deliverable="Integrated production package.",
            dependencies=[
                "Research",
                "Creative Development",
            ],
            completion_criteria=[
                "Research and creative work integrated."
            ],
            approval_required=False,
            risk_notes=[],
        ),
    ],
    critical_path=[
        "Production Brief",
        "Research",
        "Final Assembly",
    ],
    parallel_workstreams=[
        [
            "Research",
            "Creative Development",
        ]
    ],
    milestones=[
        "Brief Complete",
        "Parallel Development Complete",
        "Final Assembly Complete",
    ],
    approval_gates=[],
    blockers=[],
    schedule_risks=[],
    next_actions=[
        "Complete Production Brief."
    ],
)


production_schedule = ProductionSchedule(
    production_name=PRODUCTION,
    delivery_target="Milestone 19 validation delivery.",
    scheduled_tasks=[
        ScheduledTask(
            task_name="Production Brief",
            responsible_role="Executive Producer",
            sequence_position=1,
            depends_on=[],
            can_run_in_parallel_with=[],
            target_window="Stage 1",
            completion_gate="Production brief complete.",
        ),
        ScheduledTask(
            task_name="Research",
            responsible_role="Research Agent",
            sequence_position=2,
            depends_on=["Production Brief"],
            can_run_in_parallel_with=[
                "Creative Development"
            ],
            target_window="Stage 2",
            completion_gate="Research packet complete.",
        ),
        ScheduledTask(
            task_name="Creative Development",
            responsible_role="Creative Development Agent",
            sequence_position=2,
            depends_on=["Production Brief"],
            can_run_in_parallel_with=[
                "Research"
            ],
            target_window="Stage 2",
            completion_gate="Creative treatment complete.",
        ),
        ScheduledTask(
            task_name="Final Assembly",
            responsible_role="Production Manager",
            sequence_position=3,
            depends_on=[
                "Research",
                "Creative Development",
            ],
            can_run_in_parallel_with=[],
            target_window="Stage 3",
            completion_gate="Integrated package complete.",
        ),
    ],
    critical_path=[
        "Production Brief",
        "Research",
        "Final Assembly",
    ],
    parallel_execution_groups=[
        [
            "Research",
            "Creative Development",
        ]
    ],
    approval_windows=[],
    schedule_buffer=[],
    deadline_threats=[],
    immediate_schedule_actions=[
        "Begin Production Brief."
    ],
)


# Build dependency-aware graph.
graph = build_production_graph(
    production_plan=production_plan,
    production_schedule=production_schedule,
)

assert graph.ready_nodes == [
    "Production Brief"
]
assert graph.running_nodes == []
assert graph.completed_nodes == []
assert graph.graph_complete is False


# Complete the root node.
graph = start_graph_node(
    graph_state=graph,
    node_id="Production Brief",
)

assert graph.running_nodes == [
    "Production Brief"
]

graph = complete_graph_node(
    graph_state=graph,
    node_id="Production Brief",
)

# Research and Creative Development must release together.
assert set(graph.ready_nodes) == {
    "Research",
    "Creative Development",
}


# Start both parallel branches simultaneously.
graph = start_graph_node(
    graph_state=graph,
    node_id="Research",
)

graph = start_graph_node(
    graph_state=graph,
    node_id="Creative Development",
)

assert set(graph.running_nodes) == {
    "Research",
    "Creative Development",
}


# Completing only Research must NOT release Final Assembly.
graph = complete_graph_node(
    graph_state=graph,
    node_id="Research",
)

assert "Final Assembly" not in graph.ready_nodes


# Completing Creative Development releases Final Assembly.
graph = complete_graph_node(
    graph_state=graph,
    node_id="Creative Development",
)

assert graph.ready_nodes == [
    "Final Assembly"
]


graph = start_graph_node(
    graph_state=graph,
    node_id="Final Assembly",
)

graph = complete_graph_node(
    graph_state=graph,
    node_id="Final Assembly",
)

assert graph.graph_complete is True
assert set(graph.completed_nodes) == {
    "Production Brief",
    "Research",
    "Creative Development",
    "Final Assembly",
}


# A research change should invalidate only Research and its downstream work.
changed_graph = propagate_graph_change(
    graph_state=graph,
    changed_node_ids=["Research"],
    reason="Research evidence changed and must be refreshed.",
)

assert changed_graph.graph_complete is False

assert set(changed_graph.stale_nodes) == {
    "Research",
    "Final Assembly",
}

# Unaffected completed work must stay preserved.
assert "Production Brief" in changed_graph.completed_nodes
assert "Creative Development" in changed_graph.completed_nodes

assert "Production Brief" not in changed_graph.stale_nodes
assert "Creative Development" not in changed_graph.stale_nodes


# Only Research can resume initially.
changed_graph = resume_stale_graph_nodes(
    graph_state=changed_graph
)

assert "Research" in changed_graph.ready_nodes
assert "Research" not in changed_graph.stale_nodes
assert "Final Assembly" in changed_graph.stale_nodes


# Correct Research without rerunning Creative Development.
changed_graph = start_graph_node(
    graph_state=changed_graph,
    node_id="Research",
)

changed_graph = complete_graph_node(
    graph_state=changed_graph,
    node_id="Research",
)

assert "Creative Development" in changed_graph.completed_nodes


# Final Assembly may now resume because both dependencies are valid.
changed_graph = resume_stale_graph_nodes(
    graph_state=changed_graph
)

assert "Final Assembly" in changed_graph.ready_nodes
assert changed_graph.stale_nodes == []


changed_graph = start_graph_node(
    graph_state=changed_graph,
    node_id="Final Assembly",
)

changed_graph = complete_graph_node(
    graph_state=changed_graph,
    node_id="Final Assembly",
)

assert changed_graph.graph_complete is True

assert set(changed_graph.completed_nodes) == {
    "Production Brief",
    "Research",
    "Creative Development",
    "Final Assembly",
}


# Unknown changed nodes must be rejected.
try:
    propagate_graph_change(
        graph_state=changed_graph,
        changed_node_ids=["Unknown Node"],
        reason="Invalid test.",
    )
    raise AssertionError(
        "Unknown graph nodes should fail."
    )
except ValueError:
    pass


print("MILESTONE 19 LIVE PRODUCTION GRAPH VALIDATION: PASS")
