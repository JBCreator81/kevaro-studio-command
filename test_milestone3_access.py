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


def test_approval_service_remains_human_studio_head_constrained(monkeypatch):
    class NeverCalled:
        def load_runtime_state(self, production_name):
            raise AssertionError("authorization must happen before persistence")

    import studio_command.service as service
    monkeypatch.setattr(service, "production_persistence", NeverCalled())
    with pytest.raises(HTTPException) as exc:
        studio_head_decision(
            "Production",
            "APPROVE",
            decided_by="Riley",
            actor_role="Reviewer",
        )
    assert exc.value.status_code == 403
    assert exc.value.detail["reason_code"] == "HUMAN_STUDIO_HEAD_REQUIRED"


def test_pending_nodes_have_explicit_owner_and_enforce_mutations():
    graph = build_production_graph(
        production_plan=production_plan,
        production_schedule=production_schedule,
    )
    node = graph.nodes[0]
    assigned_agent = node.accountability.ai_agent_responsible
    assert assigned_agent.role == node.responsible_role

    running = start_graph_node(
        graph_state=graph,
        node_id=node.node_id,
        actor=assigned_agent,
    )
    completed = complete_graph_node(
        graph_state=running,
        node_id=node.node_id,
        actor=assigned_agent,
    )
    assert node.node_id in completed.completed_nodes

    with pytest.raises(AuthorizationDenied):
        start_graph_node(
            graph_state=graph,
            node_id=node.node_id,
            actor=unassigned,
        )


def test_pending_snapshot_exposes_owner_access_and_denial(monkeypatch):
    bundle = add_pending_accountability(review_bundle())

    class PendingPersistence:
        def load_runtime_state(self, production_name):
            return None

        def load_pending_review_bundle(self, production_name):
            return bundle

    import studio_command.service as service
    monkeypatch.setattr(service, "production_persistence", PendingPersistence())
    snapshot = service.live_studio_snapshot(
        "Luxury Wellness Campaign",
        actor_name="Taylor",
        actor_role="Crew",
    )
    assert snapshot["access"]["Research"]["access_level"] == "UNASSIGNED"
    assert snapshot["access"]["Research"]["blocked_reason_code"] == "ACTOR_UNASSIGNED"
    node = snapshot["graph"]["nodes"][0]
    assert node["ownership"]["current_owner"]["role"] == node["responsible_role"]
    assert node["ownership"]["access"]["capabilities"]["edit"] is False


def test_finalize_fails_closed_before_runtime_lookup(monkeypatch):
    class NeverCalled:
        def load_runtime_state(self, production_name):
            raise AssertionError("authorization must happen before persistence")

    import studio_command.service as service
    monkeypatch.setattr(service, "production_persistence", NeverCalled())
    with pytest.raises(HTTPException) as exc:
        finalize_production(
            "Production",
            actor_name="Riley",
            actor_role="Reviewer",
        )
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "ACCESS_DENIED"


@pytest.mark.parametrize(
    "path",
    [
        "/api/productions/Production/decision",
        "/api/productions/Production/finalize",
        "/api/productions/Production/deliver",
        "/api/reality-shift",
    ],
)
def test_public_mutations_fail_closed_without_trusted_context(
    monkeypatch,
    path,
):
    monkeypatch.delenv("KEVARO_INTERNAL_AUTH_TOKEN", raising=False)
    response = TestClient(__import__(
        "studio_command.service", fromlist=["app"]
    ).app).post(path)
    assert response.status_code == 422
    assert response.json()["detail"]["reason_code"] == (
        "TRUSTED_ACTOR_CONTEXT_UNAVAILABLE"
    )


def test_public_caller_cannot_claim_studio_head_with_bad_token(monkeypatch):
    monkeypatch.setenv("KEVARO_INTERNAL_AUTH_TOKEN", "server-secret")
    response = TestClient(__import__(
        "studio_command.service", fromlist=["app"]
    ).app).post(
        "/api/productions/Production/finalize",
        params={"actor_name": "Attacker", "actor_role": "Studio Head"},
        headers={"x-kevaro-internal-token": "wrong-secret"},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["reason_code"] == (
        "TRUSTED_ACTOR_CONTEXT_REQUIRED"
    )


def test_public_actor_claim_must_match_server_identity(monkeypatch):
    monkeypatch.setenv("KEVARO_INTERNAL_AUTH_TOKEN", "server-secret")
    monkeypatch.setenv("KEVARO_STUDIO_HEAD_NAME", "Morgan Lee")
    response = TestClient(__import__(
        "studio_command.service", fromlist=["app"]
    ).app).post(
        "/api/productions/Production/finalize",
        params={"actor_name": "Attacker", "actor_role": "Studio Head"},
        headers={"x-kevaro-internal-token": "server-secret"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["reason_code"] == (
        "ACTOR_CONTEXT_MISMATCH"
    )


def test_trusted_public_context_reaches_backend_authorization(
    monkeypatch,
):
    class MissingPersistence:
        def load_runtime_state(self, production_name):
            return None

    import studio_command.service as service

    monkeypatch.setenv("KEVARO_INTERNAL_AUTH_TOKEN", "server-secret")
    monkeypatch.setenv("KEVARO_STUDIO_HEAD_NAME", "Morgan Lee")
    monkeypatch.setattr(service, "production_persistence", MissingPersistence())
    response = TestClient(service.app).post(
        "/api/productions/Production/finalize",
        params={"actor_name": "Morgan Lee"},
        headers={"x-kevaro-internal-token": "server-secret"},
    )
    assert response.status_code == 404


