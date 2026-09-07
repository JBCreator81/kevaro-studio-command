from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .accountability import ai_actor
from .graph import build_production_graph
from .identity import require_production_identity
from .models import (
    AssetMediaPlan, ClearanceComplianceReport, CreativeTreatment,
    GovernedArtifactRefresh, GovernedProductionRuntimeState, ProductionPlan,
    ProductionSchedule, ResearchPacket, StudioHeadDecisionPackage,
    VerificationQAReport,
)

PLATFORM_CONDITION = "Missing Client/Studio Head Input: Specific Target Social Media Platforms"
PLATFORM_VALUES = ("Instagram Reels", "YouTube Shorts", "16:9")
REFRESH_ORDER = (
    "research_packet", "creative_treatment", "production_plan",
    "production_schedule", "asset_media_plan", "clearance_report",
    "verification_report", "decision_package",
)
ARTIFACT_MODELS = {
    "research_packet": ResearchPacket,
    "creative_treatment": CreativeTreatment,
    "production_plan": ProductionPlan,
    "production_schedule": ProductionSchedule,
    "asset_media_plan": AssetMediaPlan,
    "clearance_report": ClearanceComplianceReport,
    "verification_report": VerificationQAReport,
    "decision_package": StudioHeadDecisionPackage,
}


def _drop_matching(values: list[Any], phrase: str) -> list[Any]:
    return [value for value in values if phrase.lower() not in str(value).lower()]


def _replace_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    replacements = {
        "specific target social media platforms, detailed brand guidelines": "detailed brand guidelines",
        "target social media platforms, detailed brand guidelines": "detailed brand guidelines",
        "specific information from the client/Studio Head. These include: specific target social media platforms, detailed brand guidelines": "specific information from the client/Studio Head. These include: detailed brand guidelines",
        "target social media platforms, detailed brand guidelines": "detailed brand guidelines",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _walk_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _walk_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_walk_text(item) for item in value]
    return _replace_text(value)


