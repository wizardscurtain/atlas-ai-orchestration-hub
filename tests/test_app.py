import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.state import state


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state between tests."""
    state.variants.clear()
    state._authenticated_sessions.clear()
    yield
    state.variants.clear()
    state._authenticated_sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    """Client that is already authenticated."""
    resp = client.post("/auth/login", data={"password": "AtlasMaster2026"}, follow_redirects=False)
    assert resp.status_code == 302
    return client


class TestAuthentication:
    def test_landing_page_shows_login(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Access Code" in resp.text

    def test_wrong_password_rejected(self, client):
        resp = client.post("/auth/login", data={"password": "wrong"}, follow_redirects=False)
        assert resp.status_code == 200
        assert "Invalid password" in resp.text

    def test_correct_password_redirects(self, client):
        resp = client.post("/auth/login", data={"password": "AtlasMaster2026"}, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/dashboard"

    def test_dashboard_requires_auth(self, client):
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302

    def test_api_requires_auth(self, client):
        resp = client.get("/api/variants", follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_logout_clears_session(self, auth_client):
        resp = auth_client.get("/auth/logout", follow_redirects=False)
        assert resp.status_code == 302
        resp2 = auth_client.get("/dashboard", follow_redirects=False)
        assert resp2.status_code == 302

    def test_authenticated_user_redirected_from_login(self, auth_client):
        resp = auth_client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/dashboard"


class TestDashboard:
    def test_dashboard_renders(self, auth_client):
        resp = auth_client.get("/dashboard")
        assert resp.status_code == 200
        assert "Command Center" in resp.text
        assert "Total Drones" in resp.text

    def test_dashboard_shows_stats(self, auth_client):
        resp = auth_client.get("/dashboard")
        assert resp.status_code == 200
        assert "0" in resp.text  # no variants initially


class TestVariantCRUD:
    def test_create_variant(self, auth_client):
        resp = auth_client.post("/api/variants", data={
            "name": "Security Alpha",
            "persona_identity": "Physical security analyst specializing in perimeter threats",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert len(state.variants) == 1
        v = list(state.variants.values())[0]
        assert v.name == "Security Alpha"
        assert v.status == "inactive"

    def test_create_variant_with_mcp_tools(self, auth_client):
        auth_client.post("/api/variants", data={
            "name": "Intel Drone",
            "persona_identity": "Intelligence gathering specialist",
            "mcp_web_search": "on",
            "mcp_email_integration": "on",
            "mcp_memory_access": "on",
        }, follow_redirects=False)
        v = list(state.variants.values())[0]
        assert v.mcp_integration.web_search is True
        assert v.mcp_integration.email_integration is True
        assert v.mcp_integration.memory_access is True
        assert v.mcp_integration.file_analysis is False

    def test_create_variant_with_rag(self, auth_client):
        auth_client.post("/api/variants", data={
            "name": "RAG Drone",
            "persona_identity": "Knowledge base specialist",
            "rag_enabled": "on",
            "rag_endpoint_url": "https://vector.example.com",
            "rag_api_key": "sk-test-key",
            "rag_collection_name": "security-intel",
        }, follow_redirects=False)
        v = list(state.variants.values())[0]
        assert v.rag_config.enabled is True
        assert v.rag_config.endpoint_url == "https://vector.example.com"
        assert v.rag_config.collection_name == "security-intel"

    def test_view_variant(self, auth_client):
        auth_client.post("/api/variants", data={
            "name": "View Test",
            "persona_identity": "Test persona",
        }, follow_redirects=False)
        vid = list(state.variants.keys())[0]
        resp = auth_client.get(f"/variants/{vid}")
        assert resp.status_code == 200
        assert "View Test" in resp.text
        assert "Test persona" in resp.text

    def test_edit_variant(self, auth_client):
        auth_client.post("/api/variants", data={
            "name": "Original",
            "persona_identity": "Original identity",
        }, follow_redirects=False)
        vid = list(state.variants.keys())[0]
        resp = auth_client.post(f"/api/variants/{vid}", data={
            "name": "Updated Name",
            "persona_identity": "Updated identity",
        }, follow_redirects=False)
        assert resp.status_code == 302
        v = state.get_variant(vid)
        assert v.name == "Updated Name"
        assert v.persona_identity == "Updated identity"

    def test_delete_variant(self, auth_client):
        auth_client.post("/api/variants", data={
            "name": "To Delete",
            "persona_identity": "Will be deleted",
        }, follow_redirects=False)
        vid = list(state.variants.keys())[0]
        resp = auth_client.post(f"/api/variants/{vid}/delete", follow_redirects=False)
        assert resp.status_code == 302
        assert len(state.variants) == 0

    def test_variant_not_found(self, auth_client):
        resp = auth_client.get("/variants/nonexistent")
        assert resp.status_code == 404


class TestVariantLifecycle:
    def _create_variant(self, auth_client):
        auth_client.post("/api/variants", data={
            "name": "Lifecycle Test",
            "persona_identity": "Lifecycle test drone",
        }, follow_redirects=False)
        return list(state.variants.keys())[0]

    def test_activate_variant(self, auth_client):
        vid = self._create_variant(auth_client)
        resp = auth_client.post(f"/api/variants/{vid}/activate", follow_redirects=False)
        assert resp.status_code == 302
        assert state.get_variant(vid).status == "active"
        assert len(state.get_variant(vid).mission_log) == 1

    def test_deploy_variant(self, auth_client):
        vid = self._create_variant(auth_client)
        state.activate_variant(vid)
        resp = auth_client.post(f"/api/variants/{vid}/deploy", follow_redirects=False)
        assert resp.status_code == 302
        assert state.get_variant(vid).status == "deployed"

    def test_deactivate_variant(self, auth_client):
        vid = self._create_variant(auth_client)
        state.activate_variant(vid)
        resp = auth_client.post(f"/api/variants/{vid}/deactivate", follow_redirects=False)
        assert resp.status_code == 302
        assert state.get_variant(vid).status == "inactive"

    def test_full_lifecycle(self, auth_client):
        vid = self._create_variant(auth_client)
        v = state.get_variant(vid)
        assert v.status == "inactive"
        auth_client.post(f"/api/variants/{vid}/activate", follow_redirects=False)
        assert state.get_variant(vid).status == "active"
        auth_client.post(f"/api/variants/{vid}/deploy", follow_redirects=False)
        assert state.get_variant(vid).status == "deployed"
        auth_client.post(f"/api/variants/{vid}/deactivate", follow_redirects=False)
        assert state.get_variant(vid).status == "inactive"
        assert len(state.get_variant(vid).mission_log) == 3


class TestCentralState:
    def test_empty_state(self, auth_client):
        resp = auth_client.get("/api/state")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_variants"] == 0
        assert data["system_health"] == "operational"

    def test_state_with_variants(self, auth_client):
        auth_client.post("/api/variants", data={
            "name": "Drone 1",
            "persona_identity": "Test",
            "mcp_web_search": "on",
            "mcp_code_execution": "on",
            "rag_enabled": "on",
            "rag_endpoint_url": "https://example.com",
        }, follow_redirects=False)
        vid = list(state.variants.keys())[0]
        state.activate_variant(vid)

        auth_client.post("/api/variants", data={
            "name": "Drone 2",
            "persona_identity": "Test 2",
        }, follow_redirects=False)

        resp = auth_client.get("/api/state")
        data = resp.json()
        assert data["total_variants"] == 2
        assert data["active_variants"] == 1
        assert data["total_mcp_tools_enabled"] == 2
        assert data["rag_endpoints_configured"] == 1

    def test_list_variants_api(self, auth_client):
        auth_client.post("/api/variants", data={
            "name": "API Test",
            "persona_identity": "For API listing",
        }, follow_redirects=False)
        resp = auth_client.get("/api/variants")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "API Test"


class TestEdgeCases:
    def test_delete_nonexistent_variant(self, auth_client):
        resp = auth_client.post("/api/variants/nonexistent/delete", follow_redirects=False)
        assert resp.status_code == 404

    def test_activate_nonexistent_variant(self, auth_client):
        resp = auth_client.post("/api/variants/nonexistent/activate", follow_redirects=False)
        assert resp.status_code == 404

    def test_update_nonexistent_variant(self, auth_client):
        resp = auth_client.post("/api/variants/nonexistent", data={
            "name": "X",
            "persona_identity": "Y",
        }, follow_redirects=False)
        assert resp.status_code == 404

    def test_edit_form_nonexistent(self, auth_client):
        resp = auth_client.get("/variants/nonexistent/edit")
        assert resp.status_code == 404
