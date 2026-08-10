from google.adk import Workflow
from google.adk.workflow import JoinNode


def planning():
    return "planning complete"


def scheduling():
    return "scheduling complete"


def asset_media():
    return "asset media complete"


def clearance():
    return "clearance complete"


join = JoinNode(
    name="m20_parallel_planning_join",
    description="Wait for scheduling and asset/media planning branches.",
)

workflow = Workflow(
    name="m20_kevaro_workflow_prototype",
    description=(
        "Milestone 20 isolated modern ADK workflow prototype "
        "for Kevaro Studio Command."
    ),
    edges=[
        (
            "START",
            planning,
            (
                scheduling,
                asset_media,
            ),
            join,
            clearance,
        )
    ],
)

assert workflow.graph is not None

node_names = {
    node.name
    for node in workflow.graph.nodes
}

assert "m20_parallel_planning_join" in node_names

assert len(workflow.graph.nodes) >= 5

print("MILESTONE 20 MODERN WORKFLOW CONSTRUCTION: PASS")
print("Workflow:", workflow.name)
print("Nodes:", sorted(node_names))
print("Edges:", len(workflow.graph.edges))
