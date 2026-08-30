from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

from .accountability import human_actor
from .identity import canonical_production_name
from .models import AccountabilityActor, CrewMember, CrewProductionAssignment

SESSION_COOKIE = "kevaro_session"
SESSION_TTL_SECONDS = 8 * 60 * 60


class SessionError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedCrewIdentity:
    member: CrewMember
    assignment: CrewProductionAssignment
    actor: AccountabilityActor

    def public_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.member.user_id,
            "display_name": self.member.display_name,
            "organization_id": self.member.organization_id,
            "organization_name": self.member.organization_name,
            "production_name": self.assignment.production_name,
            "roles": self.assignment.roles,
            "owned_node_ids": self.assignment.owned_node_ids,
            "owned_task_ids": self.assignment.owned_task_ids,
            "reviewer_node_ids": self.assignment.reviewer_node_ids,
            "verifier_node_ids": self.assignment.verifier_node_ids,
            "studio_head": self.assignment.studio_head,
        }


def _b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_session(auth_subject: str, secret: str, *, now: int | None = None) -> str:
    if len(secret) < 32:
        raise SessionError("Session signing secret must contain at least 32 characters.")
    issued_at = int(time.time() if now is None else now)
    payload = {"sub": auth_subject, "iat": issued_at, "exp": issued_at + SESSION_TTL_SECONDS}
    encoded = _b64_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _b64_encode(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def verify_session(token: str, secret: str, *, now: int | None = None) -> str:
    try:
        encoded, signature = token.split(".", 1)
        expected = _b64_encode(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise SessionError("Session signature is invalid.")
        payload = json.loads(_b64_decode(encoded))
        current = int(time.time() if now is None else now)
        if not isinstance(payload.get("sub"), str) or not payload["sub"]:
            raise SessionError("Session subject is invalid.")
        if int(payload.get("iat", 0)) > current + 60 or int(payload.get("exp", 0)) <= current:
            raise SessionError("Session has expired.")
        return payload["sub"]
    except SessionError:
        raise
    except Exception as exc:
        raise SessionError("Session is invalid.") from exc


def resolve_crew_identity(
    *, token: str, secret: str, persistence: Any, production_name: str
) -> ResolvedCrewIdentity:
    subject = verify_session(token, secret)
    member = persistence.load_crew_member(subject)
    if member is None or not member.active:
        raise SessionError("Authenticated user is not an active crew member.")
    canonical_name = canonical_production_name(production_name)
    assignment = next(
        (item for item in member.assignments
         if canonical_production_name(item.production_name) == canonical_name),
        None,
    )
    if assignment is None:
        raise PermissionError("Crew member is not assigned to this production.")
    role = "Studio Head" if assignment.studio_head else (
        assignment.roles[0] if assignment.roles else "Crew Member"
    )
    return ResolvedCrewIdentity(
        member, assignment,
        AccountabilityActor(name=member.display_name, user_id=member.user_id, actor_type="HUMAN", role=role),
    )
