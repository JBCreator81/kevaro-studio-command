from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from studio_command.models import FinalProductionPackage


def _json_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


@dataclass(frozen=True)
class GovernedExportReceipt:
    production_name: str
    decision_sequence: int
    delivery_status: str
    readiness_score: int
    manifest_sha256: str
    manifest_uri: str


def build_governed_export_manifest(
    final_package: FinalProductionPackage,
) -> dict[str, Any]:
    if final_package.approval_status != "APPROVED":
        raise ValueError(
            "Governed export requires an APPROVED final production package."
        )

    if final_package.delivery_status != "READY_FOR_DELIVERY":
        raise ValueError(
            "Governed export requires delivery_status READY_FOR_DELIVERY."
        )

    if not final_package.delivery_artifacts:
        raise ValueError(
            "Governed export requires at least one delivery artifact."
        )

    if not final_package.decision_history:
        raise ValueError(
            "Governed export requires Studio Head decision history."
        )

    latest_decision = final_package.decision_history[-1]

    if latest_decision.sequence != final_package.decision_sequence:
        raise ValueError(
            "Final package decision sequence does not match latest governed decision."
        )

    manifest = {
        "schema_version": "kevaro-studio-command.governed-export.v1",
        "production_name": final_package.production_name,
        "governance": {
            "decision_sequence": final_package.decision_sequence,
            "approval_status": final_package.approval_status,
            "active_conditions": list(final_package.active_conditions),
            "authorized_actions": list(final_package.authorized_actions),
            "decision_history": [
                entry.model_dump(mode="json")
                for entry in final_package.decision_history
            ],
        },
        "verification": {
            "readiness_score": final_package.readiness_score,
            "verification_report": _json_value(
                final_package.verification_report
            ),
            "clearance_report": _json_value(
                final_package.clearance_report
            ),
        },
        "delivery": {
            "status": final_package.delivery_status,
            "artifacts": list(final_package.delivery_artifacts),
            "final_notes": list(final_package.final_notes),
        },
        "production_package": final_package.model_dump(mode="json"),
    }

    return manifest


def canonical_manifest_bytes(
    final_package: FinalProductionPackage,
) -> bytes:
    manifest = build_governed_export_manifest(final_package)

    return json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def governed_export(
    *,
    final_package: FinalProductionPackage,
    persistence: Any,
) -> GovernedExportReceipt:
    payload = canonical_manifest_bytes(final_package)
    digest = hashlib.sha256(payload).hexdigest()

    artifact_name = (
        f"exports/decision-{final_package.decision_sequence}/"
        f"governed-manifest-{digest}.json"
    )

    manifest_uri = persistence.upload_artifact_bytes(
        production_name=final_package.production_name,
        artifact_name=artifact_name,
        data=payload,
        content_type="application/json",
    )

    return GovernedExportReceipt(
        production_name=final_package.production_name,
        decision_sequence=final_package.decision_sequence,
        delivery_status=final_package.delivery_status,
        readiness_score=final_package.readiness_score,
        manifest_sha256=digest,
        manifest_uri=manifest_uri,
    )
