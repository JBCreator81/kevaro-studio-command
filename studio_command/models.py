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
