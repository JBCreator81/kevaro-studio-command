from datetime import datetime, timezone

import pytest

from studio_command.accountability import human_actor
from studio_command.adoption import (
    BUDGET, BRAND, CANONICAL_CONCEPT, CONFLICTING_CONCEPT, CREATIVE_STALE,
    LICENSING, PROP, UPLOAD, apply_first_party_adoption,
)
from studio_command.decisions import apply_verified_evidence_amendment
from test_evidence_amendment import amendment, runtime


def current_runtime():
    amended=apply_verified_evidence_amendment(runtime_state=runtime(),amendment=amendment())
    return amended.model_copy(update={
        "memory_snapshot":amended.memory_snapshot.model_copy(update={
            "stale_artifacts":[],
            "preserved_artifacts":["production_brief","delivery_artifacts",*CREATIVE_STALE],
            "current_stage":"CONDITIONS_BLOCK_EXECUTION",
        }),
        "execution_authorized":False,"corrective_cycle_active":False,"current_stage":"CONDITIONS_BLOCK_EXECUTION",
    })

def test_adoption_is_exact_append_only_and_preserves_two_conditions():
    before=current_runtime(); history=before.decision_history; platform=before.evidence_amendments
    updated=apply_first_party_adoption(runtime_state=before,actor=human_actor("Studio Head"),adopted_at=datetime(2026,9,6,tzinfo=timezone.utc))
    assert updated.workflow_state.active_conditions==[PROP,LICENSING]
    assert updated.decision_history==history
    assert updated.evidence_amendments[:1]==platform
    assert [x.resolved_condition for x in updated.evidence_amendments[-3:]]==[BRAND,UPLOAD,BUDGET]
    assert updated.creative_directives[-1].canonical_concept==CANONICAL_CONCEPT
    assert updated.creative_directives[-1].conflicting_concept==CONFLICTING_CONCEPT
    assert updated.memory_snapshot.stale_artifacts==CREATIVE_STALE
    assert updated.current_stage=="EVIDENCE_REFRESH_REQUIRED"
    assert sum(updated.first_party_declarations[-1].declaration["allocations"].values())==12000

def test_adoption_requires_human_studio_head_and_current_state():
    with pytest.raises(ValueError,match="Studio Head"):
        apply_first_party_adoption(runtime_state=current_runtime(),actor=human_actor("Editor","Editor"))
    stale=current_runtime(); stale=stale.model_copy(update={"memory_snapshot":stale.memory_snapshot.model_copy(update={"stale_artifacts":["research_packet"]})})
    with pytest.raises(ValueError,match="current governed"):
        apply_first_party_adoption(runtime_state=stale,actor=human_actor("Studio Head"))

def test_repeated_adoption_rejects_non_active_exact_conditions():
    adopted=apply_first_party_adoption(runtime_state=current_runtime(),actor=human_actor("Studio Head"))
    adopted=adopted.model_copy(update={"memory_snapshot":adopted.memory_snapshot.model_copy(update={"stale_artifacts":[]})})
    with pytest.raises(ValueError,match="exactly active"):
        apply_first_party_adoption(runtime_state=adopted,actor=human_actor("Studio Head"))