def rebuild_platform_amendment_artifacts(
    *, runtime_state: GovernedProductionRuntimeState,
    approved_artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Refresh the exact stale graph closure for the verified Aurelian amendment."""
    require_production_identity(runtime_state.production_name)
    if not runtime_state.evidence_amendments:
        raise ValueError("Selective rebuild requires a governed evidence amendment.")
    amendment = runtime_state.evidence_amendments[-1]
    if amendment.resolved_condition != PLATFORM_CONDITION:
        raise ValueError("No registered selective reconciler matches the evidence amendment.")
    if amendment.stale_artifacts != list(REFRESH_ORDER):
        raise ValueError("Stale artifacts do not match the governed graph closure exactly.")
    if runtime_state.memory_snapshot.stale_artifacts != list(REFRESH_ORDER):
        raise ValueError("Runtime stale state changed after the evidence amendment.")
    values = [ref.verified_value for ref in amendment.source_references]
    evidence_text = " ".join(str(value) for value in values)
    if not all(value in evidence_text for value in PLATFORM_VALUES):
        raise ValueError("Verified platform evidence is materially insufficient.")
    missing = [key for key in REFRESH_ORDER if key not in approved_artifacts]
    if missing:
        raise ValueError(f"Selective rebuild source bundle is incomplete: {missing}")

    rebuilt = {key: deepcopy(approved_artifacts[key]) for key in REFRESH_ORDER}
    rebuilt["research_packet"]["evidence"] = [
        {**item, "unresolved_questions": _drop_matching(item.get("unresolved_questions", []), "target social media platforms")}
        for item in rebuilt["research_packet"].get("evidence", [])
    ]
    rebuilt["creative_treatment"]["unresolved_creative_questions"] = _drop_matching(
        rebuilt["creative_treatment"].get("unresolved_creative_questions", []), "target social media platforms"
    )
    rebuilt["production_plan"]["blockers"] = _drop_matching(
        rebuilt["production_plan"].get("blockers", []), "target social media platforms"
    )
    rebuilt["production_schedule"]["deadline_threats"] = _drop_matching(
        rebuilt["production_schedule"].get("deadline_threats", []), "target social media platforms"
    )

    clearance = rebuilt["clearance_report"]
    clearance["blocked_items"] = _drop_matching(clearance.get("blocked_items", []), "specific target social media platforms")
    clearance["unresolved_questions"] = _drop_matching(clearance.get("unresolved_questions", []), "target social media platforms")
    clearance["required_documents"] = _drop_matching(clearance.get("required_documents", []), "target social media platforms")
    clearance.setdefault("cleared_items", []).append(
        "Distribution targets verified from governed evidence: Instagram Reels, YouTube Shorts, and 16:9 delivery."
    )
    for check in clearance.get("compliance_checks", []):
        if check.get("check_name") == "Target Social Media Platforms & Upload Methods":
            check["evidence_required"] = _drop_matching(check.get("evidence_required", []), "target social media platforms")
            check["blocking_issue"] = "Content upload methods are not yet specified, which impacts final export and asset-management workflow."
            check["status"] = "blocked"

    qa = rebuilt["verification_report"]
    qa["findings"] = [item for item in qa.get("findings", []) if item.get("finding_name") != PLATFORM_CONDITION]
    qa["failed_checks"] = [item for item in qa.get("failed_checks", []) if item != f"Project Blocked by {PLATFORM_CONDITION}"]
    qa["unresolved_items"] = _drop_matching(qa.get("unresolved_items", []), "target social media platforms")
    qa["next_qa_actions"] = _walk_text(qa.get("next_qa_actions", []))
    qa["qa_decision"] = "FAIL"

    decision = _walk_text(rebuilt["decision_package"])
    decision["material_blockers"] = list(runtime_state.workflow_state.active_conditions)
    decision["conditions_for_approval"] = _drop_matching(decision.get("conditions_for_approval", []), "target social media platforms")
    decision["qa_decision"] = qa["qa_decision"]
    decision["readiness_score"] = qa["readiness_score"]
    decision["clearance_status"] = clearance["clearance_decision"]
    rebuilt["decision_package"] = decision

    for key, model in ARTIFACT_MODELS.items():
        artifact = model.model_validate(rebuilt[key])
        if hasattr(artifact, "production_name"):
            require_production_identity(runtime_state.production_name, artifact.production_name)
    build_production_graph(
        production_plan=ProductionPlan.model_validate(rebuilt["production_plan"]),
        production_schedule=ProductionSchedule.model_validate(rebuilt["production_schedule"]),
    )
    if rebuilt["decision_package"]["material_blockers"] != runtime_state.workflow_state.active_conditions:
        raise ValueError("Refreshed decision package did not preserve exact active conditions.")
    return rebuilt


def rebuild_first_party_adoption_artifacts(
    *, runtime_state: GovernedProductionRuntimeState, approved_artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Consume the latest creative directive and adopted declarations."""
    if not runtime_state.creative_directives or len(runtime_state.first_party_declarations) < 3:
        raise ValueError("Selective rebuild requires governed creative and declaration evidence.")
    directive = runtime_state.creative_directives[-1]
    if directive.canonical_concept != "Symphony of Serenity" or directive.conflicting_concept != "Everyday Glow":
        raise ValueError("Creative directive does not match the registered reconciliation.")
    if runtime_state.memory_snapshot.stale_artifacts != directive.stale_artifacts:
        raise ValueError("Runtime stale state does not match the creative directive closure.")
    rebuilt = {key: deepcopy(approved_artifacts[key]) for key in directive.stale_artifacts}
    creative = rebuilt["creative_treatment"]
    concept = creative["recommended_concept"]
    concept["concept_name"] = "Symphony of Serenity"
    concept["core_idea"] = "A calm, refined cinematic progression through the fictional Aurelian Renewal Retreat, using atmosphere, hospitality, and quiet sensory detail without medical or outcome claims."
    creative["unresolved_creative_questions"] = _drop_matching(creative.get("unresolved_creative_questions", []), "brand guidelines")

    renames = {
        "Request Specific Social Media Platforms from Client/SH": "Apply Confirmed Platform Delivery Targets",
        "Obtain Detailed Brand Guidelines from Client/SH": "Apply Adopted Aurelian Brand Guidelines",
        "Clarify Content Upload Methods with Client/SH": "Apply Adopted Delivery Workflow",
    }
    def rename(value: Any) -> Any:
        if isinstance(value, dict): return {k: rename(v) for k, v in value.items()}
        if isinstance(value, list): return [rename(v) for v in value]
        if isinstance(value, str):
            for old, new in renames.items(): value = value.replace(old, new)
        return value
    rebuilt["production_plan"] = rename(rebuilt["production_plan"])
    rebuilt["production_schedule"] = rename(rebuilt["production_schedule"])
    for phrase in ("brand guidelines", "content upload methods", "detailed budget"):
        rebuilt["production_plan"]["blockers"] = _drop_matching(rebuilt["production_plan"].get("blockers", []), phrase)
        rebuilt["production_schedule"]["deadline_threats"] = _drop_matching(rebuilt["production_schedule"].get("deadline_threats", []), phrase)
    assets = rebuilt["asset_media_plan"]
    assets["client_supplied_assets"] = _drop_matching(assets.get("client_supplied_assets", []), "brand guidelines")
    assets["blocked_assets"] = _drop_matching(assets.get("blocked_assets", []), "brand guidelines")

    clearance = rebuilt["clearance_report"]
    for field in ("blocked_items", "unresolved_questions", "required_documents", "clearance_risks"):
        values=clearance.get(field, [])
        for phrase in ("brand guidelines", "content upload methods", "detailed budget"):
            values=_drop_matching(values,phrase)
        clearance[field]=values
    clearance.setdefault("cleared_items", []).extend([
        "Authenticated Aurelian brand declaration", "Adopted production delivery workflow",
        "Adopted CAD 12,000 internal budget allocation",
    ])
    clearance["clearance_decision"]="BLOCKED"

    qa=rebuilt["verification_report"]
    resolved=set(item.resolved_condition for item in runtime_state.first_party_declarations[-3:])
    qa["findings"]=[x for x in qa.get("findings",[]) if x.get("finding_name") not in resolved]
    qa["failed_checks"]=[x for x in qa.get("failed_checks",[]) if not any(condition in x for condition in resolved)]
    for phrase in ("brand guidelines", "content upload methods", "detailed budget"):
        qa["unresolved_items"]=_drop_matching(qa.get("unresolved_items",[]),phrase)
    qa["qa_decision"]="FAIL"

    decision=rebuilt["decision_package"]
    decision["material_blockers"]=list(runtime_state.workflow_state.active_conditions)
    decision["conditions_for_approval"]=list(runtime_state.workflow_state.active_conditions)
    decision["qa_decision"]="FAIL"; decision["clearance_status"]="BLOCKED"
    for key, model in ARTIFACT_MODELS.items():
        if key in rebuilt:
            artifact=model.model_validate(rebuilt[key])
            if hasattr(artifact,"production_name"): require_production_identity(runtime_state.production_name,artifact.production_name)
    build_production_graph(production_plan=ProductionPlan.model_validate(rebuilt["production_plan"]),production_schedule=ProductionSchedule.model_validate(rebuilt["production_schedule"]))
    return rebuilt


def rebuild_final_evidence_artifacts(
    *, runtime_state: GovernedProductionRuntimeState, approved_artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Refresh asset evidence while retaining final-content clearance gates."""
    from .adoption import LICENSING, PROP
    from .closure import FINAL_STALE, PROP_NAME
    if runtime_state.workflow_state.active_conditions:
        raise ValueError("Final evidence rebuild requires zero active evidence conditions.")
    if runtime_state.memory_snapshot.stale_artifacts != FINAL_STALE:
        raise ValueError("Final evidence stale closure does not match exactly.")
    if [x.resolved_condition for x in runtime_state.evidence_amendments[-2:]] != [PROP, LICENSING]:
        raise ValueError("Final evidence amendments are missing or out of order.")
    rebuilt={key:deepcopy(approved_artifacts[key]) for key in FINAL_STALE}
    assets=_walk_text(rebuilt["asset_media_plan"])
    assets["client_supplied_assets"]=[PROP_NAME+" (fictional client-owned Aurelian prop)"]
    drop=("Talent Visuals","Filming Locations","Music Tracks","Sound Effects","Voiceover Script","On-Screen Text","Premium Brand Product")
    assets["blocked_assets"]=[x for x in assets.get("blocked_assets",[]) if not any(p.lower() in str(x).lower() for p in drop)]
    assets["licensed_asset_needs"]=[]
    assets["asset_risks"]=[x for x in assets.get("asset_risks",[]) if not any(p in str(x).lower() for p in ("licensed music","budget constraints","brand guidelines"))]
    for item in assets.get("asset_requirements",[]):
        name=item.get("asset_name","")
        if "Talent Visuals" in name:
            item.update(source_strategy="Not used — no identifiable person",readiness_status="Ready",licensing_or_rights=["No talent asset; introducing an identifiable person reopens the talent gate."])
        elif "Filming Locations" in name:
            item.update(source_strategy="Original generated fictional environments",readiness_status="Ready",licensing_or_rights=["Two generated environment files with prompt and checksum provenance."])
        elif "Music Tracks" in name:
            item.update(source_strategy="Original deterministic procedural synthesis",readiness_status="Ready",licensing_or_rights=["Production-specific WAV and reproducible source; no recordings or samples."])
        elif "Sound Effects" in name:
            item.update(source_strategy="Original deterministic procedural synthesis",readiness_status="Ready",licensing_or_rights=["Production-specific WAV and reproducible source; no external library."])
        elif "On-Screen Text" in name:
            item.update(source_strategy="Noto Sans pinned package",readiness_status="Ready",licensing_or_rights=["Exact font checksum and bundled OFL-1.1 text."])
        elif "Premium Brand Product" in name:
            item["asset_name"]=PROP_NAME; item.update(source_strategy="Client-owned fictional first-party asset",readiness_status="Ready",licensing_or_rights=["Authenticated Studio Head limited-use authorization for this production."])
    rebuilt["asset_media_plan"]=assets
    clearance=rebuilt["clearance_report"]
    clear_names={"Brand Guidelines Compliance","Target Social Media Platforms & Upload Methods","Talent Releases (Likeness)","Filming Location Permits/Agreements","Music Licensing","Sound Effects (SFX) Licensing","Font Licensing (On-Screen Text)","Product Usage Permission (Prop)"}
    for check in clearance.get("compliance_checks",[]):
        if check.get("check_name") in clear_names:
            check["status"]="cleared"; check["blocking_issue"]="none"
            check["evidence_required"]=["Satisfied by governed first-party declaration or verified production asset provenance."]
    clearance["cleared_items"]=list(dict.fromkeys([*clearance.get("cleared_items",[]),"Aurelian Renewal Serum limited first-party prop authorization","No identifiable talent; generated fictional environments","Production-specific original procedural score and SFX with checksums","Pinned Noto Sans package with bundled OFL-1.1"]));
    clearance["blocked_items"]=["Final edited video deliverables","Final claims, captions, safe-zone and technical-content verification","Formal Clearance/Compliance Review"]
    clearance["required_documents"]=["Final deliverable technical QA record","Formal clearance sign-off on final edited content"]
    clearance["unresolved_questions"]=[]
    clearance["clearance_risks"]=["Final edited content has not been registered and therefore claims, captions, safe zones, duration, audio mix, and export conformance cannot yet be verified."]
    clearance["next_clearance_actions"]=["Register final edited deliverables, verify claims/captions/safe zones/technical conformance, then complete formal clearance sign-off."]
    clearance["clearance_decision"]="BLOCKED"
    qa=rebuilt["verification_report"]
    qa["findings"]=[x for x in qa.get("findings",[]) if x.get("finding_name") not in {"Missing Client/Studio Head Input: Product Usage Permission","Licensing Blockers for Talent, Locations, Music, Fonts, SFX"}]
    qa["failed_checks"]=["Final edited deliverables are not registered for content-level clearance and independent QA"]
    qa["unresolved_items"]=["Final video claims review","Caption synchronization and accuracy","Platform safe-zone and export verification","Formal clearance sign-off"]
    qa["next_qa_actions"]=["After final edited deliverables are registered and clearance is current, independently verify duration, formats, captions, safe zones, audio mix, claims, checksums, and playback."]
    qa["passed_checks"]=list(dict.fromkeys([*qa.get("passed_checks",[]),"Exact Prop Identity and First-Party Authorization","Talent and Location Rights-Avoiding Sourcing","Original Score and SFX Provenance","Noto Sans OFL-1.1 Licence Package"]))
    qa["qa_decision"]="FAIL"; qa["readiness_score"]=70
    decision=rebuilt["decision_package"]
    delivery_gates=["Final edited deliverables not registered","Formal clearance on final content pending","Independent final-content QA pending"]
    decision["material_blockers"]=delivery_gates; decision["conditions_for_approval"]=delivery_gates
    decision["clearance_status"]="BLOCKED"; decision["qa_decision"]="FAIL"; decision["readiness_score"]=70
    decision["recommended_decision"]="REQUEST CHANGES"
    decision["final_warning"]="Evidence conditions are resolved, but final edited deliverables require formal clearance and independent content-level QA before delivery."
    decision["executive_summary"]="The canonical Symphony of Serenity evidence and rights package is current. Final video deliverables remain unregistered, so clearance and independent QA correctly remain blocked."
    for key,model in ARTIFACT_MODELS.items():
        if key in rebuilt:
            artifact=model.model_validate(rebuilt[key])
            if hasattr(artifact,"production_name"): require_production_identity(runtime_state.production_name,artifact.production_name)
    return rebuilt


def rebuild_stale_artifacts(*, runtime_state: GovernedProductionRuntimeState, approved_artifacts: dict[str, Any]) -> dict[str, Any]:
    from .closure import FINAL_STALE
    if runtime_state.memory_snapshot.stale_artifacts == FINAL_STALE and not runtime_state.workflow_state.active_conditions:
        return rebuild_final_evidence_artifacts(runtime_state=runtime_state, approved_artifacts=approved_artifacts)
    if runtime_state.creative_directives and runtime_state.memory_snapshot.stale_artifacts == runtime_state.creative_directives[-1].stale_artifacts:
        return rebuild_first_party_adoption_artifacts(runtime_state=runtime_state, approved_artifacts=approved_artifacts)
    return rebuild_platform_amendment_artifacts(runtime_state=runtime_state, approved_artifacts=approved_artifacts)


def apply_selective_refresh(
    *, runtime_state: GovernedProductionRuntimeState,
    rebuilt_artifacts: dict[str, Any],
    approved_artifacts: dict[str, Any],
    refreshed_at: datetime | None = None,
) -> tuple[GovernedProductionRuntimeState, dict[str, Any]]:
    stale = runtime_state.memory_snapshot.stale_artifacts
    if list(rebuilt_artifacts) != stale:
        raise ValueError("Rebuild must supply every stale artifact in exact graph order.")
    if set(rebuilt_artifacts) & set(runtime_state.memory_snapshot.preserved_artifacts):
        raise ValueError("Selective rebuild cannot overwrite preserved artifacts.")
    merged = deepcopy(approved_artifacts)
    merged.update(deepcopy(rebuilt_artifacts))
    preserved = list(dict.fromkeys([*runtime_state.memory_snapshot.preserved_artifacts, *stale]))
    event = GovernedArtifactRefresh(
        production_name=runtime_state.production_name,
        source_amendment_index=len(runtime_state.evidence_amendments) - 1,
        rebuilt_artifacts=stale,
        preserved_artifacts=runtime_state.memory_snapshot.preserved_artifacts,
        active_conditions=runtime_state.workflow_state.active_conditions,
        refreshed_by=ai_actor("governed_selective_rebuild", "Production Orchestrator"),
        refreshed_at=refreshed_at or datetime.now(timezone.utc),
    )
    next_stage = "CONDITIONS_BLOCK_EXECUTION" if runtime_state.workflow_state.active_conditions else "FINAL_ASSET_QA_REQUIRED"
    memory = runtime_state.memory_snapshot.model_copy(update={
        "preserved_artifacts": preserved, "stale_artifacts": [],
        "current_stage": next_stage,
    })
    updated = runtime_state.model_copy(update={
        "memory_snapshot": memory,
        "artifact_refreshes": [*runtime_state.artifact_refreshes, event],
        "execution_authorized": False,
        "corrective_cycle_active": False,
        "current_stage": next_stage,
    })
    return updated, merged
