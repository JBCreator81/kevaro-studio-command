from copy import deepcopy

import pytest

from studio_command.graph import (
    build_production_graph,
    validate_production_plan_dependencies,
)
from studio_command.models import ProductionPlan, ProductionSchedule
from studio_command.persistence import ProductionPersistence, ProductionPersistenceConfig
from test_milestone1_identity import Firestore, PRODUCTION, Storage, review_bundle


def plan_payload():
    return deepcopy(review_bundle()["production_plan"])


def validate(payload):
    validate_production_plan_dependencies(ProductionPlan.model_validate(payload))


def test_exact_task_name_dependency_passes():
    payload = plan_payload()
    payload["tasks"][1]["dependencies"] = [payload["tasks"][0]["task_name"]]
    validate(payload)


def test_two_valid_dependencies_remain_separate_entries():
    payload = plan_payload()
    expected = [payload["tasks"][0]["task_name"], payload["tasks"][1]["task_name"]]
    payload["tasks"][-1]["dependencies"] = expected
    plan = ProductionPlan.model_validate(payload)
    validate_production_plan_dependencies(plan)
    assert plan.tasks[-1].dependencies == expected


@pytest.mark.parametrize(
    "dependency",
    [
        "Consolidate Production, Schedule",
        "Research findings",
        "Unknown Production Task",
    ],
)
def test_noncanonical_dependency_fails_closed(dependency):
    payload = plan_payload()
    payload["tasks"][1]["dependencies"] = [dependency]
    with pytest.raises(ValueError, match="do not exactly match canonical"):
        validate(payload)


def test_duplicate_task_names_fail_deterministically():
    payload = plan_payload()
    duplicate = payload["tasks"][0]["task_name"]
    payload["tasks"][1]["task_name"] = duplicate
    with pytest.raises(
        ValueError,
        match=rf"duplicate canonical task identities: \['{duplicate}'\]",
    ):
        validate(payload)


def test_workflow_stage_name_fails_unless_it_is_a_task_identity():
    payload = plan_payload()
    payload["tasks"][1]["dependencies"] = ["Clearance & Compliance"]
    with pytest.raises(ValueError, match="do not exactly match canonical"):
        validate(payload)

    payload["tasks"].append({
        **deepcopy(payload["tasks"][0]),
        "task_name": "Clearance & Compliance",
        "dependencies": [],
    })
    validate(payload)


def test_valid_live_style_production_plan_persists_successfully():
    bundle = review_bundle()
    plan = ProductionPlan.model_validate(bundle["production_plan"])
    schedule = ProductionSchedule.model_validate(bundle["production_schedule"])
    build_production_graph(production_plan=plan, production_schedule=schedule)
    persistence = ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test"),
        firestore_client=Firestore(),
        storage_client=Storage(),
    )
    persistence.save_pending_review_bundle(
        production_name=PRODUCTION,
        review_bundle=bundle,
    )
    assert persistence.load_pending_review_bundle(PRODUCTION) is not None
