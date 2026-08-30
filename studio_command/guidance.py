from __future__ import annotations

from typing import Any

from .access import evaluate_access, is_human_studio_head
from .models import (
    AccountabilityActor,
    GuidanceLevel,
    ProductionGraphNode,
    ProductionGraphState,
    RoleAwareGuidance,
)

VALID_GUIDANCE_LEVELS = {"Guided", "Standard", "Expert"}
BLOCKER_FIELDS = (
    "blockers", "material_blockers", "blocked_items", "blocked_assets",
    "failed_checks", "cross_artifact_conflicts", "clearance_risks",
)
MISSING_INPUT_FIELDS = (
    "required_documents", "client_supplied_assets", "unresolved_questions",
    "unresolved_items", "research_questions", "risks_or_unknowns",
    "unresolved_creative_questions",
)


def normalize_guidance_level(level: str) -> GuidanceLevel:
    normalized = level.strip().title()
    if normalized not in VALID_GUIDANCE_LEVELS:
        raise ValueError("guidance_level must be Guided, Standard, or Expert.")
    return normalized  # type: ignore[return-value]


def _items(source: dict[str, Any] | None, fields: tuple[str, ...]) -> list[str]:
    if not source:
        return []
    result: list[str] = []
    for field in fields:
        value = source.get(field)
        if isinstance(value, list):
            result.extend(str(item) for item in value if str(item).strip())
    return list(dict.fromkeys(result))


