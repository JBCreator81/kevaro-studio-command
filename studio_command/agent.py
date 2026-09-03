from collections.abc import Mapping

from google.adk.workflow import FunctionNode
from google.adk.events import Event
from google.adk.agents import Agent, SequentialAgent
from google.adk import Workflow
from google.adk.workflow import JoinNode

from .models import (
    ProductionBrief,
    ResearchPacket,
    CreativeTreatment,
    ProductionPlan,
    ProductionSchedule,
    AssetMediaPlan,
    ClearanceComplianceReport,
    VerificationQAReport,
    StudioHeadDecisionPackage,
)
from .prompts import EXECUTIVE_PRODUCER_INSTRUCTION
from .tools import search_web
from .identity import require_production_identity
from .persistence import ProductionPersistence
from .accountability import add_pending_accountability


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
Copy the tool's Parallel provenance object exactly into parallel_provenance.
Preserve exact URLs and citation IDs, and link findings with source_reference_ids.
Never invent a URL, citation, timestamp, provider field, or retrieval metadata.

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
Aggregate remaining gaps in evidence_gaps.

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


PRODUCTION_MANAGER_INSTRUCTION = """
You are the Production Manager Agent for Kevaro Studio Command.

You receive these completed upstream artifacts:

PRODUCTION BRIEF:
{production_brief}

RESEARCH PACKET:
{research_packet}

CREATIVE TREATMENT:
{creative_treatment}

Convert them into an executable, dependency-aware production plan.

OPERATING RULES

1. Every task must produce a concrete deliverable or unblock downstream work.

2. CANONICAL TASK DEPENDENCIES
First define all tasks with unique task_name values. Treat those exact task_name
strings as the complete closed set of canonical task identities. Only after that,
select each dependencies entry verbatim from that set. Every dependency must
exactly match the task_name of another task in this same ProductionPlan.

Never combine two task names into one dependency. Never comma-join dependencies.
Never paraphrase, shorten, rename, or semantically approximate a task name. Never
use a workflow-stage name, artifact name, approval, evidence item, asset, decision,
or invented name unless it is itself the exact task_name of another ProductionTask
in this plan. For multiple prerequisites, emit multiple dependency list entries,
one exact canonical task_name per entry. A task with no production-task prerequisite
must use an empty dependencies list. If no exact canonical match exists, do not
guess or repair the text; expose the issue as a blocker instead.

3. GRAPH, NOT CHAIN
Group work that can safely happen at the same time into parallel workstreams.

4. Identify the critical path controlling the delivery date.

5. Preserve all Studio Head approval gates.

6. Assign each task to the appropriate specialist role or agent.

7. Every task must have objective completion criteria.

8. Separate current blockers from possible schedule risks.

9. next_actions must contain work the autonomous production crew can begin immediately.

Return a structured ProductionPlan.
"""


SCHEDULING_AGENT_INSTRUCTION = """
You are the Scheduling Agent for Kevaro Studio Command.

You receive the completed ProductionPlan:

{production_plan}

Your job is to convert that plan into a dependency-aware execution schedule.

CORE OPERATING RULES

CANONICAL TASK IDENTITY — NON-NEGOTIABLE
The ProductionPlan is the authoritative definition of the work to be scheduled.

- Every ProductionPlan task must appear exactly once in scheduled_tasks.
- Every scheduled task must correspond to exactly one ProductionPlan task.
- Preserve each task_name verbatim from ProductionPlan.tasks.
- Do not invent, rename, omit, merge, split, replace, or reinterpret plan tasks.
- Scheduling may add timing, sequencing, dependency, parallelism, approval-window,
  buffer, critical-path, risk, and completion-gate information around those tasks,
  but it must not change the identity of the work itself.
- If ProductionPlan.tasks is empty, scheduled_tasks must also be empty. Do not
  manufacture work to make the schedule appear complete.
- If the ProductionPlan cannot be scheduled as written, expose the conflict as a
  blocker or schedule risk rather than silently modifying the plan.

1. DEPENDENCIES FIRST
Never schedule a task before its true dependencies or approval gates are satisfied.
Every depends_on value must exactly match a task_name present in
ProductionPlan.tasks. Do not use upstream workflow artifact or stage labels such
as Production Brief as scheduled-task dependencies.

2. GRAPH, NOT CHAIN
Preserve legitimate parallel workstreams.
Do not force everything into a single sequence.

3. DEADLINE PROTECTION
Identify the critical path and anything threatening the requested delivery date.

4. APPROVAL WINDOWS
Studio Head approval gates must appear at the correct point in the schedule.

5. NO INVENTED DATES
If an exact date or duration is not known, use a clear relative execution window
instead of fabricating calendar precision.

6. BUFFER VISIBILITY
Show where schedule buffer exists and where there is none.

7. COMPLETION GATES
Each scheduled task must have a clear condition that allows downstream work to begin.

8. IMMEDIATE ACTIONABILITY
Identify scheduling actions that can begin now.

Return a structured ProductionSchedule.
"""


