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


from .models import (
    GovernedProductionRuntimeState,
    ProductionMemorySnapshot,
)


def build_governed_production_runtime_state(
    *,
    workflow_state: ProductionWorkflowState,
    decision_history: list[ProductionDecisionHistoryEntry],
    preserved_artifacts: list[str],
    stale_artifacts: list[str] | None = None,
) -> GovernedProductionRuntimeState:
    if not decision_history:
        raise ValueError(
            "Unified runtime requires at least one Studio Head decision-history entry."
        )

    latest_history = decision_history[-1]

    if latest_history.production_name != workflow_state.production_name:
        raise ValueError(
            "Latest decision history and workflow state must belong to the same production."
        )

    expected_sequence = list(range(1, len(decision_history) + 1))
    actual_sequence = [entry.sequence for entry in decision_history]

    if actual_sequence != expected_sequence:
        raise ValueError(
            "Decision history must be append-only and sequential beginning at 1."
        )

    if latest_history.resulting_status != workflow_state.status:
        raise ValueError(
            "Latest decision history must match the current workflow state."
        )

    execution_authorized = (
        workflow_state.production_may_advance
        and not workflow_state.production_stopped
        and workflow_state.next_stage
        in {
            "DOWNSTREAM_PRODUCTION",
            "CONDITIONAL_DOWNSTREAM_PRODUCTION",
        }
    )

    corrective_cycle_active = (
        workflow_state.corrective_action_required
        or workflow_state.next_stage
        in {
            "CORRECTIVE_WORK",
            "INDEPENDENT_RE_VERIFICATION",
            "STUDIO_HEAD_REAPPROVAL",
        }
    )

    current_stage = workflow_state.next_stage

    memory_snapshot = ProductionMemorySnapshot(
        production_name=workflow_state.production_name,
        current_stage=current_stage,
        active_decision_sequence=latest_history.sequence,
        approved_status=workflow_state.status,
        active_conditions=workflow_state.active_conditions,
        preserved_artifacts=preserved_artifacts,
        stale_artifacts=stale_artifacts or [],
        known_good_state=not workflow_state.production_stopped,
    )

    return GovernedProductionRuntimeState(
        production_name=workflow_state.production_name,
        workflow_state=workflow_state,
        decision_history=decision_history,
        memory_snapshot=memory_snapshot,
        change_impact=None,
        impact_brief=None,
        execution_authorized=execution_authorized,
        corrective_cycle_active=corrective_cycle_active,
        current_stage=current_stage,
    )


from .models import (
    ProductionChangeImpact,
    StudioHeadImpactBrief,
)


def analyze_production_change_impact(
    *,
    runtime_state: GovernedProductionRuntimeState,
    requested_change: str,
    affected_work: list[str],
    preserved_work: list[str],
    approvals_invalidated: list[str],
    clearance_recheck_required: bool,
    qa_reverification_required: bool,
    schedule_impact: str,
    delivery_impact: str,
) -> ProductionChangeImpact:
    if not requested_change.strip():
        raise ValueError(
            "A production change must include a clear requested change."
        )

    if not affected_work:
        raise ValueError(
            "Change-impact analysis must identify at least one affected production item."
        )

    overlap = set(affected_work) & set(preserved_work)

    if overlap:
        raise ValueError(
            "Affected work and preserved work must not overlap."
        )

    stale_work = list(dict.fromkeys(affected_work))

    return ProductionChangeImpact(
        production_name=runtime_state.production_name,
        requested_change=requested_change.strip(),
        affected_work=affected_work,
        preserved_work=preserved_work,
        stale_work=stale_work,
        approvals_invalidated=approvals_invalidated,
        clearance_recheck_required=clearance_recheck_required,
        qa_reverification_required=qa_reverification_required,
        schedule_impact=schedule_impact.strip(),
        delivery_impact=delivery_impact.strip(),
    )


