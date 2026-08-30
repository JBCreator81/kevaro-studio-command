import json
from types import SimpleNamespace

from studio_command.models import ResearchPacket
from studio_command.tools import search_web
from studio_command.ui_snapshot import (
    build_pending_studio_command_snapshot,
    build_studio_command_snapshot,
)
from test_milestone1_identity import PRODUCTION, review_bundle
from test_milestone19 import production_plan, production_schedule
from test_milestone22 import runtime
from studio_command.graph import build_production_graph


URL = "https://example.com/exact/path?proof=parallel"


def research_packet():
    return {
        "evidence": [{
            "research_question": "What supports the production decision?",
            "finding": "The source supports a constrained launch.",
            "sources": [{
                "title": "Primary evidence", "url": URL,
                "publisher_or_domain": "example.com",
                "evidence_summary": "Relevant evidence.",
                "production_relevance": "Grounds the launch decision.",
                "confidence": "high", "provider": "Parallel",
                "citation_id": "parallel:search-123:1",
                "excerpts": ["Relevant excerpt."],
                "publish_date": "2026-08-29",
                "retrieval_metadata": {"rank": 1},
            }],
            "source_reference_ids": ["parallel:search-123:1"],
            "production_impact": "Constrain launch claims.",
            "unresolved_questions": ["Is regional evidence available?"],
            "requires_studio_head_decision": True,
        }],
        "overall_summary": "Grounded research.", "blockers": [],
        "evidence_gaps": ["Regional evidence remains unavailable."],
        "parallel_provenance": {
            "provider": "Parallel", "verification_status": "VERIFIED",
            "objective": "Ground the production decision",
            "search_queries": ["production evidence"],
            "invoked_at": "2026-08-30T12:00:00Z",
            "search_id": "search-123", "session_id": "session-456",
            "invocation_marker": "parallel-search:search-123",
            "result_count": 1, "usage": [{"name": "search", "count": 1}],
            "warnings": [], "research_node": "Research",
        },
    }


def graph():
    return build_production_graph(
        production_plan=production_plan,
        production_schedule=production_schedule,
    )


def pending_snapshot(packet=None):
    bundle = review_bundle()
    bundle["research_packet"] = packet if packet is not None else bundle["research_packet"]
    return build_pending_studio_command_snapshot(
        production_name=PRODUCTION, graph_state=graph(), review_bundle=bundle,
    )


def approved_snapshot(packet):
    return build_studio_command_snapshot(
        runtime_state=runtime, graph_state=graph(),
        approved_artifacts={"research_packet": packet},
    )


def test_parallel_provenance_serializes_and_legacy_packet_loads():
    packet = ResearchPacket.model_validate(research_packet())
    serialized = packet.model_dump(mode="json")
    assert serialized["parallel_provenance"]["provider"] == "Parallel"
    assert serialized["parallel_provenance"]["invoked_at"] == "2026-08-30T12:00:00Z"
    legacy = dict(research_packet())
    legacy.pop("parallel_provenance")
    legacy.pop("evidence_gaps")
    assert ResearchPacket.model_validate(legacy).parallel_provenance is None


def test_search_web_preserves_exact_urls_and_runtime_metadata(monkeypatch):
    result = SimpleNamespace(title="Exact", url=URL, excerpts=["one", "two"], publish_date=None)
    response = SimpleNamespace(
        search_id="search-123", session_id="session-456", results=[result],
        usage=[], warnings=[],
    )
    class Client:
        def __init__(self, api_key):
            assert api_key == "test-only-key"
        def search(self, **kwargs):
            return response
    monkeypatch.setenv("PARALLEL_API_KEY", "test-only-key")
    monkeypatch.setattr("studio_command.tools.Parallel", Client)
    output = search_web("objective", ["exact query"])
    assert output["results"][0]["url"] == URL
    assert output["results"][0]["citation_id"] == "parallel:search-123:1"
    assert output["provenance"]["verification_status"] == "VERIFIED"
    assert output["provenance"]["invocation_marker"] == "parallel-search:search-123"
    assert "test-only-key" not in json.dumps(output)


def test_research_node_and_pending_judge_snapshot_expose_citations():
    snapshot = pending_snapshot(research_packet())
    assert snapshot["node_intelligence"]["Research"]["evidence"][0]["sources"][0]["url"] == URL
    proof = snapshot["evidence_summary"]
    assert proof["status"] == "VERIFIED"
    assert proof["grounded_source_count"] == 1
    assert proof["most_relevant_citations"][0]["finding"]
    assert proof["production_identity"] == PRODUCTION


def test_approved_runtime_evidence_is_visible():
    snapshot = approved_snapshot(research_packet())
    assert snapshot["approval_status"] == "APPROVED"
    assert snapshot["evidence_summary"]["status"] == "VERIFIED"
    assert snapshot["evidence_summary"]["last_invocation_at"] == "2026-08-30T12:00:00Z"


def test_missing_parallel_metadata_fails_gracefully():
    proof = pending_snapshot()["evidence_summary"]
    assert proof["status"] == "UNAVAILABLE"
    assert proof["grounded_source_count"] == 0
    assert proof["last_invocation_at"] is None


def test_missing_key_returns_unavailable_without_blocking(monkeypatch):
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    output = search_web("objective", ["query"])
    assert output["provenance"]["verification_status"] == "UNAVAILABLE"
    assert output["results"] == []


def test_snapshots_remove_secret_material_from_research():
    packet = research_packet()
    packet["parallel_provenance"]["api_key"] = "must-not-appear"
    packet["parallel_provenance"]["authorization"] = "Bearer must-not-appear"
    serialized = json.dumps(pending_snapshot(packet))
    assert "must-not-appear" not in serialized
    assert "api_key" not in serialized
    assert "authorization" not in serialized


def test_parallel_provenance_persists_in_pending_review():
    from studio_command.persistence import ProductionPersistence, ProductionPersistenceConfig
    from test_milestone1_identity import Firestore, Storage
    store = ProductionPersistence(
        config=ProductionPersistenceConfig(project_id="test"),
        firestore_client=Firestore(), storage_client=Storage(),
    )
    bundle = review_bundle()
    bundle["research_packet"] = research_packet()
    store.save_pending_review_bundle(production_name=PRODUCTION, review_bundle=bundle)
    loaded = store.load_pending_review_bundle(PRODUCTION)
    assert loaded["research_packet"]["parallel_provenance"]["search_id"] == "search-123"
    assert loaded["research_packet"]["evidence"][0]["sources"][0]["url"] == URL