ASSET_MEDIA_AGENT_INSTRUCTION = """
You are the Asset & Media Agent for Kevaro Studio Command.

You receive the completed upstream artifacts:

PRODUCTION BRIEF:
{production_brief}

CREATIVE TREATMENT:
{creative_treatment}

PRODUCTION PLAN:
{production_plan}

Your job is to convert these into a complete, production-ready asset and media plan.

CORE OPERATING RULES

1. ASSET NECESSITY
Only require assets that materially support the approved production.

2. SOURCE STRATEGY
Classify each asset as generated, sourced, client-supplied, licensed, or internally created.

3. TECHNICAL SPECIFICITY
Capture relevant format, aspect ratio, resolution, duration, quality, and delivery requirements.

4. RIGHTS BEFORE USE
Never treat stock, music, voiceover, logos, likenesses, footage, or third-party materials as cleared unless rights are known.

5. DEPENDENCY AWARENESS
Respect creative approvals, brand materials, schedule gates, and upstream dependencies.

6. GENERATION READINESS
Identify which assets are suitable for automated or AI-assisted generation, but do not generate them yet.

7. BLOCKER VISIBILITY
Clearly identify assets blocked by missing approvals, brand materials, licensing, or source availability.

8. IMMEDIATE ACTIONABILITY
Identify asset work that can begin now without violating approval or licensing gates.

Return a structured AssetMediaPlan.
"""


CLEARANCE_COMPLIANCE_AGENT_INSTRUCTION = """
You are the Clearance & Compliance Agent for Kevaro Studio Command.

You receive the completed upstream artifacts:

PRODUCTION BRIEF:
{production_brief}

RESEARCH PACKET:
{research_packet}

CREATIVE TREATMENT:
{creative_treatment}

PRODUCTION PLAN:
{production_plan}

PRODUCTION SCHEDULE:
{production_schedule}

ASSET MEDIA PLAN:
{asset_media_plan}

Your job is to determine whether the production is legally, commercially,
platform-wise, and brand-wise clear to proceed.

CORE OPERATING RULES

1. EVIDENCE BEFORE CLEARANCE
Never mark an item clear without supporting evidence, license, approval,
release, ownership record, or sufficiently reliable source basis.

2. RIGHTS AND LICENSING
Check stock, music, footage, voiceover, logos, trademarks, likenesses,
third-party creative material, and distribution rights.

3. CLAIMS AND REPRESENTATIONS
Flag health, wellness, performance, financial, comparative, scientific,
or other potentially regulated or substantiation-sensitive claims.

4. BRAND AND CLIENT APPROVAL
Identify missing brand guidelines, logos, copy approvals, identity standards,
or other client-controlled materials.

5. PLATFORM AND DISTRIBUTION
Identify relevant format, accessibility, territory, privacy, disclosure,
or platform restrictions affecting delivery.

6. DO NOT INVENT LEGAL CERTAINTY
Where the evidence is incomplete or jurisdiction-dependent, classify the issue
as unresolved or conditional rather than pretending it is legally clear.

7. BLOCK UNSAFE DOWNSTREAM EXECUTION
Any unresolved issue that could create material legal, rights, platform,
brand, or reputational exposure must remain blocked.

8. ACTIONABLE CLEARANCE
Every blocked or conditional item must state what evidence, approval,
document, or decision is needed next.

Return a structured ClearanceComplianceReport.
"""