def derive_node_guidance(
    *,
    actor: AccountabilityActor,
    node: ProductionGraphNode,
    graph_state: ProductionGraphState,
    artifact: dict[str, Any] | None = None,
    guidance_level: str = "Standard",
    production_stage: str | None = None,
) -> RoleAwareGuidance:
    level = normalize_guidance_level(guidance_level)
    metadata = node.accountability
    read = evaluate_access(
        actor=actor,
        action="READ",
        accountability=metadata,
        status=node.status,
    )
    access = read
    unmet = [
        item for item in node.dependencies
        if item not in set(graph_state.completed_nodes)
    ]
    blockers = _items(artifact, BLOCKER_FIELDS)
    if node.stale_reason:
        blockers.insert(0, node.stale_reason)
    if node.status in {"BLOCKED", "FAILED"} and not blockers:
        blockers.append(f"{node.task_name} is {node.status.lower()}.")
    waiting_on = [f"Completion of {item}" for item in unmet]
    missing = _items(artifact, MISSING_INPUT_FIELDS)

    action_type = "READ"
    action = f"Review {node.task_name} context"
    rationale = "Read the available governed context before work proceeds."
    sources = ["scoped_access"]
    happens = "Use the context to coordinate with the assigned owner."
    escalation = False
    escalation_condition = None
    escalation_target = None

    if read.access_level == "STUDIO_HEAD":
        if production_stage == "STUDIO_HEAD_REVIEW" or node.approval_required:
            action_type = "APPROVE"
            action = f"Review the decision gate for {node.task_name}"
            rationale = "This work is at a human governance gate."
            sources = ["lifecycle_state", "human_final_authority"]
            happens = "Your decision will authorize advancement or route corrective work."
        elif blockers or missing:
            action_type = "REVIEW"
            action = f"Resolve or route attention for {node.task_name}"
            rationale = "Current production evidence identifies an unresolved blocker or input."
            sources = ["artifact_blockers", "artifact_missing_inputs"]
            happens = "The assigned owner can proceed when the blocking context is resolved."
        elif node.status in {"READY", "RUNNING", "STALE"}:
            action = f"Monitor {node.task_name} and its owner"
            rationale = "Command oversight is appropriate while assigned work is active."
            sources = ["node_status", "accountability"]
            happens = "The owner completes the work, then downstream dependencies are released."
        else:
            action = f"Review {node.task_name} status"
            rationale = "No command decision is presently required for this node."
            sources = ["node_status"]
            happens = "Kevaro will surface the next governance gate when state changes."
    elif unmet:
        action = f"Wait for {unmet[0]} and review available context"
        rationale = "The node cannot begin until its declared dependencies complete."
        sources = ["graph_dependencies", "node_status"]
        happens = f"{node.task_name} becomes eligible when all dependencies complete."
    elif read.access_level in {"ASSIGNED_OWNER", "CONTRIBUTOR"}:
        desired = "COMPLETE" if node.status == "RUNNING" else "START"
        candidate = evaluate_access(
            actor=actor,
            action=desired,
            accountability=metadata,
            status=node.status,
        )
        if candidate.allowed and node.status in {"READY", "RUNNING"}:
            action_type = desired
            verb = "Complete" if desired == "COMPLETE" else "Start"
            action = f"{verb} {node.task_name}"
            rationale = "Assigned work is dependency-ready and scoped access permits the action."
            sources = ["accountability", "graph_dependencies", "scoped_access"]
            happens = "Completion records progress and releases eligible downstream work."
            access = candidate
        elif candidate.requires_change_request:
            action_type = "REALITY_SHIFT"
            action = f"Request governed change for {node.task_name}"
            rationale = candidate.reason
            sources = ["protected_lifecycle_state", "scoped_access"]
            happens = "Reality Shift determines affected work and required re-verification."
            escalation = True
            escalation_condition = "Protected work must change."
            escalation_target = "Studio Head"
    elif read.access_level == "REVIEWER_VERIFIER":
        access = evaluate_access(
            actor=actor,
            action="REVIEW",
            accountability=metadata,
            status=node.status,
        )
        action_type = "REVIEW"
        action = f"Review and verify {node.task_name}"
        rationale = "Reviewer assignment permits independent review without creator edit authority."
        sources = ["accountability", "qa_separation", "scoped_access"]
        happens = "Record findings or return the work to its owner; creator content remains unchanged."
    elif not read.allowed:
        action_type = "ESCALATE"
        action = f"Contact the owner or Studio Head about {node.task_name}"
        rationale = read.reason
        sources = ["scoped_access", "accountability"]
        happens = "An authorized owner can assign scope, provide context, or route the request."
        escalation = True
        escalation_condition = "Work or context is needed without an explicit assignment."
        escalation_target = "Studio Head"

    authorization = evaluate_access(
        actor=actor,
        action=action_type if action_type != "ESCALATE" else "READ",
        accountability=metadata,
        status=node.status,
    )
    authorized = action_type == "ESCALATE" or authorization.allowed
    if not authorized:
        action_type = "ESCALATE"
        action = f"Route {node.task_name} to an authorized owner"
        rationale = authorization.reason
        sources = ["scoped_access"]
        happens = "The authorized owner or Studio Head determines the valid next path."
        escalation = True
        escalation_condition = "Recommended production action is outside current authority."
        escalation_target = "Studio Head"
        authorized = True

    owner = (
        metadata.human_owner or metadata.ai_agent_responsible
        if metadata else None
    )
    responsibility = (
        f"Own {node.task_name}."
        if access.access_level == "ASSIGNED_OWNER"
        else f"Contribute only within assigned scope on {node.task_name}."
        if access.access_level == "CONTRIBUTOR"
        else f"Independently review {node.task_name}."
        if access.access_level == "REVIEWER_VERIFIER"
        else f"Govern {node.task_name}."
        if is_human_studio_head(actor)
        else f"No assigned responsibility for {node.task_name}."
    )
    detail = None
    if level == "Guided":
        detail = f"Review context and missing inputs, then perform only: {action}."
    elif level == "Expert":
        detail = (
            f"Rule inputs: status={node.status}; access={access.access_level}; "
            f"unmet_dependencies={len(unmet)}; blockers={len(blockers)}; "
            f"missing_inputs={len(missing)}."
        )

    return RoleAwareGuidance(
        guidance_level=level,
        responsibility_now=responsibility,
        context={
            "production": graph_state.production_name,
            "node_id": node.node_id,
            "task": node.task_name,
            "status": node.status,
            "production_stage": production_stage,
            "owner": owner.model_dump(mode="json") if owner else None,
        },
        access=access.as_dict(),
        blockers=blockers,
        waiting_on=waiting_on,
        missing_inputs=missing,
        next_best_action={
            "action": action,
            "action_type": action_type,
            "target": node.node_id,
            "authorized": authorized,
            "rationale": rationale,
            "rationale_sources": sources,
        },
        what_happens_next=happens,
        escalation_required=escalation,
        escalation_condition=escalation_condition,
        escalation_target=escalation_target,
        detail=detail,
    )


def production_guidance_summary(items: list[RoleAwareGuidance]) -> dict[str, Any]:
    actionable = [
        item for item in items
        if item.next_best_action.action_type not in {"READ", "ESCALATE"}
    ]
    attention = [
        item for item in items
        if item.blockers or item.missing_inputs or item.escalation_required
    ]
    waiting = [item for item in items if item.waiting_on]
    choice = (actionable or attention or waiting or items)[0] if items else None
    return {
        "your_work_now": [item.responsibility_now for item in actionable],
        "waiting_on": list(dict.fromkeys(
            value for item in waiting for value in item.waiting_on
        )),
        "needs_attention": [item.context["node_id"] for item in attention],
        "next_best_action": (
            choice.next_best_action.model_dump(mode="json") if choice else None
        ),
    }
