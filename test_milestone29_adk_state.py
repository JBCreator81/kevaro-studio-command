from copy import deepcopy
from types import SimpleNamespace

import pytest
from google.adk.sessions.state import State

import studio_command.agent as agent
from studio_command.agent import (
    _PENDING_REVIEW_KEYS,
    _persist_pending_review_bundle,
    _project_governed_state,
)
from test_milestone1_identity import PRODUCTION, review_bundle
from test_milestone27_multicall_provenance import (
    RUN_ID,
    research_packet_for_all_calls,
    three_captured_calls,
)


class Persistence:
    def __init__(self):
        self.saved = None

    def save_pending_review_bundle(self, *, production_name, review_bundle):
        self.saved = {
            "production_name": production_name,
            "review_bundle": deepcopy(review_bundle),
        }


def live_style_values(monkeypatch):
    calls, last = three_captured_calls(monkeypatch)
    values = review_bundle()
    values["research_packet"] = research_packet_for_all_calls()
    values["parallel_search_result"] = last
    for call in calls:
        values[f"parallel_search_call:{call['function_call_id']}"] = call
    values["temp:adk-internal"] = {"must_not_persist": True}
    values["user:private-session-state"] = "must-not-persist"
    values["unapproved_application_state"] = "must-not-persist"
    return values


def run_persistence(monkeypatch, state):
    persistence = Persistence()
    monkeypatch.setattr(agent, "production_persistence", persistence)
    context = SimpleNamespace(state=state, invocation_id=RUN_ID)
    result = _persist_pending_review_bundle(context, None)
    return persistence.saved, result


def test_persist_pending_review_supports_real_adk_state(monkeypatch):
    values = live_style_values(monkeypatch)
    state = State(value=values, delta={})
    assert not hasattr(state, "items")
    saved, result = run_persistence(monkeypatch, state)
    packet = saved["review_bundle"]["research_packet"]
    assert result["pending_review_persisted"] is True
    assert saved["production_name"] == PRODUCTION
    assert len(packet["parallel_search_calls"]) == 3
    assert [
        call["provenance"]["search_id"]
        for call in packet["parallel_search_calls"]
    ] == ["search-1", "search-2", "search-3"]


def test_plain_mapping_state_remains_compatible(monkeypatch):
    saved, _ = run_persistence(monkeypatch, live_style_values(monkeypatch))
    assert saved["production_name"] == PRODUCTION
    assert len(saved["review_bundle"]["research_packet"]["evidence"]) == 3


def test_projection_is_allowlisted_and_does_not_mutate_adk_state(monkeypatch):
    values = live_style_values(monkeypatch)
    state = State(value=deepcopy(values), delta={})
    before = state.to_dict()
    projection = _project_governed_state(
        state,
        keys=_PENDING_REVIEW_KEYS,
        prefixes=("parallel_search_call:",),
    )
    assert set(_PENDING_REVIEW_KEYS).issubset(projection)
    assert len([
        key for key in projection if key.startswith("parallel_search_call:")
    ]) == 3
    assert "temp:adk-internal" not in projection
    assert "user:private-session-state" not in projection
    assert "unapproved_application_state" not in projection
    assert state.to_dict() == before
    assert not state.has_delta()


def test_no_internal_state_is_written_to_pending_bundle(monkeypatch):
    saved, _ = run_persistence(
        monkeypatch,
        State(value=live_style_values(monkeypatch), delta={}),
    )
    bundle = saved["review_bundle"]
    assert set(bundle) == set(_PENDING_REVIEW_KEYS)
    serialized = str(bundle)
    assert "must_not_persist" not in serialized
    assert "must-not-persist" not in serialized


def test_missing_optional_parallel_state_preserves_empty_provenance(monkeypatch):
    values = review_bundle()
    saved, _ = run_persistence(
        monkeypatch,
        State(value=values, delta={}),
    )
    packet = saved["review_bundle"]["research_packet"]
    assert packet["parallel_provenance"] is None
    assert packet["parallel_search_calls"] == []


def test_missing_required_review_key_still_fails_closed(monkeypatch):
    values = live_style_values(monkeypatch)
    values.pop("verification_qa_report")
    persistence = Persistence()
    monkeypatch.setattr(agent, "production_persistence", persistence)
    context = SimpleNamespace(
        state=State(value=values, delta={}),
        invocation_id=RUN_ID,
    )
    with pytest.raises(ValueError, match="verification_qa_report"):
        _persist_pending_review_bundle(context, None)
    assert persistence.saved is None
