from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import AccountabilityActor, AccountabilityMetadata

STUDIO_HEAD_ROLE = "Studio Head"
PROTECTED_STATUSES = {
    "APPROVED", "APPROVED_WITH_CONDITIONS", "COMPLETED", "DELIVERED",
    "FINALIZED", "READY_FOR_DELIVERY",
}


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    action: str
    access_level: str
    reason_code: str
    reason: str
    capabilities: dict[str, bool]
    requires_change_request: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "access_level": self.access_level,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "capabilities": self.capabilities,
            "requires_change_request": self.requires_change_request,
        }


class AuthorizationDenied(ValueError):
    def __init__(self, decision: AccessDecision):
        self.decision = decision
        super().__init__(decision.reason)

    def as_detail(self) -> dict[str, Any]:
        return {"error": "ACCESS_DENIED", **self.decision.as_dict()}


def _same_actor(
    left: AccountabilityActor,
    right: AccountabilityActor | None,
) -> bool:
    return bool(
        right
        and left.name.strip().casefold() == right.name.strip().casefold()
        and left.actor_type == right.actor_type
    )


def is_human_studio_head(actor: AccountabilityActor) -> bool:
    return (
        actor.actor_type == "HUMAN"
        and actor.role.strip().casefold() == STUDIO_HEAD_ROLE.casefold()
    )


def _capabilities(level: str, protected: bool = False) -> dict[str, bool]:
    head = level == "STUDIO_HEAD"
    owner = level == "ASSIGNED_OWNER"
    contributor = level == "CONTRIBUTOR"
    reviewer = level == "REVIEWER_VERIFIER"
    reader = level in {"DOWNSTREAM_READER", "EXPLICIT_READER"}
    return {
        "read": head or owner or contributor or reviewer or reader,
        "edit": head or ((owner or contributor) and not protected),
        "comment": head or owner or contributor or reviewer,
        "review": head or reviewer,
        "verify": head or reviewer,
        "approve": head,
        "request_change": head or owner or contributor or reviewer,
    }


def _deny(
    action: str,
    code: str,
    reason: str,
    level: str,
    protected: bool,
    change: bool = False,
) -> AccessDecision:
    return AccessDecision(
        False, action, level, code, reason,
        _capabilities(level, protected), change,
    )


def evaluate_access(
    *,
    actor: AccountabilityActor,
    action: str,
    accountability: AccountabilityMetadata | dict[str, Any] | None,
    scope: str | None = None,
    status: str | None = None,
    dependency_approved: bool = False,
) -> AccessDecision:
    action = action.strip().upper()
    metadata = (
        accountability
        if isinstance(accountability, AccountabilityMetadata)
        else AccountabilityMetadata.model_validate(accountability)
        if accountability
        else None
    )
    current_status = status or (
        metadata.current_status if metadata else ""
    ) or ""
    protected = current_status.upper() in PROTECTED_STATUSES

    if (
        action in {"APPROVE", "FINALIZE", "DELIVER"}
        and not is_human_studio_head(actor)
    ):
        return _deny(
            action,
            "HUMAN_STUDIO_HEAD_REQUIRED",
            "This action requires human Studio Head authority.",
            "UNASSIGNED",
            protected,
        )

    if is_human_studio_head(actor):
        level = "STUDIO_HEAD"
    elif metadata and (
        _same_actor(actor, metadata.human_owner)
        or _same_actor(actor, metadata.ai_agent_responsible)
    ):
        level = "ASSIGNED_OWNER"
    elif metadata and any(
        _same_actor(actor, item) for item in metadata.contributors
    ):
        assigned = metadata.contributor_scopes.get(actor.name, [])
        if action == "EDIT" and (not scope or scope not in assigned):
            return _deny(
                action,
                "CONTRIBUTOR_SCOPE_REQUIRED",
                "Contributor edit access is limited to an explicitly assigned scope.",
                "CONTRIBUTOR",
                protected,
            )
        level = "CONTRIBUTOR"
    elif metadata and _same_actor(actor, metadata.reviewer_verifier):
        level = "REVIEWER_VERIFIER"
    elif metadata and any(
        _same_actor(actor, item) for item in metadata.readers
    ):
        level = "EXPLICIT_READER"
    elif dependency_approved and action == "READ":
        level = "DOWNSTREAM_READER"
    else:
        code = (
            "LEGACY_ASSIGNMENT_REQUIRED"
            if metadata is None
            else "ACTOR_UNASSIGNED"
        )
        return _deny(
            action,
            code,
            "No explicit assignment grants this actor access to the requested production work.",
            "UNASSIGNED",
            protected,
        )

    caps = _capabilities(level, protected)
    capability = {
        "READ": "read",
        "EDIT": "edit",
        "COMMENT": "comment",
        "REVIEW": "review",
        "VERIFY": "verify",
        "APPROVE": "approve",
        "FINALIZE": "approve",
        "DELIVER": "approve",
        "REALITY_SHIFT": "request_change",
        "START": "edit",
        "COMPLETE": "edit",
    }.get(action)
    if capability is None:
        return _deny(
            action, "UNKNOWN_ACTION",
            "The requested authorization action is not recognized.",
            level, protected,
        )
    if (
        protected
        and action in {"EDIT", "START", "COMPLETE"}
        and not is_human_studio_head(actor)
    ):
        return _deny(
            action,
            "CHANGE_REQUEST_REQUIRED",
            "Completed or approved work cannot be silently rewritten; route the change through Reality Shift.",
            level,
            protected,
            True,
        )
    if (
        action in {"APPROVE", "FINALIZE", "DELIVER"}
        and not is_human_studio_head(actor)
    ):
        return _deny(
            action,
            "HUMAN_STUDIO_HEAD_REQUIRED",
            "This action requires human Studio Head authority.",
            level,
            protected,
        )
    if not caps[capability]:
        code = (
            "REVIEWER_CANNOT_REWRITE"
            if level == "REVIEWER_VERIFIER"
            and action in {"EDIT", "START", "COMPLETE"}
            else "ACTION_OUTSIDE_ASSIGNED_ROLE"
        )
        return _deny(
            action, code,
            "The requested action is outside this actor's assigned authority.",
            level, protected,
        )
    return AccessDecision(
        True, action, level, "ACCESS_GRANTED",
        "The actor is authorized for this action.", caps,
    )


def require_access(**kwargs: Any) -> AccessDecision:
    decision = evaluate_access(**kwargs)
    if not decision.allowed:
        raise AuthorizationDenied(decision)
    return decision


def access_snapshot(
    *,
    actor: AccountabilityActor,
    accountability: AccountabilityMetadata | dict[str, Any] | None,
    status: str | None = None,
) -> dict[str, Any]:
    read = evaluate_access(
        actor=actor,
        action="READ",
        accountability=accountability,
        status=status,
    )
    metadata = (
        accountability
        if isinstance(accountability, AccountabilityMetadata)
        else AccountabilityMetadata.model_validate(accountability)
        if accountability
        else None
    )
    owner = (
        metadata.human_owner or metadata.ai_agent_responsible
        if metadata else None
    )
    return {
        "actor": actor.model_dump(mode="json"),
        "current_owner": owner.model_dump(mode="json") if owner else None,
        "access_level": read.access_level,
        "capabilities": read.capabilities,
        "blocked_reason": None if read.allowed else read.reason,
        "blocked_reason_code": None if read.allowed else read.reason_code,
    }

