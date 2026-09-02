from copy import deepcopy
from types import SimpleNamespace

import pytest

from studio_command.agent import _govern_research_packet
from studio_command.models import ProductionPlan, ProductionSchedule, ResearchPacket
from studio_command.graph import build_production_graph
from studio_command.persistence import ProductionPersistence, ProductionPersistenceConfig
from studio_command.runtime_config import RuntimeConfig
from studio_command.tools import search_web
from studio_command.ui_snapshot import build_pending_studio_command_snapshot
from test_milestone1_identity import Firestore, PRODUCTION, Storage, review_bundle


RUN_ID = "governed-research-run-27"


def three_captured_calls(monkeypatch):
    responses = [
        SimpleNamespace(
            search_id=f"search-{index}",
            session_id=f"session-{index}",
            results=[SimpleNamespace(
                title=f"Source {index}",
                url=(
                    "https://example.com/duplicate"
                    if index > 1 else "https://example.com/one"
                ),
                excerpts=[f"Excerpt {index}"],
                publish_date=f"2026-09-0{index}",
            )],
            usage=[],
            warnings=[],
        )
        for index in range(1, 4)
    ]

    class Client:
        def __init__(self, api_key):
            assert api_key == "test-only-key"

        def search(self, **kwargs):
            return responses.pop(0)

    monkeypatch.setattr("studio_command.tools.Parallel", Client)
    state = {}
    config = RuntimeConfig(
        "local", "test", "test", parallel_api_key="test-only-key"
    )
    for index in range(1, 4):
        context = SimpleNamespace(
            state=state,
            function_call_id=f"function-{index}",
            invocation_id=RUN_ID,
        )
        search_web(
            f"Objective {index}",
            [f"query {index}"],
            runtime_config=config,
            tool_context=context,
        )
    return [
        value for key, value in state.items()
        if key.startswith("parallel_search_call:")
    ], state["parallel_search_result"]


def research_packet_for_all_calls():
    return {
        "evidence": [
            {
                "research_question": f"Question {index}",
                "finding": f"Finding {index}",
                "sources": [{
                    "title": f"Source {index}",
                    "url": (
                        "https://example.com/duplicate"
                        if index > 1 else "https://example.com/one"
                    ),
                    "publisher_or_domain": "example.com",
                    "evidence_summary": f"Summary {index}",
                    "production_relevance": f"Relevance {index}",
                    "confidence": "high",
                    "citation_id": f"parallel:search-{index}:1",
                }],
                "production_impact": f"Impact {index}",
                "unresolved_questions": [],
                "requires_studio_head_decision": False,
            }
            for index in range(1, 4)
        ],
        "overall_summary": "Three-call governed research.",
        "blockers": [],
        "evidence_gaps": [],
    }


def govern_all(calls, last):
    return _govern_research_packet(
        research_packet_for_all_calls(),
        last,
        parallel_search_calls=calls,
        research_run_id=RUN_ID,
        production_name=PRODUCTION,
    )


def test_three_parallel_calls_retain_ordered_provenance(monkeypatch):
    calls, last = three_captured_calls(monkeypatch)
    packet = govern_all(calls, last)
    assert len(packet["parallel_search_calls"]) == 3
    assert [
        call["call_index"] for call in packet["parallel_search_calls"]
    ] == [1, 2, 3]
    assert [
        call["provenance"]["search_id"]
        for call in packet["parallel_search_calls"]
    ] == ["search-1", "search-2", "search-3"]


def test_citations_from_every_call_validate_and_keep_association(monkeypatch):
    calls, last = three_captured_calls(monkeypatch)
    packet = govern_all(calls, last)
    sources = [record["sources"][0] for record in packet["evidence"]]
    assert [item["retrieval_metadata"]["parallel_call_index"] for item in sources] == [1, 2, 3]
    assert [item["retrieval_metadata"]["parallel_search_id"] for item in sources] == ["search-1", "search-2", "search-3"]


def test_duplicate_source_urls_retain_distinct_call_provenance(monkeypatch):
    calls, last = three_captured_calls(monkeypatch)
    packet = govern_all(calls, last)
    second = packet["parallel_search_calls"][1]["results"][0]
    third = packet["parallel_search_calls"][2]["results"][0]
    assert second["url"] == third["url"]
    assert second["citation_id"] != third["citation_id"]
    assert packet["evidence"][1]["sources"][0]["retrieval_metadata"]["parallel_call_index"] == 2
    assert packet["evidence"][2]["sources"][0]["retrieval_metadata"]["parallel_call_index"] == 3


def test_citation_absent_from_all_calls_fails_closed(monkeypatch):
    calls, last = three_captured_calls(monkeypatch)
    packet = research_packet_for_all_calls()
    packet["evidence"][0]["sources"][0]["citation_id"] = "parallel:other:99"
    with pytest.raises(ValueError, match="any captured Parallel call"):
        _govern_research_packet(
            packet, last, parallel_search_calls=calls,
            research_run_id=RUN_ID, production_name=PRODUCTION,
        )


@pytest.mark.parametrize("boundary", ["run", "production"])
def test_other_run_or_production_cannot_validate(monkeypatch, boundary):
    calls, last = three_captured_calls(monkeypatch)
    calls = deepcopy(calls)
    if boundary == "run":
        calls[0]["research_run_id"] = "different-run"
        message = "different governed research run"
    else:
        calls[0]["production_identity"] = "Different Production"
        message = "different production"
    with pytest.raises(ValueError, match=message):
        govern_all(calls, last)


def test_single_call_last_result_contract_remains_compatible(monkeypatch):
    calls, last = three_captured_calls(monkeypatch)
    packet = research_packet_for_all_calls()
    packet["evidence"] = [packet["evidence"][2]]
    governed = _govern_research_packet(
        packet, last, production_name=PRODUCTION
    )
    assert governed["parallel_provenance"] == last["provenance"]
    assert len(governed["parallel_search_calls"]) == 1


def test_complete_history_persists_and_reaches_identical_projection(monkeypatch):
    calls, last = three_captured_calls(monkeypatch)
    packet = govern_all(calls, last)
    serialized = ResearchPacket.model_validate(packet).model_dump(mode="json")
    assert len(serialized["parallel_search_calls"]) == 3

    bundle = review_bundle()
    bundle["research_packet"] = packet
    persistence = ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test"),
        firestore_client=Firestore(), storage_client=Storage(),
    )
    persistence.save_pending_review_bundle(
        production_name=PRODUCTION, review_bundle=bundle,
    )
    loaded = persistence.load_pending_review_bundle(PRODUCTION)
    assert len(loaded["research_packet"]["parallel_search_calls"]) == 3
    plan = ProductionPlan.model_validate(loaded["production_plan"])
    schedule = ProductionSchedule.model_validate(loaded["production_schedule"])
    snapshot = build_pending_studio_command_snapshot(
        production_name=PRODUCTION,
        graph_state=build_production_graph(
            production_plan=plan, production_schedule=schedule
        ),
        review_bundle=loaded,
    )
    evidence = snapshot["evidence_summary"]
    assert len(evidence["search_calls"]) == 3
    assert evidence["query"]["search_queries"] == [
        "query 1", "query 2", "query 3"
    ]
    assert snapshot["node_evidence"]["Research"] == evidence
