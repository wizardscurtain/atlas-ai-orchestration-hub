import os
import secrets

import pytest
from fastapi.testclient import TestClient

from app.main import APP_PASSWORD, APP_VERSION, app
from app.models import MCPIntegration, PersonaVariant, RAGConfiguration
from app.state import OrchestrationState, state


@pytest.fixture(autouse=True)
def clean_database_state():
    state.variants.clear()
    state._authenticated_sessions.clear()
    yield
    state.variants.clear()
    state._authenticated_sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_mongo_env_values_are_available():
    assert os.environ["MONGO_URL"]
    assert os.environ["DB_NAME"]


def test_variants_and_sessions_persist_across_state_instances():
    variant = PersonaVariant(
        name="Persistent Atlas",
        persona_identity="Persists across app restarts",
        rag_config=RAGConfiguration(enabled=True, endpoint_url="https://example.com"),
        mcp_integration=MCPIntegration(web_search=True, memory_access=True),
    )
    session_id = secrets.token_hex(16)

    state.add_variant(variant)
    state.add_session(session_id)

    fresh_state = OrchestrationState()
    reloaded_variant = fresh_state.get_variant(variant.id)

    assert reloaded_variant is not None
    assert reloaded_variant.name == "Persistent Atlas"
    assert reloaded_variant.rag_config.enabled is True
    assert fresh_state.is_authenticated(session_id) is True

    fresh_state.variants.clear()
    fresh_state._authenticated_sessions.clear()


def test_app_meta_is_public_and_uses_current_version(client):
    response = client.get("/api/app-meta")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate"
    assert response.json()["version"] == APP_VERSION


def test_health_endpoint_is_public_and_reports_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate"
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == APP_VERSION
    assert payload["mongo"] in {"deferred", "connected", "unavailable"}


def test_dashboard_snapshot_requires_auth_and_returns_live_data(client):
    unauthenticated = client.get("/api/dashboard-snapshot", follow_redirects=False)
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["detail"] == "Not authenticated"

    login = client.post("/auth/login", data={"password": APP_PASSWORD}, follow_redirects=False)
    assert login.status_code == 302

    state.add_variant(PersonaVariant(name="Live Grid", persona_identity="Dashboard polling target"))
    snapshot = client.get("/api/dashboard-snapshot")

    assert snapshot.status_code == 200
    data = snapshot.json()
    assert data["version"] == APP_VERSION
    assert data["state"]["total_variants"] == 1
    assert data["variants"][0]["name"] == "Live Grid"


def test_variant_snapshot_requires_auth_and_returns_live_data(client):
    variant = PersonaVariant(name="Signal Watch", persona_identity="Detail sync target")
    state.add_variant(variant)

    unauthenticated = client.get(f"/api/variants/{variant.id}/snapshot", follow_redirects=False)
    assert unauthenticated.status_code == 401

    login = client.post("/auth/login", data={"password": APP_PASSWORD}, follow_redirects=False)
    assert login.status_code == 302

    state.activate_variant(variant.id)
    snapshot = client.get(f"/api/variants/{variant.id}/snapshot")

    assert snapshot.status_code == 200
    data = snapshot.json()
    assert data["version"] == APP_VERSION
    assert data["variant"]["id"] == variant.id
    assert data["variant"]["status"] == "active"
    assert len(data["variant"]["mission_log"]) == 1


def test_authenticated_pages_render_sync_status_panel(client):
    login = client.post("/auth/login", data={"password": APP_PASSWORD}, follow_redirects=False)
    assert login.status_code == 302

    variant = PersonaVariant(name="Sync Ready", persona_identity="Page sync target")
    state.add_variant(variant)

    dashboard = client.get("/dashboard")
    detail = client.get(f"/variants/{variant.id}")
    form_page = client.get("/variants/new")

    assert 'data-testid="sync-status-panel"' in dashboard.text
    assert 'data-sync-mode="dashboard"' in dashboard.text
    assert 'data-testid="sync-status-panel"' in detail.text
    assert 'data-sync-mode="variant-detail"' in detail.text
    assert 'data-testid="sync-status-panel"' in form_page.text
    assert 'data-sync-mode="app-meta"' in form_page.text