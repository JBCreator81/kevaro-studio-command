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
    memory = runtime_state.memory_snapshot.model_copy(update={
        "preserved_artifacts": preserved, "stale_artifacts": [],
        "current_stage": "CONDITIONS_BLOCK_EXECUTION",
    })
    updated = runtime_state.model_copy(update={
        "memory_snapshot": memory,
        "artifact_refreshes": [*runtime_state.artifact_refreshes, event],
        "execution_authorized": False,
        "corrective_cycle_active": False,
        "current_stage": "CONDITIONS_BLOCK_EXECUTION",
    })
    return updated, merged
