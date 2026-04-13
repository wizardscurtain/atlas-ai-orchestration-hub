"""Deployment regression tests for public health and startup surface."""

import os
import sys
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from fastapi.testclient import TestClient


load_dotenv(Path("/app/frontend/.env"))
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(scope="module")
def api_base_url():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL is not set")
    return BASE_URL.rstrip("/")


def test_health_endpoint_is_public_and_returns_200(api_base_url):
    """Health endpoint should be public for deployment probes."""
    response = requests.get(f"{api_base_url}/health", timeout=20)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert isinstance(payload["version"], str)
    assert payload["mongo"] in {"deferred", "connected", "unavailable"}


def test_public_root_loads_without_auth_redirect_loop(api_base_url):
    """Preview root should render login HTML for public users."""
    response = requests.get(f"{api_base_url}/", timeout=20, allow_redirects=True)

    assert response.status_code == 200
    assert "Atlas Orchestration Hub" in response.text


def test_backend_app_import_and_startup_surface():
    """Backend import should succeed and expose app metadata endpoint."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/app-meta")

    assert response.status_code == 200
    assert isinstance(response.json().get("version"), str)
