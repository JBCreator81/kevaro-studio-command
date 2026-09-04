from fastapi.testclient import TestClient

import studio_command.service as service
from studio_command.auth import SESSION_COOKIE, issue_session
from studio_command.models import CrewMember, CrewProductionAssignment
from studio_command.runtime_config import RuntimeConfig
from test_milestone10 import make_package


SECRET = "decision-request-test-secret-at-least-32-bytes"
PRODUCTION = "Luxury Wellness Campaign"
BLOCKERS = [
    "Brand approval remains unresolved.",
    "Final music clearance remains unresolved.",
]


class DecisionStore:
    def __init__(self):
        self.runtime = None
        self.artifacts = None
        self.member = CrewMember(
            user_id="head-1",
            auth_subject="head-subject",
            display_name="Morgan Lee",
            organization_id="kevaro-studios",
            assignments=[
                CrewProductionAssignment(
                    production_name=PRODUCTION,
                    roles=["Producer"],
                    studio_head=True,
                )
            ],
        )
        self.bundle = {
            "production_brief": {"required_deliverables": ["Hero film"]},
            "research_packet": {},
            "creative_treatment": {},
            "production_plan": {},
            "production_schedule": {},
            "asset_media_plan": {},
            "clearance_compliance_report": {},
            "verification_qa_report": {},
        }
        self.package = make_package(
            blockers=BLOCKERS,
            recommendation="APPROVE WITH CONDITIONS",
        ).model_dump(mode="json")

    def load_crew_member(self, subject):
        return self.member if subject == self.member.auth_subject else None

    def load_runtime_state(self, production_name):
        return self.runtime

    def load_pending_decision_package(self, production_name):
        return self.package

    def load_pending_review_bundle(self, production_name):
        return self.bundle

    def save_runtime_state(self, runtime_state):
        self.runtime = runtime_state

    def save_approved_artifacts(self, *, production_name, approved_artifacts):
        self.artifacts = approved_artifacts


def client(monkeypatch):
    store = DecisionStore()
    config = RuntimeConfig(
        "local", "test", "local-environment", session_signing_secret=SECRET
    )
    monkeypatch.setattr(service.app.state, "runtime_config", config, raising=False)
    monkeypatch.setattr(service, "production_persistence", store)
    test_client = TestClient(service.app)
    test_client.cookies.set(
        SESSION_COOKIE, issue_session(store.member.auth_subject, SECRET)
    )
    return test_client, store


def test_decision_openapi_uses_one_json_request_model():
    operation = service.app.openapi()["paths"][
        "/api/productions/{production_name}/decision"
    ]["post"]

    assert [item["name"] for item in operation["parameters"]] == [
        "production_name"
    ]
    schema = operation["requestBody"]["content"]["application/json"]["schema"]
    assert schema["$ref"].endswith("/StudioHeadDecisionRequest")


def test_conditional_approval_json_preserves_blockers_and_human_identity(monkeypatch):
    test_client, store = client(monkeypatch)

    response = test_client.post(
        f"/api/productions/{PRODUCTION}/decision",
        json={
            "decision": "APPROVE WITH CONDITIONS",
            "conditions": BLOCKERS + ["Publish only after written sign-off."],
            "decision_notes": "Proceed only under all stated conditions.",
            "unresolved_risks_acknowledged": BLOCKERS,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED_WITH_CONDITIONS"
    assert response.json()["active_conditions"] == BLOCKERS + [
        "Publish only after written sign-off."
    ]
    assert store.runtime.decision_history[0].decided_by == "Morgan Lee"
    assert store.runtime.decision_history[0].unresolved_risks_acknowledged == BLOCKERS
    assert store.artifacts is not None


def test_conditional_approval_cannot_replace_material_blockers(monkeypatch):
    test_client, store = client(monkeypatch)

    response = test_client.post(
        f"/api/productions/{PRODUCTION}/decision",
        json={
            "decision": "APPROVE WITH CONDITIONS",
            "conditions": ["A generic condition."],
        },
    )

    assert response.status_code == 409
    assert "must preserve every material blocker" in response.json()["detail"]
    assert store.runtime is None
    assert store.artifacts is None
