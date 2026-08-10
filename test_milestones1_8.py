from studio_command.agent import (
    root_agent,
    studio_production_workflow,
    executive_producer_agent,
    research_agent,
    creative_development_agent,
    production_manager_agent,
    scheduling_agent,
    asset_media_agent,
    clearance_compliance_agent,
    verification_qa_agent,
)

from studio_command.models import (
    ProductionBrief,
    ResearchPacket,
    CreativeTreatment,
    ProductionPlan,
    ProductionSchedule,
    AssetMediaPlan,
    ClearanceComplianceReport,
    VerificationQAReport,
)


assert root_agent is studio_production_workflow
assert type(root_agent).__name__ == "Workflow"


node_names = {
    getattr(node, "name", str(node))
    for node in studio_production_workflow.graph.nodes
}


checks = [
    (
        1,
        executive_producer_agent,
        "executive_producer",
        "production_brief",
        ProductionBrief,
        "ROOT ORCHESTRATOR AND EXECUTIVE PRODUCER",
    ),
    (
        2,
        research_agent,
        "research_agent",
        "research_packet",
        ResearchPacket,
        "RESEARCH WORKFLOW",
    ),
    (
        3,
        creative_development_agent,
        "creative_development_agent",
        "creative_treatment",
        CreativeTreatment,
        "CREATIVE DEVELOPMENT WORKFLOW",
    ),
    (
        4,
        production_manager_agent,
        "production_manager_agent",
        "production_plan",
        ProductionPlan,
        "PRODUCTION MANAGER WORKFLOW",
    ),
    (
        5,
        scheduling_agent,
        "scheduling_agent",
        "production_schedule",
        ProductionSchedule,
        "SCHEDULING WORKFLOW",
    ),
    (
        6,
        asset_media_agent,
        "asset_media_agent",
        "asset_media_plan",
        AssetMediaPlan,
        "ASSET MEDIA WORKFLOW",
    ),
    (
        7,
        clearance_compliance_agent,
        "clearance_compliance_agent",
        "clearance_compliance_report",
        ClearanceComplianceReport,
        "CLEARANCE COMPLIANCE WORKFLOW",
    ),
    (
        8,
        verification_qa_agent,
        "verification_qa_agent",
        "verification_qa_report",
        VerificationQAReport,
        "VERIFICATION QA WORKFLOW",
    ),
]


for (
    milestone,
    agent,
    expected_name,
    expected_output_key,
    expected_schema,
    label,
) in checks:
    assert agent.name == expected_name
    assert agent.output_key == expected_output_key
    assert agent.output_schema is expected_schema
    assert expected_name in node_names

    print(
        f"MILESTONE {milestone} {label} VALIDATION: PASS"
    )


# Verify the foundational agents are connected in the current production graph.
routes = {
    (
        getattr(edge.from_node, "name", str(edge.from_node)),
        getattr(edge.to_node, "name", str(edge.to_node)),
    )
    for edge in studio_production_workflow.graph.edges
}

required_routes = {
    ("executive_producer", "research_agent"),
    ("research_agent", "creative_development_agent"),
    ("creative_development_agent", "production_manager_agent"),
    ("production_manager_agent", "scheduling_agent"),
    ("production_manager_agent", "asset_media_agent"),
    ("clearance_compliance_agent", "verification_qa_agent"),
}

missing_routes = required_routes - routes

assert not missing_routes, (
    f"Missing foundational workflow routes: {sorted(missing_routes)}"
)

print("MILESTONES 1-8 CURRENT GRAPH INTEGRATION: PASS")
