from __future__ import annotations

from typing import Any

from .access import access_snapshot
from .accountability import STUDIO_HEAD
from .guidance import (
    derive_node_guidance,
    normalize_guidance_level,
    production_guidance_summary,
)
from .identity import require_production_identity
from .assets import asset_snapshot
from .models import (
    AccountabilityActor,
    FinalProductionPackage,
    GovernedProductionRuntimeState,
    ProductionGraphState,
)


_SENSITIVE_EVIDENCE_KEYS = {
    "api_key", "apikey", "authorization", "authorization_header",
    "headers", "secret", "token", "access_token",
}


def _secret_safe_evidence(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _secret_safe_evidence(item)
            for key, item in value.items()
            if key.lower() not in _SENSITIVE_EVIDENCE_KEYS
        }
    if isinstance(value, list):
        return [_secret_safe_evidence(item) for item in value]
    return value


def _parallel_evidence_summary(research_packet: Any) -> dict[str, Any]:
    """Derive concise, secret-safe judge proof from current or legacy research."""
    if not isinstance(research_packet, dict):
        return {
            "provider": "Parallel", "status": "NOT_RUN",
            "grounded_source_count": 0,
            "evidence_gaps": ["Research evidence was not recorded."],
            "most_relevant_citations": [], "last_invocation_at": None,
            "invocation_marker": None,
        }
    provenance = research_packet.get("parallel_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    status = provenance.get("verification_status")
    if status not in {"VERIFIED", "UNAVAILABLE", "NOT_RUN"}:
        status = "UNAVAILABLE" if research_packet else "NOT_RUN"
    citations, seen_urls = [], set()
    records = research_packet.get("evidence") or []
    for evidence in records:
        if not isinstance(evidence, dict):
            continue
        for source in evidence.get("sources") or []:
            if not isinstance(source, dict):
                continue
            url = source.get("url")
            if not isinstance(url, str) or not url or url in seen_urls:
                continue
            seen_urls.add(url)
            citations.append({
                "citation_id": source.get("citation_id"),
                "title": source.get("title"), "url": url,
                "source": source.get("publisher_or_domain"),
                "finding": evidence.get("finding"),
                "confidence": source.get("confidence"),
                "relevance": source.get("production_relevance"),
            })
    gaps = list(research_packet.get("evidence_gaps") or [])
    for evidence in records:
        if isinstance(evidence, dict):
            for gap in evidence.get("unresolved_questions") or []:
                if gap not in gaps:
                    gaps.append(gap)
    return {
        "provider": "Parallel", "status": status,
        "query": {"objective": provenance.get("objective"),
                  "search_queries": provenance.get("search_queries") or []},
        "grounded_source_count": len(seen_urls), "evidence_gaps": gaps,
        "most_relevant_citations": citations[:5],
        "last_invocation_at": provenance.get("invoked_at"),
        "invocation_marker": provenance.get("invocation_marker"),
        "production_identity": provenance.get("production_identity"),
        "research_node": provenance.get("research_node") or "Research",
        "search_id": provenance.get("search_id"),
    }


def _node_intelligence(
    artifact_source: dict[str, Any],
    package_data: dict[str, Any] | None,
) -> dict[str, Any]:
    def artifact(key: str) -> Any:
        if key in artifact_source:
            return artifact_source[key]
        if package_data is not None:
            return package_data.get(key)
        return None

    return {
        "Production Brief": artifact("production_brief"),
        "Research": _secret_safe_evidence(artifact("research_packet")),
        "Creative Development": artifact("creative_treatment"),
        "Production Planning": artifact("production_plan"),
        "Scheduling": artifact("production_schedule"),
        "Asset & Media": artifact("asset_media_plan"),
        "Clearance & Compliance": (
            artifact("clearance_report")
            or artifact("clearance_compliance_report")
        ),
        "Verification QA": (
            artifact("verification_report")
            or artifact("verification_qa_report")
        ),
        "Studio Head Decision": (
            artifact_source.get("decision_package")
            or artifact_source.get("studio_head_decision_package")
            or (
                package_data.get("decision_history")
                if package_data is not None
                else None
            )
        ),
        "Final Package": package_data,
    }


def _artifact_access(
    node_intelligence: dict[str, Any],
    actor: AccountabilityActor,
) -> dict[str, Any]:
    return {
        name: access_snapshot(
            actor=actor,
            accountability=value.get("accountability")
            if isinstance(value, dict) else None,
        )
        for name, value in node_intelligence.items()
    }


def _graph_snapshot(
    graph_state: ProductionGraphState,
    node_intelligence: dict[str, Any],
    actor: AccountabilityActor,
    guidance_level: str,
    production_stage: str,
) -> dict[str, Any]:
    guidance_items = [derive_node_guidance(
        actor=actor, node=node, graph_state=graph_state,
        artifact=(node_intelligence.get(node.node_id)
                  if isinstance(node_intelligence.get(node.node_id), dict)
                  else None),
        guidance_level=guidance_level, production_stage=production_stage,
    ) for node in graph_state.nodes]
    guidance_by_node = {item.context["node_id"]: item for item in guidance_items}
    return {
        "ready_nodes": graph_state.ready_nodes,
        "running_nodes": graph_state.running_nodes,
        "completed_nodes": graph_state.completed_nodes,
        "blocked_nodes": graph_state.blocked_nodes,
        "stale_nodes": graph_state.stale_nodes,
        "graph_complete": graph_state.graph_complete,
        "nodes": [
            {
                "node_id": node.node_id,
                "task_name": node.task_name,
                "responsible_role": node.responsible_role,
                "dependencies": node.dependencies,
                "dependents": node.dependents,
                "status": node.status,
                "parallel_with": node.can_run_in_parallel_with,
                "approval_required": node.approval_required,
                "stale_reason": node.stale_reason,
                "artifact": node_intelligence.get(node.node_id),
                "guidance": guidance_by_node[node.node_id].model_dump(mode="json"),
                "ownership": {
                    "current_owner": (
                        node.accountability.ai_agent_responsible.model_dump(
                            mode="json"
                        )
                        if node.accountability
                        and node.accountability.ai_agent_responsible
                        else None
                    ),
                    "access": access_snapshot(
                        actor=actor,
                        accountability=node.accountability,
                        status=node.status
                    ),
                },
                "accountability": {
                    "human_owner": None,
                    "ai_agent_responsible": None,
                    "responsible_role": node.responsible_role,
                    "current_status": node.status,
                    "human_final_authority": True,
                },
            }
            for node in graph_state.nodes
        ],
        "guidance_summary": production_guidance_summary(guidance_items),
    }


def build_pending_studio_command_snapshot(
    *,
    production_name: str,
    graph_state: ProductionGraphState,
    review_bundle: dict[str, Any],
    actor: AccountabilityActor = STUDIO_HEAD,
    guidance_level: str = "Standard",
    asset_registry=None,
) -> dict[str, Any]:
    guidance_level = normalize_guidance_level(guidance_level)
    canonical_name = require_production_identity(
        production_name,
        graph_state.production_name,
        review_bundle["production_plan"]["production_name"],
        review_bundle["production_schedule"]["production_name"],
        review_bundle["studio_head_decision_package"]["production_name"],
    )
    node_intelligence = _node_intelligence(review_bundle, None)
    evidence_summary = _parallel_evidence_summary(node_intelligence.get("Research"))
    evidence_summary["production_identity"] = canonical_name
    graph_snapshot = _graph_snapshot(
        graph_state, node_intelligence, actor, guidance_level,
        "STUDIO_HEAD_REVIEW",
    )
    asset_media = node_intelligence.get("Asset & Media")
    required_assets = [
        item.get("asset_name") for item in asset_media.get("asset_requirements", [])
        if isinstance(item, dict) and item.get("asset_name")
    ] if isinstance(asset_media, dict) else []
    production_assets = asset_snapshot(asset_registry, required_assets)
    if isinstance(asset_media, dict):
        node_intelligence["Asset & Media"] = {
            **asset_media, "production_assets": production_assets,
        }
    for node in graph_snapshot["nodes"]:
        node["production_assets"] = [
            item for item in production_assets["assets"]
            if item["node_id"] == node["node_id"]
        ]

    return {
        "production_name": canonical_name,
        "current_stage": "STUDIO_HEAD_REVIEW",
        "approval_status": "PENDING_STUDIO_HEAD_REVIEW",
        "decision_sequence": 0,
        "execution_authorized": False,
        "corrective_cycle_active": False,
        "active_conditions": [],
        "preserved_artifacts": [],
        "stale_artifacts": [],
        "graph": graph_snapshot,
        "node_intelligence": node_intelligence,
        "evidence_summary": evidence_summary,
        "access": _artifact_access(node_intelligence, actor),
        "accountability": {
            name: value.get("accountability")
            if isinstance(value, dict) else None
            for name, value in node_intelligence.items()
        },
        "production_package": None,
        "delivery": None,
        "guidance_level": guidance_level,
        "guidance": graph_snapshot["guidance_summary"],
        "production_assets": production_assets,
        "asset_guidance": {
            "missing_required_asset": production_assets["missing_deliverables"],
            "next_best_action": production_assets["next_required_asset_action"],
            "actions": production_assets["asset_actions"],
        },
    }


def build_studio_command_snapshot(
    *,
    runtime_state: GovernedProductionRuntimeState,
    graph_state: ProductionGraphState,
    final_package: FinalProductionPackage | None = None,
    approved_artifacts: dict[str, Any] | None = None,
    actor: AccountabilityActor = STUDIO_HEAD,
    guidance_level: str = "Standard",
    asset_registry=None,
) -> dict[str, Any]:
    guidance_level = normalize_guidance_level(guidance_level)
    require_production_identity(
        runtime_state.production_name,
        graph_state.production_name,
        *(
            [final_package.production_name]
            if final_package is not None
            else []
        ),
    )

    latest_history = runtime_state.decision_history[-1]
    package_data = (
        final_package.model_dump(mode="json")
        if final_package is not None
        else None
    )
    node_intelligence = _node_intelligence(approved_artifacts or {}, package_data)
    evidence_summary = _parallel_evidence_summary(node_intelligence.get("Research"))
    evidence_summary["production_identity"] = runtime_state.production_name
    graph_snapshot = _graph_snapshot(
        graph_state, node_intelligence, actor, guidance_level,
        runtime_state.current_stage,
    )
    asset_media = node_intelligence.get("Asset & Media")
    required_assets = [
        item.get("asset_name") for item in asset_media.get("asset_requirements", [])
        if isinstance(item, dict) and item.get("asset_name")
    ] if isinstance(asset_media, dict) else []
    production_assets = asset_snapshot(asset_registry, required_assets)
    if isinstance(asset_media, dict):
        node_intelligence["Asset & Media"] = {
            **asset_media, "production_assets": production_assets,
        }
    for node in graph_snapshot["nodes"]:
        node["production_assets"] = [
            item for item in production_assets["assets"]
            if item["node_id"] == node["node_id"]
        ]

    return {
        "production_name": runtime_state.production_name,
        "current_stage": runtime_state.current_stage,
        "approval_status": runtime_state.workflow_state.status,
        "decision_sequence": latest_history.sequence,
        "execution_authorized": runtime_state.execution_authorized,
        "corrective_cycle_active": runtime_state.corrective_cycle_active,
        "active_conditions": runtime_state.workflow_state.active_conditions,
        "preserved_artifacts": runtime_state.memory_snapshot.preserved_artifacts,
        "stale_artifacts": runtime_state.memory_snapshot.stale_artifacts,
        "graph": graph_snapshot,
        "node_intelligence": node_intelligence,
        "evidence_summary": evidence_summary,
        "access": _artifact_access(node_intelligence, actor),
        "accountability": {
            name: value.get("accountability")
            if isinstance(value, dict) else None
            for name, value in node_intelligence.items()
        },
        "production_package": package_data,
        "delivery": (
            {
                "status": final_package.delivery_status,
                "readiness_score": final_package.readiness_score,
                "delivery_artifacts": final_package.delivery_artifacts,
                "final_notes": final_package.final_notes,
            }
            if final_package is not None
            else None
        ),
        "guidance_level": guidance_level,
        "guidance": graph_snapshot["guidance_summary"],
        "production_assets": production_assets,
        "asset_guidance": {
            "missing_required_asset": production_assets["missing_deliverables"],
            "next_best_action": production_assets["next_required_asset_action"],
            "actions": production_assets["asset_actions"],
        },
    }