def build_studio_head_impact_brief(
    *,
    runtime_state: GovernedProductionRuntimeState,
    command: str,
    change_impact: ProductionChangeImpact,
    scope_confirmed: bool,
    stale_decision_detected: bool,
) -> StudioHeadImpactBrief:
    if change_impact.production_name != runtime_state.production_name:
        raise ValueError(
            "Change impact and runtime state must belong to the same production."
        )

    if not command.strip():
        raise ValueError(
            "Studio Head command must not be empty."
        )

    conflict_detected = (
        bool(change_impact.approvals_invalidated)
        or change_impact.clearance_recheck_required
        or change_impact.qa_reverification_required
        or stale_decision_detected
        or not scope_confirmed
    )

    high_impact = (
        stale_decision_detected
        or not scope_confirmed
        or bool(change_impact.approvals_invalidated)
        or change_impact.clearance_recheck_required
        or change_impact.qa_reverification_required
    )

    if high_impact:
        impact_level = "HIGH"
    elif len(change_impact.affected_work) > 1:
        impact_level = "CONSEQUENTIAL"
    else:
        impact_level = "LOW"

    human_confirmation_required = impact_level in {
        "CONSEQUENTIAL",
        "HIGH",
    }

    may_execute = (
        scope_confirmed
        and not stale_decision_detected
        and not change_impact.clearance_recheck_required
        and not change_impact.qa_reverification_required
        and not change_impact.approvals_invalidated
    )

    affected_summary = ", ".join(change_impact.affected_work)

    if change_impact.preserved_work:
        preserved_summary = ", ".join(change_impact.preserved_work)
    else:
        preserved_summary = "No unaffected production work was identified."

    production_explanation = (
        f"This command affects {affected_summary}. "
        f"The following work remains valid and should be protected: "
        f"{preserved_summary}. "
        f"Schedule impact: {change_impact.schedule_impact} "
        f"Delivery impact: {change_impact.delivery_impact}"
    )

    if may_execute:
        recommended_path = (
            "Proceed with the requested change while preserving unaffected work."
        )
    else:
        recommended_path = (
            "Hold execution, resolve the flagged production impacts, "
            "refresh any invalid approvals or clearance, re-verify affected work, "
            "then return to the Studio Head for an informed decision."
        )

    return StudioHeadImpactBrief(
        production_name=runtime_state.production_name,
        command=command.strip(),
        impact_level=impact_level,
        conflict_detected=conflict_detected,
        stale_decision_detected=stale_decision_detected,
        scope_confirmed=scope_confirmed,
        production_explanation=production_explanation,
        affected_work=change_impact.affected_work,
        preserved_work=change_impact.preserved_work,
        recommended_path=recommended_path,
        human_confirmation_required=human_confirmation_required,
        may_execute=may_execute,
    )


def apply_change_impact_to_runtime(
    *,
    runtime_state: GovernedProductionRuntimeState,
    change_impact: ProductionChangeImpact,
    impact_brief: StudioHeadImpactBrief,
) -> GovernedProductionRuntimeState:
    if change_impact.production_name != runtime_state.production_name:
        raise ValueError(
            "Change impact and runtime state must belong to the same production."
        )

    if impact_brief.production_name != runtime_state.production_name:
        raise ValueError(
            "Impact Brief and runtime state must belong to the same production."
        )

    if impact_brief.command.strip() != change_impact.requested_change.strip():
        raise ValueError(
            "Impact Brief command must match the analyzed production change."
        )

    existing_preserved = list(
        runtime_state.memory_snapshot.preserved_artifacts
    )
    existing_stale = list(
        runtime_state.memory_snapshot.stale_artifacts
    )

    stale_set = set(existing_stale) | set(change_impact.stale_work)

    updated_preserved = [
        item
        for item in existing_preserved
        if item not in stale_set
    ]

    for item in change_impact.preserved_work:
        if (
            item not in updated_preserved
            and item not in stale_set
        ):
            updated_preserved.append(item)

    updated_stale = list(
        dict.fromkeys(existing_stale + change_impact.stale_work)
    )

    guarded = (
        impact_brief.human_confirmation_required
        or not impact_brief.may_execute
    )

    if guarded:
        execution_authorized = False
        current_stage = "STUDIO_HEAD_IMPACT_REVIEW"
    else:
        execution_authorized = runtime_state.execution_authorized
        current_stage = runtime_state.current_stage

    updated_memory = runtime_state.memory_snapshot.model_copy(
        update={
            "current_stage": current_stage,
            "preserved_artifacts": updated_preserved,
            "stale_artifacts": updated_stale,
            "known_good_state": True,
        }
    )

    return runtime_state.model_copy(
        update={
            "memory_snapshot": updated_memory,
            "change_impact": change_impact,
            "impact_brief": impact_brief,
            "execution_authorized": execution_authorized,
            "corrective_cycle_active": (
                runtime_state.corrective_cycle_active
                or bool(change_impact.stale_work)
                or change_impact.qa_reverification_required
                or change_impact.clearance_recheck_required
            ),
            "current_stage": current_stage,
        }
    )


