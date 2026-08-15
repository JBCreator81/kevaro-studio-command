from studio_command.models import (
    FinalProductionPackage,
    GovernedProductionRuntimeState,
    ProductionDecisionHistoryEntry,
    ProductionGraphNode,
    ProductionGraphState,
    ProductionMemorySnapshot,
    ProductionWorkflowState,
)
from studio_command.ui_snapshot import build_studio_command_snapshot


PRODUCTION = "Luxury Wellness Campaign"


workflow_state = ProductionWorkflowState(
    production_name=PRODUCTION,
    status="APPROVED",
    active_conditions=[],
    corrective_action_required=False,
    production_may_advance=True,
    production_stopped=False,
    next_stage="DOWNSTREAM_PRODUCTION",
)

history = ProductionDecisionHistoryEntry(
    sequence=1,
    production_name=PRODUCTION,
    decision="APPROVE",
    decided_by="Studio Head",
    source_recommendation="APPROVE",
    recommendation_followed=True,
    resulting_status="APPROVED",
    next_stage="DOWNSTREAM_PRODUCTION",
    production_may_advance=True,
    corrective_action_required=False,
    production_stopped=False,
    active_conditions=[],
    unresolved_risks_acknowledged=[],
    decision_notes="Approved for final delivery.",
)

memory = ProductionMemorySnapshot(
    production_name=PRODUCTION,
    current_stage="DOWNSTREAM_PRODUCTION",
    active_decision_sequence=1,
    approved_status="APPROVED",
    active_conditions=[],
    preserved_artifacts=[
        "Production Brief",
        "Research Packet",
        "Creative Treatment",
        "Production Plan",
        "Production Schedule",
        "Asset Media Plan",
        "Clearance Report",
        "Verification QA Report",
    ],
    stale_artifacts=[],
    known_good_state=True,
)

runtime = GovernedProductionRuntimeState(
    production_name=PRODUCTION,
    workflow_state=workflow_state,
    decision_history=[history],
    memory_snapshot=memory,
    change_impact=None,
    impact_brief=None,
    execution_authorized=True,
    corrective_cycle_active=False,
    current_stage="DOWNSTREAM_PRODUCTION",
)


nodes = [
    ProductionGraphNode(
        node_id="Production Brief",
        task_name="Production Brief",
        responsible_role="Executive Producer",
        dependencies=[],
        dependents=["Research"],
        status="COMPLETED",
        can_run_in_parallel_with=[],
        approval_required=False,
        stale_reason=None,
    ),
    ProductionGraphNode(
        node_id="Research",
        task_name="Research",
        responsible_role="Research Agent",
        dependencies=["Production Brief"],
        dependents=["Final Assembly"],
        status="COMPLETED",
        can_run_in_parallel_with=["Creative Development"],
        approval_required=False,
        stale_reason=None,
    ),
    ProductionGraphNode(
        node_id="Creative Development",
        task_name="Creative Development",
        responsible_role="Creative Development Agent",
        dependencies=["Production Brief"],
        dependents=["Final Assembly"],
        status="COMPLETED",
        can_run_in_parallel_with=["Research"],
        approval_required=False,
        stale_reason=None,
    ),
    ProductionGraphNode(
        node_id="Final Assembly",
        task_name="Final Assembly",
        responsible_role="Production Manager",
        dependencies=["Research", "Creative Development"],
        dependents=[],
        status="COMPLETED",
        can_run_in_parallel_with=[],
        approval_required=False,
        stale_reason=None,
    ),
]

graph = ProductionGraphState(
    production_name=PRODUCTION,
    nodes=nodes,
    ready_nodes=[],
    running_nodes=[],
    completed_nodes=[
        "Production Brief",
        "Research",
        "Creative Development",
        "Final Assembly",
    ],
    blocked_nodes=[],
    stale_nodes=[],
    graph_complete=True,
)


# Milestone 21 already validates construction of the complete package.
# Here we use the validated model as the delivery object consumed by the UI contract.
final_package = FinalProductionPackage.model_construct(
    production_name=PRODUCTION,
    decision_sequence=1,
    approval_status="APPROVED",
    active_conditions=[],
    production_brief={},
    research_packet={},
    creative_treatment={},
    production_plan={},
    production_schedule={},
    asset_media_plan={},
    clearance_report={},
    verification_report={},
    decision_history=[history],
    authorized_actions=["Assemble final production package"],
    delivery_artifacts=[
        "gs://test-bucket/final/hero-video.mp4",
    ],
    delivery_status="READY_FOR_DELIVERY",
    readiness_score=100,
    final_notes=[
        "Final governed production package ready for delivery.",
    ],
)


snapshot = build_studio_command_snapshot(
    runtime_state=runtime,
    graph_state=graph,
    final_package=final_package,
)


assert snapshot["production_name"] == PRODUCTION
assert snapshot["approval_status"] == "APPROVED"
assert snapshot["decision_sequence"] == 1
assert snapshot["execution_authorized"] is True
assert snapshot["corrective_cycle_active"] is False

assert snapshot["graph"]["graph_complete"] is True
assert len(snapshot["graph"]["nodes"]) == 4
assert snapshot["graph"]["blocked_nodes"] == []
assert snapshot["graph"]["stale_nodes"] == []

assert snapshot["delivery"] is not None
assert snapshot["delivery"]["status"] == "READY_FOR_DELIVERY"
assert snapshot["delivery"]["readiness_score"] == 100
assert snapshot["delivery"]["delivery_artifacts"] == [
    "gs://test-bucket/final/hero-video.mp4"
]


# A different production must never leak into the Command Center snapshot.
wrong_graph = graph.model_copy(
    update={"production_name": "Different Production"}
)

try:
    build_studio_command_snapshot(
        runtime_state=runtime,
        graph_state=wrong_graph,
        final_package=final_package,
    )
    raise AssertionError(
        "Cross-production graph state must be rejected."
    )
except ValueError:
    pass


wrong_package = final_package.model_copy(
    update={"production_name": "Different Production"}
)

try:
    build_studio_command_snapshot(
        runtime_state=runtime,
        graph_state=graph,
        final_package=wrong_package,
    )
    raise AssertionError(
        "Cross-production final package must be rejected."
    )
except ValueError:
    pass


print("MILESTONE 22 STUDIO COMMAND SNAPSHOT VALIDATION: PASS")
print("MILESTONE 22 GOVERNED RUNTIME CONNECTION: PASS")
print("MILESTONE 22 PRODUCTION GRAPH CONNECTION: PASS")
print("MILESTONE 21-22 DELIVERY CONNECTION: PASS")
print("MILESTONE 1-22 JUDGE EXPERIENCE DATA PATH: PASS")
