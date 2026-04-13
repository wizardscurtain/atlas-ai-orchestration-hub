import secrets

import pytest
from fastapi.testclient import TestClient

from app.main import APP_PASSWORD, APP_VERSION, app
from app.models import PersonaVariant
from app.state import OrchestrationState, state


@pytest.fixture(autouse=True)
def clean_database_state():
    """Regression scope: MongoDB-backed variants, sessions, and mission logs."""
    state.variants.clear()
    state._authenticated_sessions.clear()
    yield
    state.variants.clear()
    state._authenticated_sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_session_persists_across_client_instances():
    login_client = TestClient(app)
    login_response = login_client.post("/auth/login", data={"password": APP_PASSWORD}, follow_redirects=False)
    assert login_response.status_code == 302
    session_cookie = login_response.cookies.get("session_id")
    assert isinstance(session_cookie, str)
    assert len(session_cookie) > 0

    fresh_client = TestClient(app)
    fresh_client.cookies.set("session_id", session_cookie)
    dashboard = fresh_client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code == 200


def test_mission_log_persists_when_reloading_state_instance():
    variant = PersonaVariant(name="TEST_Mission Persist", persona_identity="Check mission history persistence")
    state.add_variant(variant)
    state.activate_variant(variant.id)
    state.deploy_variant(variant.id)

    fresh_state = OrchestrationState()
    reloaded = fresh_state.get_variant(variant.id)
    assert reloaded is not None
    assert len(reloaded.mission_log) == 2
    assert reloaded.status == "deployed"

    fresh_state.delete_variant(variant.id)


def test_dashboard_snapshot_contains_live_state_and_version(client):
    login = client.post("/auth/login", data={"password": APP_PASSWORD}, follow_redirects=False)
    assert login.status_code == 302

    created = PersonaVariant(
        name="TEST_Live Snapshot",
        persona_identity="Live snapshot should include this variant",
    )
    state.add_variant(created)

    snapshot = client.get("/api/dashboard-snapshot")
    assert snapshot.status_code == 200
    data = snapshot.json()
    assert data["version"] == APP_VERSION
    assert data["state"]["total_variants"] == 1
    assert data["variants"][0]["name"] == "TEST_Live Snapshot"