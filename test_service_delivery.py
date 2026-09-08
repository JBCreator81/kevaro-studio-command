from fastapi.testclient import TestClient

from studio_command.auth import SESSION_COOKIE, issue_session

import studio_command.service as service
from studio_command.models import (
    CrewMember,
    CrewProductionAssignment,
    FinalProductionPackage,
    GovernedProductionRuntimeState,
)
from studio_command.runtime_config import RuntimeConfig


class FakePersistence:
    def __init__(self, runtime_state):
        self.runtime_state = runtime_state
        self.saved = []

    def load_runtime_state(self, production_name):
        if self.runtime_state.production_name == production_name:
            return self.runtime_state
        return None

    def save_runtime_state(self, runtime_state):
        self.saved.append(runtime_state)


class FakeReceipt:
    delivery_status = "DELIVERED"

    def __dict__(self):
        return {}


class FakeResult:
    def __init__(self, runtime_state):
        self.runtime_state = runtime_state
        self.receipt = type(
            "Receipt",
            (),
            {
                "delivery_status": "DELIVERED",
                "__dict__": {
                    "delivery_status": "DELIVERED",
                },
            },
        )()


def test_delivery_route_rejects_missing_runtime(monkeypatch):
    class MissingPersistence:
        def load_runtime_state(self, production_name):
            return None

        def load_crew_member(self, auth_subject):
            if auth_subject != "delivery-test-head":
                return None
            return CrewMember(
                user_id="delivery-test-head",
                auth_subject=auth_subject,
                display_name="Delivery Test Head",
                organization_id="test-studio",
                assignments=[CrewProductionAssignment(
                    production_name="Test Production",
                    roles=["Studio Head"],
                    studio_head=True,
                )],
            )

    monkeypatch.setattr(service, "production_persistence", MissingPersistence())
    monkeypatch.setattr(
        service.app.state,
        "runtime_config",
        RuntimeConfig(
            "local",
            "test",
            "local-environment",
            session_signing_secret="delivery-route-test-session-secret-32-bytes",
        ),
        raising=False,
    )

    client = TestClient(service.app)
    response = client.post(
        "/api/productions/Test Production/deliver",
        json={
            "production_name": "Test Production"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["reason_code"] == (
        "AUTHENTICATED_SESSION_REQUIRED"
    )

    client.cookies.set(
        SESSION_COOKIE,
        issue_session(
            "delivery-test-head",
            "delivery-route-test-session-secret-32-bytes",
        ),
    )
    authenticated = client.post(
        "/api/productions/Test Production/deliver",
        json={"production_name": "Test Production"},
    )
    assert authenticated.status_code == 404
    assert authenticated.json()["detail"] == (
        "Governed production runtime was not found."
    )


def test_delivery_route_is_registered_before_frontend_catchall():
    paths = [route.path for route in service.app.routes]

    delivery_index = paths.index(
        "/api/productions/{production_name}/deliver"
    )
    catchall_index = paths.index("/{full_path:path}")

    assert delivery_index < catchall_index


print("SERVICE GOVERNED DELIVERY ROUTE TEST: PASS")
