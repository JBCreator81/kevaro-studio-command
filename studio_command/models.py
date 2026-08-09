from typing import List
from pydantic import BaseModel, Field


class ProductionBrief(BaseModel):
    production_title: str = Field(
        description="A concise working title for the production."
    )

    production_type: str = Field(
        description="The production format, such as commercial, social campaign, short film, trailer, or branded content."
    )

    objective: str = Field(
        description="The primary outcome the Studio Head wants this production to achieve."
    )

    target_audience: str = Field(
        description="The intended audience for the production."
    )

    launch_or_delivery_date: str = Field(
        description="The requested launch, premiere, shoot, or final delivery date. Use 'Not specified' if absent."
    )

    required_deliverables: List[str] = Field(
        description="The concrete production deliverables required to complete the directive."
    )

    creative_constraints: List[str] = Field(
        description="Creative, brand, format, duration, tone, platform, or content constraints."
    )

    production_constraints: List[str] = Field(
        description="Schedule, resource, budget, technical, legal, or operational constraints."
    )

    acceptance_criteria: List[str] = Field(
        description="Measurable conditions that must be true before the production can be considered ready."
    )

    research_questions: List[str] = Field(
        description="Questions that require evidence or external research before execution."
    )

    automatic_work: List[str] = Field(
        description="Low-risk production work that agents may begin without additional Studio Head approval."
    )

    approval_required: List[str] = Field(
        description="Material creative or production decisions that should require Studio Head approval."
    )

    assumptions: List[str] = Field(
        description="Explicit assumptions made because the directive did not provide enough information."
    )

    risks_or_unknowns: List[str] = Field(
        description="Material uncertainties, blockers, or risks that could affect production readiness."
    )


class EvidenceSource(BaseModel):
    title: str = Field(
        description="Human-readable title or name of the evidence source."
    )

    url: str = Field(
        description="Canonical source URL when available."
    )

    publisher_or_domain: str = Field(
        description="Publisher, organization, platform, or domain responsible for the source."
    )

    evidence_summary: str = Field(
        description="Concise summary of the evidence relevant to the production question."
    )

    production_relevance: str = Field(
        description="Why this evidence matters to a production decision, deliverable, constraint, or risk."
    )

    confidence: str = Field(
        description="Evidence confidence classification: high, medium, or low."
    )


class ResearchEvidence(BaseModel):
    research_question: str = Field(
        description="The exact production research question being investigated."
    )

    finding: str = Field(
        description="Evidence-grounded answer to the research question."
    )

    sources: List[EvidenceSource] = Field(
        description="Sources supporting the finding."
    )

    production_impact: str = Field(
        description="What production decision or workstream this finding should affect."
    )

    unresolved_questions: List[str] = Field(
        description="Important uncertainties that remain after research."
    )

    requires_studio_head_decision: bool = Field(
        description="Whether the evidence creates or materially affects a Studio Head approval gate."
    )


class ResearchPacket(BaseModel):
    evidence: List[ResearchEvidence] = Field(
        description="Evidence records produced for the Production Brief research questions."
    )

    overall_summary: str = Field(
        description="Executive summary of the research for the production team."
    )

    blockers: List[str] = Field(
        description="Evidence-related blockers that could prevent production work from proceeding safely."
    )


class CreativeConcept(BaseModel):
    concept_name: str = Field(
        description="Short working name for the creative concept."
    )

    core_idea: str = Field(
        description="The central creative idea and audience-facing proposition."
    )

    emotional_target: str = Field(
        description="The primary emotional response the concept is designed to create."
    )

    visual_direction: str = Field(
        description="Overall visual language, composition, texture, lighting, palette, and cinematic direction."
    )

    narrative_arc: List[str] = Field(
        description="Ordered narrative beats from opening through final payoff."
    )

    key_messages: List[str] = Field(
        description="Messages the audience should understand or feel after viewing."
    )

    evidence_used: List[str] = Field(
        description="Research findings that materially influenced this concept."
    )

    production_requirements: List[str] = Field(
        description="Assets, talent, locations, footage, graphics, audio, or production elements required."
    )

    risks_or_tradeoffs: List[str] = Field(
        description="Creative or production risks, compromises, or dependencies associated with this concept."
    )


