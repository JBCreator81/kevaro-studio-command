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
