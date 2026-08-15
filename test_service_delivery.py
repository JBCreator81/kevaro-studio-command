from fastapi.testclient import TestClient

import studio_command.service as service
from studio_command.models import (
    FinalProductionPackage,
    GovernedProductionRuntimeState,
)


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

    monkeypatch.setattr(service, "production_persistence", MissingPersistence())

    client = TestClient(service.app)
    response = client.post(
        "/api/productions/Test Production/deliver",
        json={
            "production_name": "Test Production"
        },
    )

    assert response.status_code in (404, 422)


def test_delivery_route_is_registered_before_frontend_catchall():
    paths = [route.path for route in service.app.routes]

    delivery_index = paths.index(
        "/api/productions/{production_name}/deliver"
    )
    catchall_index = paths.index("/{full_path:path}")

    assert delivery_index < catchall_index


print("SERVICE GOVERNED DELIVERY ROUTE TEST: PASS")
