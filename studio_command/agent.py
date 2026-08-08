from google.adk.agents import Agent

from .models import ProductionBrief
from .prompts import EXECUTIVE_PRODUCER_INSTRUCTION


executive_producer_agent = Agent(
    name="executive_producer",
    model="gemini-3.5-flash",
    description=(
        "Interprets Studio Head directives and converts them into "
        "structured, production-ready briefs for the autonomous production crew."
    ),
    instruction=EXECUTIVE_PRODUCER_INSTRUCTION,
    output_schema=ProductionBrief,
    output_key="production_brief",
)


root_agent = Agent(
    name="studio_orchestrator",
    model="gemini-3.5-flash",
    description=(
        "The central Kevaro Studio Command orchestrator. "
        "It routes Studio Head production directives to the appropriate specialist agents."
    ),
    instruction="""
You are the Studio Orchestrator for Kevaro Studio Command.

For the current MVP milestone, every new Studio Head production directive
must first be delegated to the Executive Producer Agent.

Do not perform creative development, research, scheduling, asset generation,
compliance review, or QA yourself.

Your job is orchestration, not execution.

Send the directive to the Executive Producer Agent so it can produce the
structured ProductionBrief that becomes the production contract for downstream work.
""",
    sub_agents=[executive_producer_agent],
)