class CreativeTreatment(BaseModel):
    recommended_concept: CreativeConcept = Field(
        description="The strongest creative concept recommended for production."
    )

    alternate_concepts: List[CreativeConcept] = Field(
        description="Viable alternate concepts that remain materially different from the recommended direction."
    )

    script_direction: str = Field(
        description="High-level script and voiceover direction without pretending the final script is already approved."
    )

    visual_system: List[str] = Field(
        description="Core visual rules that should remain consistent across the production."
    )

    audio_direction: str = Field(
        description="Music, sound design, pacing, voice, and sonic identity guidance."
    )

    mandatory_elements: List[str] = Field(
        description="Production Brief requirements and evidence-backed elements that must be preserved."
    )

    studio_head_approvals: List[str] = Field(
        description="Material creative decisions requiring Studio Head approval before downstream production."
    )

    unresolved_creative_questions: List[str] = Field(
        description="Creative uncertainties that still need resolution."
    )


class ProductionTask(BaseModel):
    task_name: str = Field(
        description="Clear executable production task."
    )

    responsible_role: str = Field(
        description="Agent or production role responsible for completing the task."
    )

    deliverable: str = Field(
        description="Concrete output expected from this task."
    )

    dependencies: List[str] = Field(
        description="Tasks, approvals, assets, evidence, or decisions required before this task can proceed."
    )

    completion_criteria: List[str] = Field(
        description="Objective conditions that define successful completion."
    )

    approval_required: bool = Field(
        description="Whether this task requires Studio Head approval before downstream work proceeds."
    )

    risk_notes: List[str] = Field(
        description="Known execution risks or scheduling concerns for this task."
    )


class ProductionPlan(BaseModel):
    production_name: str = Field(
        description="Production being planned."
    )

    execution_summary: str = Field(
        description="Concise explanation of how the production will be executed."
    )

    tasks: List[ProductionTask] = Field(
        description="Ordered production tasks required to complete the project."
    )

    critical_path: List[str] = Field(
        description="Tasks and dependencies that directly control the delivery date."
    )

    parallel_workstreams: List[List[str]] = Field(
        description="Groups of tasks that may safely proceed in parallel."
    )

    milestones: List[str] = Field(
        description="Major production checkpoints from creative approval through final delivery."
    )

    approval_gates: List[str] = Field(
        description="Material decisions that require Studio Head approval."
    )

    blockers: List[str] = Field(
        description="Known blockers preventing or threatening execution."
    )

    schedule_risks: List[str] = Field(
        description="Timing risks that could affect the promised delivery date."
    )

    next_actions: List[str] = Field(
        description="Immediate executable actions the autonomous production crew should take next."
    )


class ScheduledTask(BaseModel):
    task_name: str = Field(
        description="Production task being scheduled."
    )

    responsible_role: str = Field(
        description="Agent or production role responsible for the task."
    )

    sequence_position: int = Field(
        description="Relative execution position within the production schedule."
    )

    depends_on: List[str] = Field(
        description="Tasks or approval gates that must be completed first."
    )

    can_run_in_parallel_with: List[str] = Field(
        description="Other tasks that may safely execute at the same time."
    )

    target_window: str = Field(
        description="Planned execution window relative to the production deadline."
    )

    completion_gate: str = Field(
        description="Evidence or condition required before this task is considered complete."
    )