VERIFICATION_QA_AGENT_INSTRUCTION = """
You are the Verification & QA Agent for Kevaro Studio Command.

You receive all completed upstream production artifacts:

PRODUCTION BRIEF:
{production_brief}

RESEARCH PACKET:
{research_packet}

CREATIVE TREATMENT:
{creative_treatment}

PRODUCTION PLAN:
{production_plan}

PRODUCTION SCHEDULE:
{production_schedule}

ASSET MEDIA PLAN:
{asset_media_plan}

CLEARANCE COMPLIANCE REPORT:
{clearance_compliance_report}

Your job is to independently verify whether the production package is
internally consistent, evidence-supported, technically coherent, complete,
and ready for Studio Head review.

CORE OPERATING RULES

1. VERIFY, DO NOT CREATE
Do not invent new creative direction or production requirements.
Evaluate the work already produced.

2. CROSS-ARTIFACT CONSISTENCY
Compare all artifacts for contradictions in scope, concept, assets,
schedule, format, approvals, rights, and delivery requirements.

3. EVIDENCE VALIDATION
Material claims, research conclusions, and compliance decisions must be
traceable to evidence or explicitly classified as unresolved.

4. TECHNICAL VALIDATION
Check output formats, aspect ratios, resolutions, durations, audio standards,
dependencies, deadlines, approval gates, and delivery assumptions.

5. BLOCKER INTEGRITY
Do not pass work that remains blocked by unresolved rights, licensing,
brand approvals, missing evidence, or material dependencies.

6. SEVERITY DISCIPLINE
Classify findings proportionately as info, warning, major, or critical.

7. READINESS SCORE
Score readiness from 0 to 100 based on the actual state of the production,
not optimism.

8. QA DECISION
Use PASS only when there are no material unresolved blockers.
Use CONDITIONAL PASS when the package is substantially sound but specific
items still require resolution.
Use FAIL when material contradictions, missing evidence, technical defects,
or unresolved blockers prevent safe production progression.

9. ACTIONABLE REMEDIATION
Every failed or unresolved finding must identify what must happen next.

Return a structured VerificationQAReport.
"""


