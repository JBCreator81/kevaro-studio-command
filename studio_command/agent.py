from google.adk.agents import Agent, SequentialAgent

from .models import ProductionBrief, ResearchPacket
from .prompts import EXECUTIVE_PRODUCER_INSTRUCTION
from .tools import search_web


RESEARCH_AGENT_INSTRUCTION = """
You are the Research Agent for Kevaro Studio Command.

The Executive Producer has already created this ProductionBrief:

{production_brief}

Your job is to investigate the production-relevant research questions in that
brief and return evidence-grounded findings for downstream production decisions.

CORE OPERATING RULES

1. EVIDENCE BEFORE EXECUTION
Never present assumptions as facts.
Use the search_web tool for external evidence.
Clearly distinguish sourced findings from unresolved uncertainty.

2. PRODUCTION RELEVANCE
Research only the questions and evidence needs raised by the ProductionBrief.
Every finding must explain which production decision, deliverable,
constraint, risk, or approval gate it affects.

3. SOURCE QUALITY
Prefer authoritative, primary, reputable, and recent sources where possible.
Do not rely on a single source when the issue materially affects production.

4. UNCERTAINTY
Record meaningful unresolved questions.
If evidence is weak, contradictory, stale, or incomplete, say so explicitly.

5. MINIMAL HUMAN FRICTION
Escalate only when evidence creates a genuine Studio Head decision gate.

Return a structured ResearchPacket.
"""


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


research_agent = Agent(
    name="research_agent",
    model="gemini-3.5-flash",
    description=(
        "Investigates research questions from the ProductionBrief and returns "
        "source-grounded production evidence."
    ),
    instruction=RESEARCH_AGENT_INSTRUCTION,
    tools=[search_web],
    output_schema=ResearchPacket,
    output_key="research_packet",
)


root_agent = SequentialAgent(
    name="studio_orchestrator",
    description=(
        "Kevaro Studio Command production workflow. "
        "Creates the production brief first, then performs evidence research."
    ),
    sub_agents=[
        executive_producer_agent,
        research_agent,
    ],
)