from .models import ProductionExecutionAuthorization


def build_production_execution_authorization(
    *,
    runtime_state: GovernedProductionRuntimeState,
    requested_actions: list[str],
) -> ProductionExecutionAuthorization:
    if not requested_actions:
        raise ValueError(
            "Execution authorization requires at least one requested production action."
        )

    latest_history = runtime_state.decision_history[-1]

    if latest_history.production_name != runtime_state.production_name:
        raise ValueError(
            "Latest human decision must belong to the governed production."
        )

    human_authority_confirmed = bool(
        latest_history.decided_by.strip()
        and "agent" not in latest_history.decided_by.lower()
    )

    blocked_reasons: list[str] = []

    if not human_authority_confirmed:
        blocked_reasons.append(
            "Current execution state is not backed by confirmed human Studio Head authority."
        )

    if not runtime_state.execution_authorized:
        blocked_reasons.append(
            "The governed runtime does not currently authorize downstream production."
        )

    if runtime_state.corrective_cycle_active:
        blocked_reasons.append(
            "Corrective work or re-verification is still active."
        )

    if runtime_state.current_stage == "STUDIO_HEAD_IMPACT_REVIEW":
        blocked_reasons.append(
            "A consequential production change is awaiting Studio Head impact review."
        )

    if runtime_state.memory_snapshot.stale_artifacts:
        blocked_reasons.append(
            "Production contains stale work that must be refreshed before execution."
        )

    workflow_state = runtime_state.workflow_state

    if workflow_state.production_stopped:
        blocked_reasons.append(
            "The Studio Head stopped this production path."
        )

    if workflow_state.status == "CHANGES_REQUESTED":
        blocked_reasons.append(
            "The Studio Head requested changes before production may continue."
        )

    if workflow_state.status == "REJECTED":
        blocked_reasons.append(
            "The Studio Head rejected the current production path."
        )

    if blocked_reasons:
        return ProductionExecutionAuthorization(
            production_name=runtime_state.production_name,
            decision_sequence=latest_history.sequence,
            authorization_status="BLOCKED",
            execution_mode="BLOCKED",
            source_stage=runtime_state.current_stage,
            active_conditions=workflow_state.active_conditions,
            authorized_actions=[],
            blocked_actions=requested_actions,
            blockers=blocked_reasons,
            human_authority_confirmed=human_authority_confirmed,
            may_execute=False,
        )

    if workflow_state.status == "APPROVED_WITH_CONDITIONS":
        authorization_status = "AUTHORIZED_WITH_CONDITIONS"
        execution_mode = "CONDITIONAL"
        active_conditions = workflow_state.active_conditions
    elif workflow_state.status == "APPROVED":
        authorization_status = "AUTHORIZED"
        execution_mode = "UNCONDITIONAL"
        active_conditions = []
    else:
        return ProductionExecutionAuthorization(
            production_name=runtime_state.production_name,
            decision_sequence=latest_history.sequence,
            authorization_status="BLOCKED",
            execution_mode="BLOCKED",
            source_stage=runtime_state.current_stage,
            active_conditions=workflow_state.active_conditions,
            authorized_actions=[],
            blocked_actions=requested_actions,
            blockers=[
                f"Workflow status {workflow_state.status} does not authorize downstream execution."
            ],
            human_authority_confirmed=human_authority_confirmed,
            may_execute=False,
        )

    return ProductionExecutionAuthorization(
        production_name=runtime_state.production_name,
        decision_sequence=latest_history.sequence,
        authorization_status=authorization_status,
        execution_mode=execution_mode,
        source_stage=runtime_state.current_stage,
        active_conditions=active_conditions,
        authorized_actions=requested_actions,
        blocked_actions=[],
        blockers=[],
        human_authority_confirmed=True,
        may_execute=True,
    )