STUDIO_HEAD_DECISION_GATE_INSTRUCTION = """
You are the Studio Head Decision Gate for Kevaro Studio Command.

You receive the completed upstream production package:

PRODUCTION BRIEF:
{production_brief}

RESEARCH PACKET:
{research_packet}

CREATIVE TREATMENT:
{creative_treatment}

PRODUCTION PLAN:
{production_plan}

PRODUCTION SCHEDULE:
{production_schedule}

ASSET MEDIA PLAN:
{asset_media_plan}

CLEARANCE COMPLIANCE REPORT:
{clearance_compliance_report}

VERIFICATION QA REPORT:
{verification_qa_report}

Your responsibility is to prepare the final decision package for the human
Studio Head.

You do NOT make or impersonate the Studio Head's final approval.

CORE OPERATING RULES

1. HUMAN AUTHORITY BOUNDARY
Never claim that the Studio Head approved, rejected, or accepted anything.
You may recommend a decision, but the actual decision remains human.

2. EVIDENCE-BASED SUMMARY
Summarize the production based only on the completed upstream artifacts.

3. RESPECT QA AND CLEARANCE
Carry forward material blockers, unresolved issues, readiness score,
clearance status, and QA decision accurately.

4. DO NOT HIDE RISK
If QA failed or clearance remains conditional or blocked, state that clearly.

5. DECISION COMPRESSION AND AUTHORITY CALIBRATION
Escalate only decisions that materially require human Studio Head judgment.

A Studio Head decision is appropriate when it involves one or more of:
- a material change to approved creative direction, brand identity, scope, or deliverables;
- a meaningful budget, schedule, quality, or resource tradeoff;
- legal, rights, licensing, compliance, safety, or reputational risk requiring human acceptance;
- an unresolved contradiction between evidence, agents, or governing requirements;
- an irreversible or high-impact production commitment;
- a final approval gate explicitly reserved to the human Studio Head.

DO NOT escalate routine specialist execution choices when evidence supports a safe decision
and the choice does not materially change approved creative intent, scope, budget, schedule,
quality threshold, legal exposure, or delivery requirements.

Routine specialist decisions include, when adequately supported:
- codec, bitrate, export, file-size, and encoding targets;
- platform-safe transcoding and technical delivery defaults;
- ordinary formatting and specification choices;
- routine production sequencing and operational implementation;
- non-material asset refinement or technical workflow choices.

For routine specialist decisions:
- the responsible agent decides autonomously;
- record the rationale and supporting evidence;
- continue execution without creating a Studio Head gate.

Do not reopen a decision already explicitly supplied or approved in the production directive
unless new evidence creates a material conflict or risk.

When the directive establishes a technical hierarchy or fallback, specialists must resolve
implementation within that authority without escalation. For example, a 24 fps cinematic
master plus platform-safe adaptations authorizes the technical specialist to select supported
platform delivery settings, transcoding, resolution, bitrate, file size, and frame-rate
adaptations using verified evidence. Phrases such as "where practical" do not create a Studio
Head gate unless the specialist choice would materially change creative intent, scope, budget,
schedule, quality threshold, legal exposure, or an explicit delivery requirement.

Only place an item in the Studio Head decisions list when requires_human_decision is genuinely true
after applying this authority test. The decisions list may be empty when no additional human
judgment is required.

6. APPROVAL LOGIC
Recommended decisions are limited to:
- APPROVE
- APPROVE WITH CONDITIONS
- REQUEST CHANGES
- REJECT

Do not recommend APPROVE when material blockers remain unresolved.

7. DECISION OPTIONS
Always provide the Studio Head with the permitted human decision options.

8. FINAL WARNING
Surface the single most important unresolved risk, or 'none' if no material
risk remains.

9. DATE INTEGRITY
Never invent or infer an absolute calendar date from a relative deadline.
If an upstream artifact says 'next Friday', preserve the wording 'next Friday'
unless an explicit calendar date was supplied in the production directive or
verified upstream evidence.
Never introduce historical or unsupported dates.

Return a structured StudioHeadDecisionPackage.
"""


executive_producer_agent = Agent(
    mode="single_turn",
    name="executive_producer",
    model="gemini-2.5-flash",
    description=(
        "Interprets Studio Head directives and converts them into "
        "structured, production-ready briefs for the autonomous production crew."
    ),
    instruction=EXECUTIVE_PRODUCER_INSTRUCTION,
    output_schema=ProductionBrief,
    output_key="production_brief",
)


research_agent = Agent(
    mode="single_turn",
    name="research_agent",
    model="gemini-2.5-flash",
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
    mode="single_turn",
    name="creative_development_agent",
    model="gemini-2.5-flash",
    description=(
        "Transforms the ProductionBrief and ResearchPacket into a structured, "
        "evidence-grounded creative treatment."
    ),
    instruction=CREATIVE_DEVELOPMENT_INSTRUCTION,
    output_schema=CreativeTreatment,
    output_key="creative_treatment",
)


production_manager_agent = Agent(
    mode="single_turn",
    name="production_manager_agent",
    model="gemini-2.5-flash",
    description=(
        "Converts the production brief, research, and creative treatment "
        "into an executable production plan."
    ),
    instruction=PRODUCTION_MANAGER_INSTRUCTION,
    output_schema=ProductionPlan,
    output_key="production_plan",
)


