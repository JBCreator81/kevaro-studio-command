import json
from pathlib import Path

from studio_command.models import (
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
    next_stage="READY_FOR_DELIVERY",
)

history = ProductionDecisionHistoryEntry(
    sequence=1,
    production_name=PRODUCTION,
    decision="APPROVE",
    decided_by="Studio Head",
    source_recommendation="APPROVE",
    recommendation_followed=True,
    resulting_status="APPROVED",
    next_stage="READY_FOR_DELIVERY",
    production_may_advance=True,
    corrective_action_required=False,
    production_stopped=False,
    active_conditions=[],
    unresolved_risks_acknowledged=[],
    decision_notes="Approved final production package.",
)

memory = ProductionMemorySnapshot(
    production_name=PRODUCTION,
    current_stage="READY_FOR_DELIVERY",
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
        "Final Production Package",
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
    current_stage="READY_FOR_DELIVERY",
)

node_specs = [
    ("Production Brief", "Executive Producer", [], ["Research"], "COMPLETED"),
    ("Research", "Research Agent", ["Production Brief"], ["Creative Development"], "COMPLETED"),
    ("Creative Development", "Creative Development Agent", ["Research"], ["Production Planning"], "COMPLETED"),
    ("Production Planning", "Production Manager", ["Creative Development"], ["Scheduling", "Asset & Media"], "COMPLETED"),
    ("Scheduling", "Scheduling Agent", ["Production Planning"], ["Clearance & Compliance"], "COMPLETED"),
    ("Asset & Media", "Asset & Media Agent", ["Production Planning"], ["Clearance & Compliance"], "COMPLETED"),
    ("Clearance & Compliance", "Clearance Agent", ["Scheduling", "Asset & Media"], ["Verification QA"], "COMPLETED"),
    ("Verification QA", "Independent QA Agent", ["Clearance & Compliance"], ["Studio Head Decision"], "COMPLETED"),
    ("Studio Head Decision", "Studio Head", ["Verification QA"], ["Final Package"], "COMPLETED"),
    ("Final Package", "Kevaro Delivery Runtime", ["Studio Head Decision"], [], "COMPLETED"),
]

nodes = [
    ProductionGraphNode(
        node_id=name,
        task_name=name,
        responsible_role=role,
        dependencies=dependencies,
        dependents=dependents,
        status=status,
        can_run_in_parallel_with=(
            ["Asset & Media"]
            if name == "Scheduling"
            else ["Scheduling"]
            if name == "Asset & Media"
            else []
        ),
        approval_required=(name == "Studio Head Decision"),
        stale_reason=None,
    )
    for name, role, dependencies, dependents, status in node_specs
]

graph = ProductionGraphState(
    production_name=PRODUCTION,
    nodes=nodes,
    ready_nodes=[],
    running_nodes=[],
    completed_nodes=[node.node_id for node in nodes],
    blocked_nodes=[],
    stale_nodes=[],
    graph_complete=True,
)

snapshot = build_studio_command_snapshot(
    runtime_state=runtime,
    graph_state=graph,
    final_package=None,
)

snapshot["delivery"] = {
    "status": "READY_FOR_DELIVERY",
    "readiness_score": 100,
    "delivery_artifacts": [
        "Hero Campaign Master",
        "Social Cutdowns",
        "Production Evidence Package",
        "Governance & QA Record",
    ],
    "final_notes": [
        "Independent QA passed.",
        "Clearance complete.",
        "Studio Head approval recorded.",
    ],
}

output = Path("frontend/public/studio-snapshot.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(snapshot, indent=2) + "\n")

print(f"JUDGE SNAPSHOT GENERATED: {output}")
print("PRODUCTION:", snapshot["production_name"])
print("STAGE:", snapshot["current_stage"])
print("GRAPH NODES:", len(snapshot["graph"]["nodes"]))
print("DELIVERY:", snapshot["delivery"]["status"])
