from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .decisions import evidence_amendment_stale_artifacts
from .identity import require_production_identity
from .models import (
    AccountabilityActor, EvidenceSourceReference, GovernedCreativeDirective,
    GovernedEvidenceAmendment, GovernedFirstPartyDeclaration,
    GovernedProductionRuntimeState,
)

CANONICAL_CONCEPT = "Symphony of Serenity"
CONFLICTING_CONCEPT = "Everyday Glow"
BRAND = "Missing Client/Studio Head Input: Detailed Brand Guidelines"
UPLOAD = "Missing Client/Studio Head Input: Content Upload Methods"
BUDGET = "Missing Client/Studio Head Input: Detailed Budget Constraints"
PROP = "Missing Client/Studio Head Input: Product Usage Permission (for prop)"
LICENSING = "Unresolved Licensing for Key Assets (Talent, Locations, Music, Fonts, SFX)"
RESOLVABLE = (BRAND, UPLOAD, BUDGET)
CREATIVE_STALE = [
    "creative_treatment", "production_plan", "production_schedule",
    "asset_media_plan", "clearance_report", "verification_report",
    "decision_package",
]
DECLARATIONS: dict[str, dict[str, Any]] = {
    BRAND: {
        "positioning": "Fictional premium luxury-wellness retreat",
        "concept": CANONICAL_CONCEPT,
        "tone": ["calm", "refined", "cinematic", "restrained"],
        "claim_rule": "No medical, therapeutic, guaranteed-outcome, unsupported scientific, or comparative claims.",
        "asset_rule": "Use only confirmed client-owned fictional Aurelian assets.",
        "ai_rule": "AI visuals require generation provenance and source-material review.",
        "unsupported_exclusions": ["trademark status", "exclusive palette", "logo geometry"],
    },
    UPLOAD: {
        "deliverables": ["Instagram Reels 9:16", "YouTube Shorts 9:16", "16:9 master"],
        "source_master": "24fps; 4K where practical",
        "handoff": "Governed delivery location with immutable version, checksums, captions, clearance manifest, and production notes.",
        "publishing_boundary": "Client-designated operator uses client-controlled publishing tools; Kevaro does not possess client credentials.",
    },
    BUDGET: {
        "currency": "CAD", "total": 12000, "classification": "Planned approved internal allocation; not invoices or proof of spend.",
        "allocations": {
            "Creative direction and production design": 1200,
            "Storyboard and previsualization": 800,
            "Original or verified-AI visuals": 2600,
            "Editing, motion, colour, and mastering": 2500,
            "Original music": 1200,
            "Original sound design and mix": 800,
            "Captions, adaptations, and technical QA": 1000,
            "Clearance and provenance documentation": 700,
            "Studio Head-controlled contingency": 1200,
        },
    },
}

def apply_first_party_adoption(*, runtime_state: GovernedProductionRuntimeState, actor: AccountabilityActor, adopted_at: datetime | None = None) -> GovernedProductionRuntimeState:
    require_production_identity(runtime_state.production_name)
    if actor.actor_type != "HUMAN" or actor.role != "Studio Head":
        raise ValueError("First-party adoption requires authenticated Studio Head authority.")
    if runtime_state.memory_snapshot.stale_artifacts:
        raise ValueError("Adoption requires a current governed production state.")
    for condition in RESOLVABLE:
        if condition not in runtime_state.workflow_state.active_conditions:
            raise ValueError("First-party adoption condition is not exactly active.")
    now = adopted_at or datetime.now(timezone.utc)
    directive = GovernedCreativeDirective(
        production_name=runtime_state.production_name, canonical_concept=CANONICAL_CONCEPT,
        conflicting_concept=CONFLICTING_CONCEPT, stale_artifacts=CREATIVE_STALE,
        directed_by=actor, directed_at=now,
    )
    declarations=[]; amendments=[]
    for condition in RESOLVABLE:
        declaration=GovernedFirstPartyDeclaration(
            production_name=runtime_state.production_name,
            declaration_type={BRAND:"BRAND_GUIDELINES",UPLOAD:"DELIVERY_WORKFLOW",BUDGET:"BUDGET_ALLOCATION"}[condition],
            resolved_condition=condition, declaration=DECLARATIONS[condition],
            adopted_by=actor, adopted_at=now,
        ); declarations.append(declaration)
        amendments.append(GovernedEvidenceAmendment(
            production_name=runtime_state.production_name, resolved_condition=condition,
            resolution_summary=f"Authenticated Studio Head adopted {declaration.declaration_type} first-party production evidence.",
            amended_artifact="creative_treatment" if condition==BRAND else "production_plan",
            source_references=[EvidenceSourceReference(
                source_production_name=runtime_state.production_name,
                artifact_key="first_party_declarations", field_path=[len(runtime_state.first_party_declarations)+len(declarations)-1,"declaration"],
                verified_value=declaration.declaration,
            )], stale_artifacts=CREATIVE_STALE, recorded_by=actor, recorded_at=now,
        ))
    remaining=[c for c in runtime_state.workflow_state.active_conditions if c not in RESOLVABLE]
    workflow=runtime_state.workflow_state.model_copy(update={"active_conditions":remaining})
    memory=runtime_state.memory_snapshot.model_copy(update={
        "active_conditions":remaining, "stale_artifacts":CREATIVE_STALE,
        "preserved_artifacts":[x for x in runtime_state.memory_snapshot.preserved_artifacts if x not in CREATIVE_STALE],
        "current_stage":"EVIDENCE_REFRESH_REQUIRED",
    })
    return runtime_state.model_copy(update={
        "workflow_state":workflow, "memory_snapshot":memory,
        "creative_directives":[*runtime_state.creative_directives,directive],
        "first_party_declarations":[*runtime_state.first_party_declarations,*declarations],
        "evidence_amendments":[*runtime_state.evidence_amendments,*amendments],
        "execution_authorized":False,"corrective_cycle_active":True,"current_stage":"EVIDENCE_REFRESH_REQUIRED",
    })
