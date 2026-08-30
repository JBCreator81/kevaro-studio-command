import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from studio_command.access import AuthorizationDenied, evaluate_access, require_access
from studio_command.accountability import add_pending_accountability, human_actor, ai_actor
from studio_command.graph import build_production_graph, complete_graph_node, start_graph_node
from studio_command.models import AccountabilityMetadata, ProductionPlan
from studio_command.service import finalize_production, studio_head_decision
from test_milestone1_identity import review_bundle
from test_milestone19 import production_plan, production_schedule


owner = human_actor("Avery", "Editor")
other_owner = human_actor("Jordan", "Producer")
contributor = human_actor("Casey", "Contributor")
reviewer = human_actor("Riley", "Reviewer")
unassigned = human_actor("Taylor", "Crew")
downstream = ai_actor("delivery_agent", "Downstream Worker")


def metadata(status="IN_PROGRESS"):
    return AccountabilityMetadata(
        human_owner=owner,
        contributors=[contributor],
        contributor_scopes={"Casey": ["script_direction"]},
        reviewer_verifier=reviewer,
        current_status=status,
    )


def test_studio_head_has_full_governed_capabilities():
    decision = evaluate_access(
        actor=human_actor("Morgan Lee"),
        action="APPROVE",
        accountability=None,
    )
    assert decision.allowed
    assert decision.access_level == "STUDIO_HEAD"
    assert decision.capabilities["edit"]
    assert decision.capabilities["approve"]


def test_assigned_owner_can_edit_owned_work():
    assert evaluate_access(
        actor=owner, action="EDIT", accountability=metadata()
    ).allowed


def test_owner_cannot_silently_edit_another_owners_protected_work():
    decision = evaluate_access(
        actor=other_owner,
        action="EDIT",
        accountability=metadata("APPROVED"),
    )
    assert not decision.allowed
    assert decision.reason_code == "ACTOR_UNASSIGNED"


def test_owned_approved_work_requires_reality_shift():
    decision = evaluate_access(
        actor=owner,
        action="EDIT",
        accountability=metadata("APPROVED"),
    )
    assert not decision.allowed
    assert decision.reason_code == "CHANGE_REQUEST_REQUIRED"
    assert decision.requires_change_request


def test_contributor_is_limited_to_explicit_scope():
    assert evaluate_access(
        actor=contributor,
        action="EDIT",
        scope="script_direction",
        accountability=metadata(),
    ).allowed
    denied = evaluate_access(
        actor=contributor,
        action="EDIT",
        scope="visual_system",
        accountability=metadata(),
    )
    assert denied.reason_code == "CONTRIBUTOR_SCOPE_REQUIRED"


def test_reviewer_can_review_but_not_rewrite():
    assert evaluate_access(
        actor=reviewer, action="REVIEW", accountability=metadata()
    ).allowed
    denied = evaluate_access(
        actor=reviewer, action="EDIT", accountability=metadata()
    )
    assert denied.reason_code == "REVIEWER_CANNOT_REWRITE"


def test_downstream_reads_approved_dependency_but_cannot_modify_it():
    assert evaluate_access(
        actor=downstream,
        action="READ",
        accountability=None,
        dependency_approved=True,
    ).allowed
    assert not evaluate_access(
        actor=downstream,
        action="EDIT",
        accountability=None,
        dependency_approved=True,
    ).allowed


def test_unassigned_and_legacy_work_fail_closed_but_load():
    legacy = production_plan.model_dump(mode="json", exclude={"accountability"})
    assert ProductionPlan.model_validate(legacy).accountability is None
    with pytest.raises(AuthorizationDenied) as exc:
        require_access(
            actor=unassigned,
            action="EDIT",
            accountability=None,
        )
    assert exc.value.as_detail()["reason_code"] == "LEGACY_ASSIGNMENT_REQUIRED"


def test_public_governed_mutation_requires_authenticated_session(monkeypatch):
    import studio_command.service as service
    from studio_command.runtime_config import RuntimeConfig
    monkeypatch.setattr(service.app.state, "runtime_config", RuntimeConfig("local", "test", "local-environment", session_signing_secret="x" * 32), raising=False)
    response = TestClient(service.app).post("/api/productions/Production/finalize")
    assert response.status_code == 401
    assert response.json()["detail"]["reason_code"] == "AUTHENTICATED_SESSION_REQUIRED"


def test_browser_actor_claim_does_not_replace_session(monkeypatch):
    import studio_command.service as service
    from studio_command.runtime_config import RuntimeConfig
    monkeypatch.setattr(service.app.state, "runtime_config", RuntimeConfig("local", "test", "local-environment", session_signing_secret="x" * 32), raising=False)
    response = TestClient(service.app).post("/api/productions/Production/finalize", params={"actor_name": "Attacker", "actor_role": "Studio Head"})
    assert response.status_code == 401
