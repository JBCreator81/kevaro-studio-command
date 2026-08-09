from typing import List

from .models import StudioHeadDecisionPackage, StudioHeadDecisionRecord


ALLOWED_STUDIO_HEAD_DECISIONS = {
    "APPROVE",
    "APPROVE WITH CONDITIONS",
    "REQUEST CHANGES",
    "REJECT",
}


def record_studio_head_decision(
    *,
    production_name: str,
    decision: str,
    conditions: List[str],
    decision_notes: str,
    decided_by: str,
    decision_package: StudioHeadDecisionPackage,
    unresolved_risks_acknowledged: List[str],
) -> StudioHeadDecisionRecord:
    normalized_decision = decision.strip().upper()

    if normalized_decision not in ALLOWED_STUDIO_HEAD_DECISIONS:
        raise ValueError(
            "Invalid Studio Head decision. Expected APPROVE, "
            "APPROVE WITH CONDITIONS, REQUEST CHANGES, or REJECT."
        )

    if not decided_by.strip():
        raise ValueError("A human Studio Head identity is required.")

    if "agent" in decided_by.strip().lower():
        raise ValueError(
            "Studio Head authority cannot be attributed to an autonomous agent."
        )

    if (
        normalized_decision == "APPROVE WITH CONDITIONS"
        and not conditions
    ):
        raise ValueError(
            "APPROVE WITH CONDITIONS requires at least one explicit condition."
        )

    if (
        normalized_decision == "APPROVE"
        and decision_package.material_blockers
    ):
        raise ValueError(
            "Unconditional approval is not allowed while material blockers remain."
        )

    recommendation = decision_package.recommended_decision.strip().upper()

    if normalized_decision in {"APPROVE", "APPROVE WITH CONDITIONS"}:
        next_action = "Advance production according to the human Studio Head decision."
    elif normalized_decision == "REQUEST CHANGES":
        next_action = "Route the production package for corrective work and re-review."
    else:
        next_action = "Stop the current production path and record the rejection."

    return StudioHeadDecisionRecord(
        production_name=production_name.strip(),
        decision=normalized_decision,
        conditions=conditions,
        decision_notes=decision_notes.strip(),
        decided_by=decided_by.strip(),
        source_recommendation=recommendation,
        recommendation_followed=normalized_decision == recommendation,
        unresolved_risks_acknowledged=unresolved_risks_acknowledged,
        next_action=next_action,
    )
