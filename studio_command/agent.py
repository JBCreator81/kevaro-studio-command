from google.adk.agents import Agent, SequentialAgent

from .models import (
    ProductionBrief,
    ResearchPacket,
    CreativeTreatment,
)
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


CREATIVE_DEVELOPMENT_INSTRUCTION = """
You are the Creative Development Agent for Kevaro Studio Command.

You receive two completed upstream production artifacts.

PRODUCTION BRIEF:

{production_brief}

RESEARCH PACKET:

{research_packet}

Your job is to convert the approved production intent and evidence into a
clear, production-ready creative direction.

CORE OPERATING RULES

1. BRIEF FIDELITY
Do not change the objective, target audience, required deliverables,
constraints, acceptance criteria, or mandatory Studio Head approvals.

2. EVIDENCE-GROUNDED CREATIVITY
Use relevant findings from the ResearchPacket to strengthen creative choices.
Do not invent market facts, legal requirements, trends, or audience claims.

3. DISTINCT CREATIVE OPTIONS
Produce one recommended concept and viable alternate concepts.
Alternates must be materially different creative directions, not minor rewrites.

4. PRODUCTION REALISM
Concepts must respect timing, format, budget assumptions, platform requirements,
available assets, and known production risks.

5. APPROVAL GOVERNANCE
Do not treat material creative choices as approved merely because you generated them.
Clearly identify decisions requiring Studio Head approval.

6. NO PREMATURE EXECUTION
Do not generate final production assets.
Do not pretend the final script, edit, casting, music, or visual lock is approved.

Return a structured CreativeTreatment.
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


creative_development_agent = Agent(
    name="creative_development_agent",
    model="gemini-3.5-flash",
    description=(
        "Transforms the ProductionBrief and ResearchPacket into a structured, "
        "evidence-grounded creative treatment."
    ),
    instruction=CREATIVE_DEVELOPMENT_INSTRUCTION,
    output_schema=CreativeTreatment,
    output_key="creative_treatment",
)


root_agent = SequentialAgent(
    name="studio_orchestrator",
    description=(
        "Kevaro Studio Command production workflow. "
        "Creates the brief, performs evidence research, then develops the creative treatment."
    ),
    sub_agents=[
        executive_producer_agent,
        research_agent,
        creative_development_agent,
    ],
)