class ProductionSchedule(BaseModel):
    production_name: str = Field(
        description="Production associated with this schedule."
    )

    delivery_target: str = Field(
        description="Requested or inferred final delivery target."
    )

    scheduled_tasks: List[ScheduledTask] = Field(
        description="Dependency-aware execution schedule."
    )

    critical_path: List[str] = Field(
        description="Ordered tasks controlling the final delivery date."
    )

    parallel_execution_groups: List[List[str]] = Field(
        description="Tasks grouped for safe parallel execution."
    )

    approval_windows: List[str] = Field(
        description="Studio Head approval points and when they must occur."
    )

    schedule_buffer: List[str] = Field(
        description="Available timing buffers or explicitly identified lack of buffer."
    )

    deadline_threats: List[str] = Field(
        description="Conditions that could cause the delivery deadline to slip."
    )

    immediate_schedule_actions: List[str] = Field(
        description="Scheduling actions that can begin immediately."
    )


class MediaAssetRequirement(BaseModel):
    asset_name: str = Field(
        description="Clear name for the required production asset."
    )

    asset_type: str = Field(
        description="Type of asset such as video, image, audio, voiceover, graphic, logo, animation, or document."
    )

    purpose: str = Field(
        description="Why this asset is required and where it supports the production."
    )

    source_strategy: str = Field(
        description="Whether the asset should be generated, sourced, supplied by the client, licensed, or created internally."
    )

    required_specifications: List[str] = Field(
        description="Technical, creative, format, resolution, duration, aspect ratio, or quality requirements."
    )

    dependencies: List[str] = Field(
        description="Approvals, creative decisions, brand materials, research, or other assets required first."
    )

    licensing_or_rights: List[str] = Field(
        description="Usage rights, attribution, licensing, release, or ownership requirements."
    )

    approval_required: bool = Field(
        description="Whether Studio Head approval is required before the asset may be used downstream."
    )

    readiness_status: str = Field(
        description="Current readiness classification such as ready, blocked, awaiting approval, awaiting source, or requires generation."
    )


class AssetMediaPlan(BaseModel):
    production_name: str = Field(
        description="Production associated with this asset plan."
    )

    asset_requirements: List[MediaAssetRequirement] = Field(
        description="All material media and production assets required for execution."
    )

    immediately_actionable_assets: List[str] = Field(
        description="Assets that can be sourced, prepared, generated, or requested immediately."
    )

    blocked_assets: List[str] = Field(
        description="Assets currently prevented from progressing and why."
    )

    client_supplied_assets: List[str] = Field(
        description="Assets that must be supplied by the client or Studio Head."
    )

    generation_candidates: List[str] = Field(
        description="Assets suitable for automated or AI-assisted generation."
    )

    licensed_asset_needs: List[str] = Field(
        description="Assets that require commercial licensing, releases, or rights clearance."
    )

    format_matrix: List[str] = Field(
        description="Required output formats, aspect ratios, resolutions, durations, or delivery variants."
    )

    asset_risks: List[str] = Field(
        description="Asset-related risks that may affect quality, legality, schedule, or delivery."
    )

    next_asset_actions: List[str] = Field(
        description="Immediate asset and media actions the production crew should execute next."
    )


class ComplianceCheck(BaseModel):
    check_name: str = Field(
        description="Specific legal, rights, brand, platform, or compliance check."
    )

    category: str = Field(
        description="Compliance category such as licensing, copyright, trademark, claims, release, brand, platform, accessibility, or privacy."
    )

    applies_to: List[str] = Field(
        description="Assets, claims, deliverables, channels, or production elements affected by this check."
    )

    status: str = Field(
        description="Current status such as clear, blocked, requires evidence, requires approval, or unresolved."
    )

    evidence_required: List[str] = Field(
        description="Documents, licenses, releases, source evidence, approvals, or confirmations required to clear this check."
    )

    blocking_issue: str = Field(
        description="Material issue preventing clearance, or 'none' when no blocker exists."
    )

    approval_required: bool = Field(
        description="Whether Studio Head or authorized human approval is required."
    )


