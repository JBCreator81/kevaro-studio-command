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


from .models import ProductionWorkflowState


def derive_production_workflow_state(
    decision_record: StudioHeadDecisionRecord,
) -> ProductionWorkflowState:
    decision = decision_record.decision.strip().upper()

    if decision == "APPROVE":
        return ProductionWorkflowState(
            production_name=decision_record.production_name,
            status="APPROVED",
            active_conditions=[],
            corrective_action_required=False,
            production_may_advance=True,
            production_stopped=False,
            next_stage="DOWNSTREAM_PRODUCTION",
        )

    if decision == "APPROVE WITH CONDITIONS":
        return ProductionWorkflowState(
            production_name=decision_record.production_name,
            status="APPROVED_WITH_CONDITIONS",
            active_conditions=decision_record.conditions,
            corrective_action_required=False,
            production_may_advance=True,
            production_stopped=False,
            next_stage="CONDITIONAL_DOWNSTREAM_PRODUCTION",
        )

    if decision == "REQUEST CHANGES":
        return ProductionWorkflowState(
            production_name=decision_record.production_name,
            status="CHANGES_REQUESTED",
            active_conditions=[],
            corrective_action_required=True,
            production_may_advance=False,
            production_stopped=False,
            next_stage="CORRECTIVE_WORK",
        )

    if decision == "REJECT":
        return ProductionWorkflowState(
            production_name=decision_record.production_name,
            status="REJECTED",
            active_conditions=[],
            corrective_action_required=False,
            production_may_advance=False,
            production_stopped=True,
            next_stage="STOPPED",
        )

    raise ValueError(
        f"Unsupported Studio Head decision for workflow transition: {decision}"
    )
