import pytest

from studio_command.access import evaluate_access
from studio_command.accountability import add_pending_accountability, human_actor
from studio_command.graph import build_production_graph
from studio_command.guidance import derive_node_guidance
from studio_command.ui_snapshot import build_pending_studio_command_snapshot
from studio_command.models import (
    AccountabilityMetadata,
    ProductionGraphNode,
    ProductionGraphState,
)


owner = human_actor("Avery", "Editor")
contributor = human_actor("Casey", "Contributor")
reviewer = human_actor("Riley", "Reviewer")
unassigned = human_actor("Taylor", "Crew")
head = human_actor("Morgan", "Studio Head")


def node(
    *, status="READY", dependencies=None, accountability=None,
    approval_required=False,
):
    return ProductionGraphNode(
        node_id="Edit",
        task_name="Edit",
        responsible_role="Editor",
        dependencies=dependencies or [],
        dependents=["QA"],
        status=status,
        can_run_in_parallel_with=[],
        approval_required=approval_required,
        stale_reason=None,
        accountability=accountability,
    )


def graph(item, completed=None):
    return ProductionGraphState(
        production_name="Campaign",
        nodes=[item],
        ready_nodes=[item.node_id] if item.status == "READY" else [],
        running_nodes=[item.node_id] if item.status == "RUNNING" else [],
        completed_nodes=completed or [],
        blocked_nodes=[item.node_id] if item.status == "BLOCKED" else [],
        stale_nodes=[],
        graph_complete=False,
    )


def assigned():
    return AccountabilityMetadata(
        human_owner=owner,
        contributors=[contributor],
        contributor_scopes={"Casey": ["captions"]},
        reviewer_verifier=reviewer,
        current_status="READY",
    )


def guidance(actor, item, **kwargs):
    return derive_node_guidance(
        actor=actor,
        node=item,
        graph_state=graph(item, kwargs.pop("completed", None)),
        **kwargs,
    )


def test_studio_head_receives_command_level_pending_review_guidance():
    item = node(accountability=assigned())
    result = guidance(head, item, production_stage="STUDIO_HEAD_REVIEW")
    assert result.next_best_action.action_type == "APPROVE"
    assert "human_final_authority" in result.next_best_action.rationale_sources
    assert result.next_best_action.authorized


def test_assigned_owner_receives_actionable_owned_work_guidance():
    result = guidance(owner, node(accountability=assigned()))
    assert result.responsibility_now == "Own Edit."
    assert result.next_best_action.action_type == "START"
    assert result.access["access_level"] == "ASSIGNED_OWNER"


def test_contributor_guidance_is_scope_limited():
    result = guidance(contributor, node(accountability=assigned()))
    assert "assigned scope" in result.responsibility_now
    assert result.access["access_level"] == "CONTRIBUTOR"
    assert result.access["capabilities"]["approve"] is False


def test_reviewer_gets_review_without_edit_authority_leakage():
    result = guidance(reviewer, node(accountability=assigned()))
    assert result.next_best_action.action_type == "REVIEW"
    assert result.access["capabilities"]["review"] is True
    assert result.access["capabilities"]["edit"] is False


def test_unassigned_actor_gets_safe_escalation_guidance():
    result = guidance(unassigned, node(accountability=assigned()))
    assert result.next_best_action.action_type == "ESCALATE"
    assert result.escalation_target == "Studio Head"
    assert result.access["capabilities"]["edit"] is False


def test_blocked_dependencies_surface_as_waiting_on():
    item = node(dependencies=["Brief"], accountability=assigned())
    result = guidance(owner, item)
    assert result.waiting_on == ["Completion of Brief"]
    assert result.next_best_action.action_type == "READ"


def test_missing_evidence_and_inputs_surface():
    result = guidance(
        owner,
        node(accountability=assigned()),
        artifact={
            "blockers": ["Rights check incomplete"],
            "required_documents": ["Talent release"],
        },
    )
    assert result.blockers == ["Rights check incomplete"]
    assert result.missing_inputs == ["Talent release"]


@pytest.mark.parametrize("actor", [head, owner, contributor, reviewer, unassigned])
def test_next_best_action_never_exceeds_actor_permissions(actor):
    item = node(accountability=assigned())
    result = guidance(actor, item)
    action = result.next_best_action.action_type
    if action == "ESCALATE":
        assert result.escalation_required
        return
    decision = evaluate_access(
        actor=actor,
        action=action,
        accountability=item.accountability,
        status=item.status,
    )
    assert decision.allowed


def test_guidance_level_changes_detail_not_authorization():
    item = node(accountability=assigned())
    results = [guidance(owner, item, guidance_level=level) for level in (
        "Guided", "Standard", "Expert",
    )]
    assert {item.next_best_action.action_type for item in results} == {"START"}
    assert {item.access["capabilities"]["edit"] for item in results} == {True}
    assert results[0].detail and results[1].detail is None and results[2].detail


def test_pending_review_reviewer_guidance_remains_review_only():
    result = guidance(
        reviewer,
        node(accountability=assigned()),
        production_stage="STUDIO_HEAD_REVIEW",
    )
    assert result.next_best_action.action_type == "REVIEW"
    assert result.access["capabilities"]["approve"] is False


def test_approved_runtime_protected_owner_routes_through_reality_shift():
    item = node(status="APPROVED", accountability=assigned())
    result = guidance(owner, item, production_stage="DOWNSTREAM_PRODUCTION")
    assert result.next_best_action.action_type == "REALITY_SHIFT"
    assert result.escalation_target == "Studio Head"


def test_legacy_node_loads_and_fails_closed_without_new_authority():
    result = guidance(unassigned, node(accountability=None))
    assert result.access["reason_code"] == "LEGACY_ASSIGNMENT_REQUIRED"
    assert result.next_best_action.action_type == "ESCALATE"


def test_blocked_node_surfaces_state_when_artifact_has_no_blocker_text():
    result = guidance(owner, node(status="BLOCKED", accountability=assigned()))
    assert result.blockers == ["Edit is blocked."]


def test_pending_snapshot_exposes_node_and_command_center_guidance_contract():
    from test_milestone1_identity import review_bundle
    from test_milestone19 import production_plan, production_schedule

    bundle = add_pending_accountability(review_bundle())
    snapshot = build_pending_studio_command_snapshot(
        production_name="Luxury Wellness Campaign",
        graph_state=build_production_graph(
            production_plan=production_plan,
            production_schedule=production_schedule,
        ),
        review_bundle=bundle,
        actor=head,
        guidance_level="Guided",
    )
    node_guidance = snapshot["graph"]["nodes"][0]["guidance"]
    assert set(node_guidance) == {
        "guidance_level", "responsibility_now", "context", "access",
        "blockers", "waiting_on", "missing_inputs", "next_best_action",
        "what_happens_next", "escalation_required", "escalation_condition",
        "escalation_target", "detail",
    }
    assert set(snapshot["guidance"]) == {
        "your_work_now", "waiting_on", "needs_attention", "next_best_action",
    }
    assert snapshot["guidance_level"] == "Guided"