class ClearanceComplianceReport(BaseModel):
    production_name: str = Field(
        description="Production being reviewed."
    )

    compliance_checks: List[ComplianceCheck] = Field(
        description="Structured clearance and compliance checks for the production."
    )

    cleared_items: List[str] = Field(
        description="Items presently supported for production use."
    )

    blocked_items: List[str] = Field(
        description="Items that must not proceed until cleared."
    )

    unresolved_questions: List[str] = Field(
        description="Material compliance uncertainties still requiring evidence or decision."
    )

    required_documents: List[str] = Field(
        description="Licenses, releases, approvals, records, or other documentation required."
    )

    claim_restrictions: List[str] = Field(
        description="Statements or representations that should be avoided, qualified, or substantiated."
    )

    distribution_constraints: List[str] = Field(
        description="Platform, territory, format, accessibility, privacy, or usage restrictions affecting delivery."
    )

    clearance_risks: List[str] = Field(
        description="Remaining legal, rights, brand, platform, or reputational risks."
    )

    clearance_decision: str = Field(
        description="Overall result such as CLEAR TO PROCEED, CONDITIONAL, or BLOCKED."
    )

    next_clearance_actions: List[str] = Field(
        description="Immediate actions required to reach production clearance."
    )


class VerificationFinding(BaseModel):
    finding_name: str = Field(
        description="Specific verification or QA finding."
    )

    category: str = Field(
        description="Area being checked such as evidence, consistency, schedule, asset, compliance, technical, creative, or completeness."
    )

    severity: str = Field(
        description="Severity such as info, warning, major, or critical."
    )

    status: str = Field(
        description="Result such as passed, failed, unresolved, or requires review."
    )

    affected_items: List[str] = Field(
        description="Production artifacts, tasks, assets, claims, or decisions affected by this finding."
    )

    evidence: List[str] = Field(
        description="Evidence or artifact references supporting the finding."
    )

    remediation: str = Field(
        description="Required corrective action, or 'none' when no correction is needed."
    )


class VerificationQAReport(BaseModel):
    production_name: str = Field(
        description="Production being verified."
    )

    findings: List[VerificationFinding] = Field(
        description="Structured verification and QA findings."
    )

    passed_checks: List[str] = Field(
        description="Checks that successfully passed."
    )

    failed_checks: List[str] = Field(
        description="Checks that failed and require correction."
    )

    unresolved_items: List[str] = Field(
        description="Items that cannot yet be verified because evidence, approval, or information is missing."
    )

    cross_artifact_conflicts: List[str] = Field(
        description="Contradictions or mismatches between production artifacts."
    )

    technical_validation: List[str] = Field(
        description="Technical delivery, format, schedule, asset, or production validations."
    )

    evidence_validation: List[str] = Field(
        description="Checks confirming whether material claims and decisions are supported by evidence."
    )

    readiness_score: int = Field(
        ge=0,
        le=100,
        description="Overall production readiness score from 0 to 100."
    )

    qa_decision: str = Field(
        description="Overall QA result such as PASS, CONDITIONAL PASS, or FAIL."
    )

    next_qa_actions: List[str] = Field(
        description="Immediate corrective or verification actions required next."
    )


class StudioHeadDecisionItem(BaseModel):
    item_name: str = Field(
        description="Specific decision item requiring Studio Head attention."
    )

    category: str = Field(
        description="Decision category such as creative, budget, schedule, compliance, asset, technical, risk, or delivery."
    )

    recommendation: str = Field(
        description="System recommendation based on the completed production evidence."
    )

    rationale: str = Field(
        description="Concise evidence-based rationale supporting the recommendation."
    )

    risk_if_approved: str = Field(
        description="Material risk if this item is approved in its current state."
    )

    risk_if_delayed: str = Field(
        description="Material consequence of delaying the decision."
    )

    requires_human_decision: bool = Field(
        description="Whether this item must be explicitly decided by the Studio Head."
    )


