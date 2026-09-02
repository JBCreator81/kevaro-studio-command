import json
from datetime import datetime
from types import SimpleNamespace

from google.adk.utils.content_utils import to_user_content

from studio_command.agent import (
    _serialize_research_handoff,
    studio_production_workflow,
)
from studio_command.models import ResearchPacket
from test_milestone1_identity import PRODUCTION
from test_milestone27_multicall_provenance import (
    govern_all,
    three_captured_calls,
)


def serialized_handoff(monkeypatch):
    calls, last = three_captured_calls(monkeypatch)
    governed = govern_all(calls, last)
    typed = ResearchPacket.model_validate(governed)
    assert isinstance(typed.parallel_provenance.invoked_at, datetime)
    assert all(
        isinstance(call.provenance.invoked_at, datetime)
        for call in typed.parallel_search_calls
    )
    context = SimpleNamespace(state={"research_packet": typed})
    serialized = _serialize_research_handoff(context, typed)
    return typed, serialized, context


def test_research_packet_datetime_crosses_json_safe_handoff(monkeypatch):
    typed, serialized, context = serialized_handoff(monkeypatch)
    json.dumps(serialized)
    assert isinstance(serialized["parallel_provenance"]["invoked_at"], str)
    assert all(
        isinstance(call["provenance"]["invoked_at"], str)
        for call in serialized["parallel_search_calls"]
    )
    assert context.state["research_packet"] == serialized
    assert typed.parallel_provenance.search_id == (
        serialized["parallel_provenance"]["search_id"]
    )


def test_json_safe_handoff_revalidates_typed_provenance(monkeypatch):
    _, serialized, _ = serialized_handoff(monkeypatch)
    revalidated = ResearchPacket.model_validate(serialized)
    assert isinstance(revalidated.parallel_provenance.invoked_at, datetime)
    assert len(revalidated.parallel_search_calls) == 3
    assert all(
        isinstance(call.provenance.invoked_at, datetime)
        for call in revalidated.parallel_search_calls
    )


def test_handoff_preserves_all_evidence_and_multicall_fields(monkeypatch):
    typed, serialized, _ = serialized_handoff(monkeypatch)
    assert len(serialized["evidence"]) == len(typed.evidence) == 3
    assert len(serialized["parallel_search_calls"]) == 3
    assert serialized["evidence_gaps"] == typed.evidence_gaps
    assert [
        source["citation_id"]
        for evidence in serialized["evidence"]
        for source in evidence["sources"]
    ] == [f"parallel:search-{index}:1" for index in range(1, 4)]
    assert all(
        call["production_identity"] == PRODUCTION
        for call in serialized["parallel_search_calls"]
    )


def test_adk_creative_handoff_accepts_serialized_research(monkeypatch):
    _, serialized, _ = serialized_handoff(monkeypatch)
    content = to_user_content(serialized)
    delivered = json.loads(content.parts[0].text)
    assert delivered == serialized
    edges = {
        (edge.from_node.name, edge.to_node.name)
        for edge in studio_production_workflow.graph.edges
    }
    assert ("research_agent", "serialize_research_handoff") in edges
    assert ("serialize_research_handoff", "creative_development_agent") in edges