scheduling_agent = Agent(
    mode="single_turn",
    name="scheduling_agent",
    model="gemini-2.5-flash",
    description=(
        "Transforms the ProductionPlan into a dependency-aware schedule "
        "with parallel workstreams, approval windows, critical path, and deadline risks."
    ),
    instruction=SCHEDULING_AGENT_INSTRUCTION,
    output_schema=ProductionSchedule,
    output_key="production_schedule",
)


asset_media_agent = Agent(
    mode="single_turn",
    name="asset_media_agent",
    model="gemini-2.5-flash",
    description=(
        "Builds the production asset and media plan, including sourcing strategy, "
        "technical requirements, rights, blockers, and generation candidates."
    ),
    instruction=ASSET_MEDIA_AGENT_INSTRUCTION,
    output_schema=AssetMediaPlan,
    output_key="asset_media_plan",
)


clearance_compliance_agent = Agent(
    mode="single_turn",
    name="clearance_compliance_agent",
    model="gemini-2.5-flash",
    description=(
        "Reviews production assets, claims, rights, brand requirements, "
        "platform constraints, and evidence to determine clearance status."
    ),
    instruction=CLEARANCE_COMPLIANCE_AGENT_INSTRUCTION,
    output_schema=ClearanceComplianceReport,
    output_key="clearance_compliance_report",
)


verification_qa_agent = Agent(
    mode="single_turn",
    name="verification_qa_agent",
    model="gemini-2.5-flash",
    description=(
        "Independently verifies the complete production package for consistency, "
        "evidence support, technical validity, completeness, and readiness."
    ),
    instruction=VERIFICATION_QA_AGENT_INSTRUCTION,
    output_schema=VerificationQAReport,
    output_key="verification_qa_report",
)


studio_head_decision_gate = Agent(
    mode="single_turn",
    name="studio_head_decision_gate",
    model="gemini-2.5-flash",
    description=(
        "Prepares the final evidence-based decision package for the human Studio Head "
        "without impersonating or replacing human approval authority."
    ),
    instruction=STUDIO_HEAD_DECISION_GATE_INSTRUCTION,
    output_schema=StudioHeadDecisionPackage,
    output_key="studio_head_decision_package",
)


legacy_root_agent = SequentialAgent(
    name="studio_orchestrator",
    description=(
        "Kevaro Studio Command autonomous production workflow. "
        "Transforms a Studio Head directive through executive production, evidence research, "
        "creative development, production planning, scheduling, asset and media planning, "
        "clearance and compliance, independent QA, and human decision preparation."
    ),
    sub_agents=[
        executive_producer_agent,
        research_agent,
        creative_development_agent,
        production_manager_agent,
        scheduling_agent,
        asset_media_agent,
        clearance_compliance_agent,
        verification_qa_agent,
        studio_head_decision_gate,
    ],
)


def _serialize_research_handoff(ctx, node_input):
    """Keep typed research internally and emit JSON-safe workflow state."""
    value = ctx.state.get("research_packet")
    if value is None:
        value = node_input
    research_packet = ResearchPacket.model_validate(value)
    serialized = research_packet.model_dump(mode="json")
    ctx.state["research_packet"] = serialized
    return serialized


serialize_research_handoff = FunctionNode(
    name="serialize_research_handoff",
    func=_serialize_research_handoff,
)


production_planning_join = JoinNode(
    name="production_planning_join",
    description=(
        "Wait for scheduling and asset/media planning to complete "
        "before clearance, compliance, and downstream verification."
    ),
)


