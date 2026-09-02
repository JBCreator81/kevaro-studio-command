from pathlib import Path

import studio_command.service as service
from studio_command.ui_snapshot import (
    build_pending_studio_command_snapshot,
    build_studio_command_snapshot,
)
from test_milestone1_identity import PRODUCTION, review_bundle
from test_milestone19 import production_plan, production_schedule
from test_milestone22 import runtime
from studio_command.graph import build_production_graph


SAFE_URL = "https://evidence.example/report"


def packet(url=SAFE_URL):
    return {
        "evidence": [{
            "research_question": "What evidence governs the launch claim?",
            "finding": "The recorded source limits the claim.",
            "sources": [{
                "title": "Governed source",
                "url": url,
                "publisher_or_domain": "evidence.example",
                "evidence_summary": "The report supports a limited claim.",
                "production_relevance": "Constrains launch copy.",
                "confidence": "high",
                "provider": "Parallel",
                "citation_id": "parallel:live-search:1",
                "publish_date": "2026-09-01",
            }],
            "production_impact": "Use qualified launch copy.",
            "unresolved_questions": ["Has the regional edition shipped?"],
            "requires_studio_head_decision": True,
        }],
        "overall_summary": "One governed source was returned.",
        "blockers": [],
        "evidence_gaps": ["Regional evidence is unresolved."],
        "parallel_provenance": {
            "provider": "Parallel",
            "verification_status": "VERIFIED",
            "objective": "Verify launch support",
            "search_queries": ["launch evidence"],
            "invoked_at": "2026-09-02T10:00:00Z",
            "search_id": "live-search",
            "invocation_marker": "parallel-search:live-search",
            "result_count": 1,
            "research_node": "Research",
            "production_identity": PRODUCTION,
        },
    }


def graph():
    return build_production_graph(
        production_plan=production_plan,
        production_schedule=production_schedule,
    )


def test_real_runtime_evidence_projection_is_complete_and_consistent():
    snapshot = build_studio_command_snapshot(
        runtime_state=runtime,
        graph_state=graph(),
        approved_artifacts={"research_packet": packet()},
    )
    evidence = snapshot["evidence_summary"]
    research = snapshot["node_intelligence"]["Research"]
    assert evidence["production_identity"] == snapshot["production_name"] == PRODUCTION
    assert evidence["query"]["objective"] == "Verify launch support"
    assert evidence["last_invocation_at"] == "2026-09-02T10:00:00Z"
    assert evidence["findings"][0]["finding"] == research["evidence"][0]["finding"]
    assert evidence["findings"][0]["sources"][0]["url"] == research["evidence"][0]["sources"][0]["url"]
    assert evidence["most_relevant_citations"][0]["evidence_summary"]
    assert evidence["most_relevant_citations"][0]["confidence"] == "high"
    assert evidence["evidence_gaps"] == [
        "Regional evidence is unresolved.",
        "Has the regional edition shipped?",
    ]


def test_absent_evidence_stays_visibly_empty():
    bundle = review_bundle()
    bundle["research_packet"] = {}
    evidence = build_pending_studio_command_snapshot(
        production_name=PRODUCTION, graph_state=graph(), review_bundle=bundle,
    )["evidence_summary"]
    assert evidence["grounded_source_count"] == 0
    assert evidence["findings"] == []
    assert evidence["most_relevant_citations"] == []
    assert evidence["status"] == "NOT_RUN"


def test_unsafe_or_missing_urls_are_retained_as_evidence_but_not_links():
    evidence = build_studio_command_snapshot(
        runtime_state=runtime,
        graph_state=graph(),
        approved_artifacts={"research_packet": packet("javascript:alert(1)")},
    )["evidence_summary"]
    assert evidence["grounded_source_count"] == 1
    assert evidence["most_relevant_citations"][0]["title"] == "Governed source"
    assert evidence["most_relevant_citations"][0]["url"] is None


def test_live_production_endpoint_carries_persisted_evidence(monkeypatch):
    approved = {
        "research_packet": packet(),
        "production_plan": production_plan.model_dump(mode="json"),
        "production_schedule": production_schedule.model_dump(mode="json"),
    }

    class Persistence:
        def load_runtime_state(self, production_name):
            assert production_name == PRODUCTION
            return runtime

        def load_approved_artifacts(self, production_name):
            assert production_name == PRODUCTION
            return approved

        def load_final_package(self, production_name):
            return None

        def load_asset_registry(self, production_name):
            return None

    monkeypatch.setattr(service, "production_persistence", Persistence())
    snapshot = service.live_studio_snapshot(PRODUCTION)
    citation = snapshot["evidence_summary"]["most_relevant_citations"][0]
    assert snapshot["production_name"] == PRODUCTION
    assert citation["citation_id"] == "parallel:live-search:1"
    assert citation["url"] == SAFE_URL


def test_frontend_uses_one_evidence_projection_and_safe_external_links():
    app = Path("frontend/src/App.jsx").read_text()
    renderer = Path("frontend/src/EvidenceDetails.jsx").read_text()
    assert app.count("evidence={evidence}") == 2
    assert 'selectedNode.node_id === "Research"' in app
    assert 'target="_blank"' in renderer
    assert 'rel="noopener noreferrer"' in renderer
    assert '"http:", "https:"' in renderer
    assert "citation-unlinked" in renderer
    assert "No citations are present in the governed state" in renderer