class StudioHeadDecisionPackage(BaseModel):
    production_name: str = Field(
        description="Production presented to the Studio Head."
    )

    executive_summary: str = Field(
        description="Concise final summary of the production package and current state."
    )

    qa_decision: str = Field(
        description="Final QA decision inherited from the Verification & QA stage."
    )

    readiness_score: int = Field(
        ge=0,
        le=100,
        description="Verified production readiness score."
    )

    clearance_status: str = Field(
        description="Current clearance and compliance status."
    )

    decision_items: List[StudioHeadDecisionItem] = Field(
        description="Items that require Studio Head judgment or acknowledgement."
    )

    material_blockers: List[str] = Field(
        description="Issues that prevent unconditional approval."
    )

    conditions_for_approval: List[str] = Field(
        description="Conditions that must be satisfied for approval or conditional approval."
    )

    recommended_decision: str = Field(
        description="System recommendation such as APPROVE, APPROVE WITH CONDITIONS, REQUEST CHANGES, or REJECT."
    )

    decision_options: List[str] = Field(
        description="Permitted Studio Head decisions."
    )

    final_warning: str = Field(
        description="Most important unresolved risk or 'none' if no material warning remains."
    )


class StudioHeadDecisionRecord(BaseModel):
    production_name: str = Field(
        description="Production receiving the Studio Head's human decision."
    )

    decision: str = Field(
        description="Human-selected decision: APPROVE, APPROVE WITH CONDITIONS, REQUEST CHANGES, or REJECT."
    )

    conditions: List[str] = Field(
        description="Conditions explicitly attached by the Studio Head. Empty when none apply."
    )

    decision_notes: str = Field(
        description="Optional Studio Head rationale, direction, or notes attached to the decision."
    )

    decided_by: str = Field(
        description="Human authority who made the decision. Must identify the Studio Head and never an autonomous agent."
    )

    source_recommendation: str = Field(
        description="System recommendation presented before the human decision was made."
    )

    recommendation_followed: bool = Field(
        description="Whether the Studio Head's human decision matched the system recommendation."
    )

    unresolved_risks_acknowledged: List[str] = Field(
        description="Material unresolved risks explicitly acknowledged as part of the human decision."
    )

    next_action: str = Field(
        description="Required workflow action resulting from this decision."
    )


class ProductionWorkflowState(BaseModel):
    production_name: str = Field(
        description="Production whose post-decision workflow state is being tracked."
    )

    status: str = Field(
        description="Current production state: APPROVED, APPROVED_WITH_CONDITIONS, CHANGES_REQUESTED, or REJECTED."
    )

    active_conditions: List[str] = Field(
        description="Human-approved conditions that remain active for this production."
    )

    corrective_action_required: bool = Field(
        description="Whether the production must return for corrective work."
    )

    production_may_advance: bool = Field(
        description="Whether downstream production execution may proceed."
    )

    production_stopped: bool = Field(
        description="Whether the current production path has been stopped."
    )

    next_stage: str = Field(
        description="Deterministic next workflow stage resulting from the Studio Head decision."
    )


class ProductionDecisionHistoryEntry(BaseModel):
    sequence: int = Field(
        description="Monotonic sequence number for this production decision event."
    )

    production_name: str = Field(
        description="Production associated with this decision-history entry."
    )

    decision: str = Field(
        description="Human Studio Head decision recorded for this event."
    )

    decided_by: str = Field(
        description="Human Studio Head identity responsible for the decision."
    )

    source_recommendation: str = Field(
        description="System recommendation presented before the human decision."
    )

    recommendation_followed: bool = Field(
        description="Whether the human decision matched the system recommendation."
    )

    resulting_status: str = Field(
        description="Production workflow status resulting from the human decision."
    )

    next_stage: str = Field(
        description="Deterministic workflow stage entered after this decision."
    )

    production_may_advance: bool = Field(
        description="Whether production may advance after this decision."
    )

    corrective_action_required: bool = Field(
        description="Whether corrective work is required after this decision."
    )

    production_stopped: bool = Field(
        description="Whether the production path was stopped by this decision."
    )

    active_conditions: List[str] = Field(
        description="Conditions remaining active after this decision."
    )

    unresolved_risks_acknowledged: List[str] = Field(
        description="Material unresolved risks acknowledged by the Studio Head."
    )

    decision_notes: str = Field(
        description="Human notes or rationale attached to this decision."
    )