def _merge_parallel_planning_state(ctx, node_input):
    """Promote joined parallel planning outputs into shared workflow state."""

    schedule_branch = node_input["scheduling_agent"]
    asset_branch = node_input["asset_media_agent"]

    if (
        isinstance(schedule_branch, dict)
        and "production_schedule" in schedule_branch
    ):
        production_schedule = schedule_branch["production_schedule"]
    else:
        production_schedule = schedule_branch

    if (
        isinstance(asset_branch, dict)
        and "asset_media_plan" in asset_branch
    ):
        asset_media_plan = asset_branch["asset_media_plan"]
    else:
        asset_media_plan = asset_branch

    ctx.state["production_schedule"] = production_schedule
    ctx.state["asset_media_plan"] = asset_media_plan

    return {
        "production_schedule": production_schedule,
        "asset_media_plan": asset_media_plan,
    }


production_planning_merge = FunctionNode(
    name="production_planning_merge",
    func=_merge_parallel_planning_state,
)



production_persistence = ProductionPersistence()

_PENDING_REVIEW_KEYS = (
    "production_brief",
    "research_packet",
    "creative_treatment",
    "production_plan",
    "production_schedule",
    "asset_media_plan",
    "clearance_compliance_report",
    "verification_qa_report",
    "studio_head_decision_package",
)


def _govern_research_packet(
    research_packet,
    parallel_search_result=None,
    *,
    parallel_search_calls=None,
    research_run_id=None,
    production_name=None,
):
    """Bind every research citation to an ordered captured Parallel call."""
    packet = _review_value(research_packet)
    if not isinstance(packet, dict):
        raise ValueError("Research packet must be a structured object.")

    calls = list(parallel_search_calls or [])
    if not calls and isinstance(parallel_search_result, dict):
        calls = [{
            "function_call_id": None,
            "research_run_id": research_run_id,
            "result": parallel_search_result,
        }]
    if not calls:
        packet["parallel_provenance"] = None
        packet["parallel_search_calls"] = []
        return packet

    retained_calls = []
    by_citation = {}
    for call_index, call in enumerate(calls, start=1):
        if not isinstance(call, dict):
            raise ValueError("Parallel call history contains an invalid record.")
        call_run_id = call.get("research_run_id")
        if research_run_id and call_run_id != research_run_id:
            raise ValueError(
                "Parallel call belongs to a different governed research run."
            )
        call_production = call.get("production_identity")
        if (
            production_name and call_production
            and call_production != production_name
        ):
            raise ValueError(
                "Parallel call belongs to a different production."
            )
        result = call.get("result")
        provenance = result.get("provenance") if isinstance(result, dict) else None
        results = result.get("results") if isinstance(result, dict) else None
        if not isinstance(provenance, dict) or not isinstance(results, list):
            raise ValueError("Parallel call history lacks structured provenance.")
        retained_calls.append({
            "call_index": call_index,
            "research_run_id": call_run_id,
            "production_identity": production_name,
            "function_call_id": call.get("function_call_id"),
            "provenance": provenance,
            "results": results,
        })
        for item in results:
            if not isinstance(item, dict) or not item.get("citation_id"):
                continue
            citation_id = item["citation_id"]
            prior = by_citation.get(citation_id)
            if prior and prior[0] != item:
                raise ValueError(
                    f"Parallel citation identifier is ambiguous: {citation_id}."
                )
            by_citation[citation_id] = (item, provenance, call_index)

    for evidence in packet.get("evidence") or []:
        if not isinstance(evidence, dict):
            raise ValueError("Research evidence must be a structured object.")
        for source in evidence.get("sources") or []:
            if not isinstance(source, dict):
                raise ValueError("Research source must be a structured object.")
            citation_id = source.get("citation_id")
            captured = by_citation.get(citation_id)
            if captured is None:
                raise ValueError(
                    "Research source is not present in any captured Parallel call: "
                    f"{citation_id or 'missing citation identifier'}"
                )
            captured, provenance, call_index = captured
            if provenance.get("verification_status") != "VERIFIED":
                raise ValueError(
                    f"Research citation {citation_id} lacks verified provenance."
                )
            if source.get("url") != captured.get("url"):
                raise ValueError(
                    f"Research source URL does not match captured citation {citation_id}."
                )
            source.update({
                "title": captured.get("title"),
                "url": captured.get("url"),
                "publisher_or_domain": captured.get("source"),
                "citation_id": captured.get("citation_id"),
                "excerpts": captured.get("excerpts") or [],
                "publish_date": captured.get("publish_date"),
                "provider": provenance.get("provider"),
            })
            retrieval_metadata = {
                **(source.get("retrieval_metadata") or {}),
                "parallel_call_index": call_index,
            }
            if provenance.get("search_id"):
                retrieval_metadata["parallel_search_id"] = provenance["search_id"]
            source["retrieval_metadata"] = retrieval_metadata

    packet["parallel_provenance"] = retained_calls[-1]["provenance"]
    packet["parallel_search_calls"] = (
        retained_calls if production_name else []
    )
    return packet


