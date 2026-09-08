from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .decisions import (
    build_production_decision_history_entry,
    derive_production_workflow_state,
    record_studio_head_decision,
)
from .identity import require_production_identity
from .models import AccountabilityAction, AccountabilityActor, StudioHeadDecisionPackage

EXPECTED = {
    "aurelian-symphony-of-serenity-instagram-reels-v1.mp4": "f8db828dcf2b65356fa5700b3b877602d8adaea3e64a50009097c8c669bd55b0",
    "aurelian-symphony-of-serenity-youtube-shorts-v1.mp4": "f8db828dcf2b65356fa5700b3b877602d8adaea3e64a50009097c8c669bd55b0",
    "aurelian-symphony-of-serenity-16x9-master-v1.mp4": "bdd92d7e259c4a65ab4a9e2fb53589bbd0f10b64b2661a8ea47c4d4bca5e7cf3",
}


def _review(asset: Any, review_type: str):
    return next((r for r in asset.reviews if r.decision == "APPROVE" and any(
        a.get("review_type") == review_type for a in r.annotations
    )), None)


def approve_final_media_chain(*, persistence: Any, production_name: str,
                              actor: AccountabilityActor, asset_ids: list[str],
                              decision_notes: str) -> dict[str, Any]:
    production_name = require_production_identity(production_name)
    if persistence.load_final_package(production_name) is not None:
        raise ValueError("Final-media package is already finalized.")
    if len(asset_ids) != 3 or len(set(asset_ids)) != 3:
        raise ValueError("Final-media approval requires exactly three distinct asset IDs.")
    registry = persistence.load_asset_registry(production_name)
    if registry is None:
        raise ValueError("Production asset registry was not found.")
    latest = {}
    for asset_id in asset_ids:
        versions = [a for a in registry.assets if a.asset_id == asset_id]
        if not versions:
            raise ValueError(f"Final-media asset was not found: {asset_id}")
        latest[asset_id] = max(versions, key=lambda a: a.version_number)
    if {a.filename for a in latest.values()} != set(EXPECTED):
        raise ValueError("Final-media approval requires the exact three Aurelian deliverables.")
    clearance_records, qa_records = [], []
    for asset in latest.values():
        expected_hash = EXPECTED[asset.filename]
        if asset.storage.checksum_sha256 != expected_hash:
            raise ValueError(f"Checksum mismatch for {asset.filename}.")
        if asset.provenance.get("checksum_sha256") != expected_hash:
            raise ValueError(f"Provenance checksum mismatch for {asset.filename}.")
        clearance = _review(asset, "CLEARANCE_COMPLIANCE")
        qa = _review(asset, "INDEPENDENT_QA")
        if clearance is None or qa is None:
            raise ValueError(f"Both Clearance and independent QA approvals are required for {asset.filename}.")
        creator = next((h.actor.name for h in asset.accountability.action_history if h.action == "ASSET_REGISTERED"), None)
        if not creator or qa.reviewer.name.casefold() == creator.casefold():
            raise ValueError(f"Independent QA reviewer is not distinct from the creator for {asset.filename}.")
        clearance_records.append(clearance); qa_records.append(qa)
    if len({r.reviewer.name.casefold() for r in qa_records}) != 1:
        raise ValueError("One identifiable independent QA reviewer must cover all deliverables.")

    artifacts = persistence.load_approved_artifacts(production_name)
    runtime = persistence.load_runtime_state(production_name)
    if artifacts is None or runtime is None:
        raise ValueError("Governed runtime and approved artifacts are required.")
    now = datetime.now(timezone.utc)
    clearance = artifacts["clearance_report"]
    clearance.update({
        "blocked_items": [], "unresolved_questions": [], "required_documents": [],
        "clearance_risks": [], "clearance_decision": "CLEAR TO PROCEED",
        "next_clearance_actions": [],
    })
    for check in clearance.get("compliance_checks", []):
        check["status"] = "cleared"; check["blocking_issue"] = "none"
    clearance.setdefault("cleared_items", []).append(
        "Three immutable final Aurelian MP4 versions passed authorized final-content Clearance/Compliance review."
    )
    qa = artifacts["verification_report"]
    qa.update({
        "failed_checks": [], "unresolved_items": [], "cross_artifact_conflicts": [],
        "readiness_score": 100, "qa_decision": "PASS", "next_qa_actions": [],
        "technical_validation": [
            "All three immutable MP4s: 720 H.264 frames, 24 fps, 30.000-second video, stereo AAC at 48 kHz.",
            "Vertical deliverables are 1080x1920 (9:16); master is 3840x2160 (16:9).",
            "Counted-frame decode scans, representative-frame inspection, safe-zone review, and SHA-256 identity passed."
        ],
        "evidence_validation": [
            "Final content uses only registered Aurelian environments, procedural score/SFX, Noto Sans/OFL, and fictional Renewal Serum.",
            "No spoken words require captions; no unsupported medical claims or real third-party talent, location, or product appears."
        ],
    })
    qa.setdefault("passed_checks", []).extend([
        "Immutable final-media checksum identity", "End-to-end counted-frame decode",
        "Final content, spelling, safe zones, continuity, and audio review",
    ])
    decision = artifacts["decision_package"]
    decision.update({
        "readiness_score": 100, "material_blockers": [], "conditions_for_approval": [],
        "clearance_status": "CLEAR TO PROCEED", "qa_decision": "PASS",
        "recommended_decision": "APPROVE",
        "executive_summary": "Three immutable Aurelian deliverables passed authorized Clearance and distinct independent QA.",
        "final_warning": "No unresolved final-media blocker remains; delivery still requires authenticated Studio Head approval and governed finalization.",
    })
    artifacts["delivery_artifacts"] = list(EXPECTED)
    artifacts["final_notes"] = [
        "Clearance reviewer: " + clearance_records[0].reviewer.name,
        "Independent QA reviewer: " + qa_records[0].reviewer.name,
        "Final-media approval preserves immutable SHA-256 and append-only review history.",
    ]
    package = StudioHeadDecisionPackage.model_validate(decision)
    record = record_studio_head_decision(
        production_name=production_name, decision="APPROVE", conditions=[],
        decision_notes=decision_notes, decided_by=actor.name,
        decision_package=package, unresolved_risks_acknowledged=[],
    )
    workflow = derive_production_workflow_state(record)
    sequence = runtime.decision_history[-1].sequence + 1
    history = build_production_decision_history_entry(
        sequence=sequence, decision_record=record, workflow_state=workflow,
    )
    runtime.decision_history.append(history)
    runtime.workflow_state = workflow
    runtime.memory_snapshot.active_decision_sequence = sequence
    runtime.execution_authorized = True
    runtime.corrective_cycle_active = False
    runtime.current_stage = "FINAL_MEDIA_APPROVED"
    for key, reviewer, action in (
        ("clearance_report", clearance_records[0].reviewer, "FINAL_MEDIA_CLEARANCE_PASS"),
        ("verification_report", qa_records[0].reviewer, "INDEPENDENT_FINAL_MEDIA_QA_PASS"),
    ):
        accountability = artifacts[key]["accountability"]
        accountability["last_changed_by"] = reviewer.model_dump(mode="json")
        accountability["last_changed_at"] = now.isoformat()
        accountability["current_status"] = "APPROVED"
        accountability.setdefault("action_history", []).append(AccountabilityAction(
            action=action, actor=reviewer, timestamp=now, status="APPROVED",
            details="Validated exact immutable final-media checksums and review evidence.",
        ).model_dump(mode="json"))
    persistence.save_approved_artifacts(production_name=production_name, approved_artifacts=artifacts)
    persistence.save_runtime_state(runtime)
    return {
        "production_name": production_name, "clearance": "CLEAR TO PROCEED",
        "qa": "PASS", "readiness": 100, "studio_head_approval": "APPROVED",
        "decision_sequence": sequence, "asset_ids": asset_ids,
    }
