from google.adk import Workflow
from google.adk.workflow import JoinNode

from .agent import (
    executive_producer_agent,
    research_agent,
    creative_development_agent,
    production_manager_agent,
    scheduling_agent,
    asset_media_agent,
    clearance_compliance_agent,
    verification_qa_agent,
    studio_head_decision_gate,
)


production_planning_join = JoinNode(
    name="production_planning_join",
    description=(
        "Wait for scheduling and asset/media planning to complete "
        "before clearance, compliance, and downstream verification."
    ),
)


studio_production_workflow = Workflow(
    name="kevaro_studio_production_workflow",
    description=(
        "Modern graph-based Kevaro Studio Command production workflow. "
        "Coordinates governed production stages, parallel planning, "
        "independent QA, and human Studio Head decision preparation."
    ),
    edges=[
        (
            "START",
            executive_producer_agent,
            research_agent,
            creative_development_agent,
            production_manager_agent,
            (
                scheduling_agent,
                asset_media_agent,
            ),
            production_planning_join,
            clearance_compliance_agent,
            verification_qa_agent,
            studio_head_decision_gate,
        )
    ],
)
