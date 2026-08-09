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


from .models import ProductionDecisionHistoryEntry


def build_production_decision_history_entry(
    *,
    sequence: int,
    decision_record: StudioHeadDecisionRecord,
    workflow_state: ProductionWorkflowState,
) -> ProductionDecisionHistoryEntry:
    if sequence < 1:
        raise ValueError("Decision-history sequence must be 1 or greater.")

    if decision_record.production_name != workflow_state.production_name:
        raise ValueError(
            "Decision record and workflow state must belong to the same production."
        )

    return ProductionDecisionHistoryEntry(
        sequence=sequence,
        production_name=decision_record.production_name,
        decision=decision_record.decision,
        decided_by=decision_record.decided_by,
        source_recommendation=decision_record.source_recommendation,
        recommendation_followed=decision_record.recommendation_followed,
        resulting_status=workflow_state.status,
        next_stage=workflow_state.next_stage,
        production_may_advance=workflow_state.production_may_advance,
        corrective_action_required=workflow_state.corrective_action_required,
        production_stopped=workflow_state.production_stopped,
        active_conditions=workflow_state.active_conditions,
        unresolved_risks_acknowledged=(
            decision_record.unresolved_risks_acknowledged
        ),
        decision_notes=decision_record.decision_notes,
    )


from .models import CorrectiveWorkRecord


def build_corrective_work_record(
    *,
    history_entry: ProductionDecisionHistoryEntry,
    issues_to_correct: list[str],
    corrective_actions_completed: list[str],
    submitted_by: str,
) -> CorrectiveWorkRecord:
    if history_entry.decision != "REQUEST CHANGES":
        raise ValueError(
            "Corrective work may only originate from a REQUEST CHANGES decision."
        )

    if history_entry.next_stage != "CORRECTIVE_WORK":
        raise ValueError(
            "Decision history entry is not routed to corrective work."
        )

    if not issues_to_correct:
        raise ValueError(
            "Corrective work must identify at least one issue to correct."
        )

    ready_for_re_review = (
        len(corrective_actions_completed) >= len(issues_to_correct)
        and all(action.strip() for action in corrective_actions_completed)
    )

    return CorrectiveWorkRecord(
        production_name=history_entry.production_name,
        source_decision_sequence=history_entry.sequence,
        issues_to_correct=issues_to_correct,
        corrective_actions_completed=corrective_actions_completed,
        submitted_by=submitted_by,
        ready_for_re_review=ready_for_re_review,
        re_review_required=True,
        studio_head_reapproval_required=True,
    )


from .models import ProductionReReviewRecord


def build_production_re_review_record(
    *,
    corrective_record: CorrectiveWorkRecord,
    verification_completed: bool,
    verification_passed: bool,
) -> ProductionReReviewRecord:
    if not corrective_record.ready_for_re_review:
        raise ValueError(
            "Corrective work must be complete before formal re-review can begin."
        )

    if not corrective_record.re_review_required:
        raise ValueError(
            "Corrective work record does not require formal re-review."
        )

    if not corrective_record.studio_head_reapproval_required:
        raise ValueError(
            "Corrective work must require a fresh Studio Head decision."
        )

    if verification_passed and not verification_completed:
        raise ValueError(
            "Verification cannot pass before verification is completed."
        )

    if not verification_completed:
        next_stage = "INDEPENDENT_RE_VERIFICATION"
        may_return_to_studio_head = False
    elif not verification_passed:
        next_stage = "CORRECTIVE_WORK"
        may_return_to_studio_head = False
    else:
        next_stage = "STUDIO_HEAD_REAPPROVAL"
        may_return_to_studio_head = True

    return ProductionReReviewRecord(
        production_name=corrective_record.production_name,
        source_decision_sequence=corrective_record.source_decision_sequence,
        corrective_work_ready=corrective_record.ready_for_re_review,
        verification_required=True,
        verification_completed=verification_completed,
        verification_passed=verification_passed,
        studio_head_reapproval_required=True,
        may_return_to_studio_head=may_return_to_studio_head,
        may_advance_to_production=False,
        next_stage=next_stage,
    )


from .models import StudioHeadReapprovalRecord


def record_studio_head_reapproval(
    *,
    re_review_record: ProductionReReviewRecord,
    prior_history_entry: ProductionDecisionHistoryEntry,
    decision: str,
    conditions: list[str],
    decision_notes: str,
    decided_by: str,
    decision_package: StudioHeadDecisionPackage,
    unresolved_risks_acknowledged: list[str],
) -> StudioHeadReapprovalRecord:
    if re_review_record.next_stage != "STUDIO_HEAD_REAPPROVAL":
        raise ValueError(
            "Production is not authorized to return to the Studio Head."
        )

    if not re_review_record.verification_completed:
        raise ValueError(
            "Re-verification must be completed before Studio Head reapproval."
        )

    if not re_review_record.verification_passed:
        raise ValueError(
            "Re-verification must pass before Studio Head reapproval."
        )

    if not re_review_record.may_return_to_studio_head:
        raise ValueError(
            "Re-review record does not permit return to the Studio Head."
        )

    if re_review_record.may_advance_to_production:
        raise ValueError(
            "Re-review may not bypass the fresh Studio Head decision."
        )

    if (
        prior_history_entry.sequence
        != re_review_record.source_decision_sequence
    ):
        raise ValueError(
            "Re-review source sequence must match the prior history entry."
        )

    if (
        prior_history_entry.production_name
        != re_review_record.production_name
    ):
        raise ValueError(
            "Prior history and re-review must belong to the same production."
        )

    fresh_decision = record_studio_head_decision(
        production_name=re_review_record.production_name,
        decision=decision,
        conditions=conditions,
        decision_notes=decision_notes,
        decided_by=decided_by,
        decision_package=decision_package,
        unresolved_risks_acknowledged=unresolved_risks_acknowledged,
    )

    fresh_workflow_state = derive_production_workflow_state(
        fresh_decision
    )

    new_sequence = prior_history_entry.sequence + 1

    fresh_history_entry = build_production_decision_history_entry(
        sequence=new_sequence,
        decision_record=fresh_decision,
        workflow_state=fresh_workflow_state,
    )

    return StudioHeadReapprovalRecord(
        production_name=re_review_record.production_name,
        prior_decision_sequence=prior_history_entry.sequence,
        new_decision_sequence=new_sequence,
        re_review_stage=re_review_record.next_stage,
        fresh_human_decision_required=True,
        decision_record=fresh_decision,
        workflow_state=fresh_workflow_state,
        history_entry=fresh_history_entry,
    )
