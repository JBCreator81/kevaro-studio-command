from types import SimpleNamespace

import pytest

from studio_command.agent import _govern_research_packet
from studio_command.persistence import (
    ProductionPersistence,
    ProductionPersistenceConfig,
)
from studio_command.runtime_config import RuntimeConfig
from studio_command.tools import search_web
from studio_command.ui_snapshot import build_pending_studio_command_snapshot
from studio_command.graph import build_production_graph
from studio_command.models import ProductionPlan, ProductionSchedule
from test_milestone1_identity import Firestore, PRODUCTION, Storage, review_bundle
from test_milestone5_parallel import URL, research_packet


def store():
    return ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test"),
        firestore_client=Firestore(),
        storage_client=Storage(),
    )


def captured_parallel_result(monkeypatch):
    result = SimpleNamespace(
        title="Primary evidence",
        url=URL,
        excerpts=["Relevant excerpt."],
        publish_date="2026-08-29",
    )
    response = SimpleNamespace(
        search_id="search-123",
        session_id="session-456",
        results=[result],
        usage=[],
        warnings=[],
    )

    class Client:
        def __init__(self, api_key):
            assert api_key == "test-only-key"

        def search(self, **kwargs):
            return response

    monkeypatch.setattr("studio_command.tools.Parallel", Client)
    context = SimpleNamespace(state={})
    output = search_web(
        "Ground the production decision",
        ["production evidence"],
        runtime_config=RuntimeConfig(
            "local", "test", "test", parallel_api_key="test-only-key"
        ),
        tool_context=context,
    )
    assert context.state["parallel_search_result"] == output
    return output


def test_captured_live_parallel_provenance_survives_normal_persistence(monkeypatch):
    output = captured_parallel_result(monkeypatch)
    packet = _govern_research_packet(research_packet(), output)
    bundle = review_bundle()
    bundle["research_packet"] = packet
    persistence = store()
    persistence.save_pending_review_bundle(
        production_name=PRODUCTION,
        review_bundle=bundle,
    )
    loaded = persistence.load_pending_review_bundle(PRODUCTION)["research_packet"]
    assert loaded["parallel_provenance"] == output["provenance"]
    assert loaded["parallel_provenance"]["verification_status"] == "VERIFIED"
    assert loaded["parallel_provenance"]["search_queries"] == [
        "production evidence"
    ]
    assert loaded["evidence"][0]["sources"][0]["provider"] == "Parallel"
    assert loaded["evidence"][0]["sources"][0]["citation_id"] == (
        "parallel:search-123:1"
    )


def test_absent_captured_provenance_is_never_fabricated():
    packet = _govern_research_packet(research_packet(), None)
    assert packet["parallel_provenance"] is None


def test_uncaptured_source_fails_closed(monkeypatch):
    output = captured_parallel_result(monkeypatch)
    packet = research_packet()
    packet["evidence"][0]["sources"][0]["url"] = "https://invented.invalid"
    with pytest.raises(ValueError, match="does not match captured citation"):
        _govern_research_packet(packet, output)


def test_valid_task_dependencies_survive_persistence():
    bundle = review_bundle()
    persistence = store()
    dependencies = bundle["production_plan"]["tasks"][1]["dependencies"]
    persistence.save_pending_review_bundle(
        production_name=PRODUCTION,
        review_bundle=bundle,
    )
    loaded = persistence.load_pending_review_bundle(PRODUCTION)
    assert loaded["production_plan"]["tasks"][1]["dependencies"] == dependencies
    plan = ProductionPlan.model_validate(loaded["production_plan"])
    schedule = ProductionSchedule.model_validate(loaded["production_schedule"])
    build_production_graph(production_plan=plan, production_schedule=schedule)


def test_unknown_production_brief_dependency_fails_before_write():
    bundle = review_bundle()
    bundle["production_plan"]["tasks"][0]["dependencies"] = [
        "PRODUCTION BRIEF"
    ]
    bundle["production_schedule"]["scheduled_tasks"][0]["depends_on"] = [
        "PRODUCTION BRIEF"
    ]
    persistence = store()
    with pytest.raises(ValueError, match="unknown dependencies.*PRODUCTION BRIEF"):
        persistence.save_pending_review_bundle(
            production_name=PRODUCTION,
            review_bundle=bundle,
        )
    assert persistence.load_pending_review_bundle(PRODUCTION) is None


def test_valid_snapshot_exposes_identical_research_evidence_projection():
    bundle = review_bundle()
    bundle["research_packet"] = research_packet()
    plan = ProductionPlan.model_validate(bundle["production_plan"])
    schedule = ProductionSchedule.model_validate(bundle["production_schedule"])
    snapshot = build_pending_studio_command_snapshot(
        production_name=PRODUCTION,
        graph_state=build_production_graph(
            production_plan=plan, production_schedule=schedule
        ),
        review_bundle=bundle,
    )
    assert snapshot["node_evidence"]["Research"] == snapshot["evidence_summary"]
    assert snapshot["evidence_summary"]["most_relevant_citations"][0]["url"] == URL