def _validate_review_bundle_graph(review_bundle):
    from .graph import build_production_graph

    plan = ProductionPlan.model_validate(review_bundle["production_plan"])
    schedule = ProductionSchedule.model_validate(
        review_bundle["production_schedule"]
    )
    build_production_graph(
        production_plan=plan,
        production_schedule=schedule,
    )


def _review_value(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _project_governed_state(state, *, keys=(), prefixes=()):
    """Read an allowlisted projection from ADK State or a plain mapping."""
    to_dict = getattr(state, "to_dict", None)
    if callable(to_dict):
        snapshot = to_dict()
    elif isinstance(state, Mapping):
        snapshot = state
    else:
        snapshot = {
            key: state[key]
            for key in keys
            if key in state
        }
    projected = {
        key: snapshot[key]
        for key in keys
        if key in snapshot
    }
    if prefixes:
        projected.update({
            key: value
            for key, value in snapshot.items()
            if any(key.startswith(prefix) for prefix in prefixes)
        })
    return projected


def _persist_pending_review_bundle(ctx, node_input):
    review_bundle = _project_governed_state(
        ctx.state,
        keys=_PENDING_REVIEW_KEYS,
    )

    for key in _PENDING_REVIEW_KEYS:
        value = review_bundle.get(key)

        if value is None:
            raise ValueError(
                f"Cannot persist Studio Head review bundle. Missing workflow state: {key}"
            )

        review_bundle[key] = _review_value(review_bundle[key])

    review_bundle = add_pending_accountability(review_bundle)
    decision_package = review_bundle["studio_head_decision_package"]
    production_name = decision_package.get("production_name")

    if not production_name:
        raise ValueError(
            "Studio Head decision package does not contain a production name."
        )

    production_name = require_production_identity(
        production_name,
        review_bundle["production_plan"]["production_name"],
        review_bundle["production_schedule"]["production_name"],
    )

    parallel_state = _project_governed_state(
        ctx.state,
        keys=("parallel_search_result",),
        prefixes=("parallel_search_call:",),
    )
    parallel_search_calls = [
        value
        for key, value in parallel_state.items()
        if key.startswith("parallel_search_call:")
    ]
    review_bundle["research_packet"] = _govern_research_packet(
        review_bundle["research_packet"],
        parallel_state.get("parallel_search_result"),
        parallel_search_calls=parallel_search_calls,
        research_run_id=ctx.invocation_id,
        production_name=production_name,
    )

    _validate_review_bundle_graph(review_bundle)
    production_persistence.save_pending_review_bundle(
        production_name=production_name,
        review_bundle=review_bundle,
    )

    ctx.state["pending_review_persisted"] = True

    return {
        "production_name": production_name,
        "pending_review_persisted": True,
    }


persist_pending_review = FunctionNode(
    name="persist_pending_review",
    func=_persist_pending_review_bundle,
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
            serialize_research_handoff,
            creative_development_agent,
            production_manager_agent,
            (
                scheduling_agent,
                asset_media_agent,
            ),
            production_planning_join,
            production_planning_merge,
            clearance_compliance_agent,
            verification_qa_agent,
            studio_head_decision_gate,
            persist_pending_review,
        )
    ],
)

# Production entry point.
root_agent = studio_production_workflow
