from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import AccountabilityAction, AccountabilityActor, AccountabilityMetadata


STUDIO_HEAD = AccountabilityActor(
    name="Studio Head", actor_type="HUMAN", role="Studio Head"
)

ARTIFACT_AGENTS = {
    "production_brief": ("executive_producer", "Executive Producer / Orchestrator"),
    "research_packet": ("research_agent", "Research Agent"),
    "creative_treatment": ("creative_development_agent", "Creative Development Agent"),
    "production_plan": ("production_manager_agent", "Production Manager Agent"),
    "production_schedule": ("scheduling_agent", "Scheduling Agent"),
    "asset_media_plan": ("asset_media_agent", "Asset & Media Agent"),
    "clearance_compliance_report": (
        "clearance_compliance_agent", "Clearance & Compliance Agent"
    ),
    "clearance_report": ("clearance_compliance_agent", "Clearance & Compliance Agent"),
    "verification_qa_report": (
        "verification_qa_agent", "Independent Verification / QA Agent"
    ),
    "verification_report": (
        "verification_qa_agent", "Independent Verification / QA Agent"
    ),
    "studio_head_decision_package": (
        "studio_head_decision_gate", "Studio Head Decision Gate Preparer"
    ),
    "decision_package": (
        "studio_head_decision_gate", "Studio Head Decision Gate Preparer"
    ),
}


def ai_actor(name: str, role: str) -> AccountabilityActor:
    return AccountabilityActor(name=name, actor_type="AI_AGENT", role=role)


def human_actor(name: str, role: str = "Studio Head") -> AccountabilityActor:
    return AccountabilityActor(name=name, actor_type="HUMAN", role=role)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def pending_accountability(
    key: str, *, timestamp: datetime | None = None
) -> AccountabilityMetadata:
    timestamp = timestamp or _now()
    agent_name, role = ARTIFACT_AGENTS[key]
    agent = ai_actor(agent_name, role)
    reviewer = (
        agent
        if key in {"verification_qa_report", "verification_report"}
        else None
    )
    return AccountabilityMetadata(
        human_owner=STUDIO_HEAD,
        ai_agent_responsible=agent,
        reviewer_verifier=reviewer,
        last_changed_by=agent,
        created_at=timestamp,
        last_changed_at=timestamp,
        current_status="PENDING_STUDIO_HEAD_REVIEW",
        action_history=[
            AccountabilityAction(
                action="CREATED_FOR_REVIEW",
                actor=agent,
                timestamp=timestamp,
                status="PENDING_STUDIO_HEAD_REVIEW",
            )
        ],
        human_final_authority=True,
    )


def add_pending_accountability(
    review_bundle: dict[str, Any],
) -> dict[str, Any]:
    timestamp = _now()
    enriched: dict[str, Any] = {}
    for key, value in review_bundle.items():
        artifact = dict(value) if isinstance(value, dict) else value
        if (
            isinstance(artifact, dict)
            and key in ARTIFACT_AGENTS
            and not artifact.get("accountability")
        ):
            artifact["accountability"] = pending_accountability(
                key, timestamp=timestamp
            ).model_dump(mode="json")
        enriched[key] = artifact
    return enriched


def add_human_approval(
    artifacts: dict[str, Any], *, decided_by: str, status: str
) -> dict[str, Any]:
    timestamp = _now()
    approver = human_actor(decided_by)
    enriched: dict[str, Any] = {}
    for key, value in artifacts.items():
        artifact = dict(value) if isinstance(value, dict) else value
        if not isinstance(artifact, dict):
            enriched[key] = artifact
            continue
        raw = artifact.get("accountability")
        metadata = (
            AccountabilityMetadata.model_validate(raw)
            if raw
            else pending_accountability(key, timestamp=timestamp)
            if key in ARTIFACT_AGENTS
            else AccountabilityMetadata(human_owner=STUDIO_HEAD)
        )
        metadata.approved_by = approver
        metadata.last_changed_by = approver
        metadata.last_changed_at = timestamp
        metadata.current_status = status
        metadata.action_history.append(
            AccountabilityAction(
                action="STUDIO_HEAD_DECISION",
                actor=approver,
                timestamp=timestamp,
                status=status,
                details=(
                    "Human Studio Head decision established governed runtime state."
                ),
            )
        )
        artifact["accountability"] = metadata.model_dump(mode="json")
        enriched[key] = artifact
    return enriched


def human_decision_accountability(
    *, decided_by: str, action: str, status: str
) -> AccountabilityMetadata:
    timestamp = _now()
    authority = human_actor(decided_by)
    return AccountabilityMetadata(
        human_owner=authority,
        approved_by=authority,
        last_changed_by=authority,
        created_at=timestamp,
        last_changed_at=timestamp,
        current_status=status,
        action_history=[
            AccountabilityAction(
                action=action,
                actor=authority,
                timestamp=timestamp,
                status=status,
            )
        ],
        human_final_authority=True,
    )
