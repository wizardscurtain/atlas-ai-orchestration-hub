import os
from pathlib import Path

from dotenv import dotenv_values
from fastapi.testclient import TestClient

from app.main import APP_PASSWORD, ROOT_DIR, STATIC_DIR, TEMPLATES_DIR, app


# Regression checks for env loading, auth password usage, and project paths.
def test_app_password_loaded_from_real_env_file():
    env_file = ROOT_DIR / ".env"
    assert env_file.exists()

    env_values = dotenv_values(env_file)
    assert "APP_PASSWORD" in env_values
    assert env_values["APP_PASSWORD"] == APP_PASSWORD


def test_auth_accepts_password_from_environment_value():
    client = TestClient(app)
    expected_password = os.environ["APP_PASSWORD"]

    response = client.post(
        "/auth/login",
        data={"password": expected_password},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_template_and_static_use_stable_project_paths():
    assert ROOT_DIR == Path("/app")
    assert TEMPLATES_DIR == Path("/app/templates")
    assert STATIC_DIR == Path("/app/static")
    assert TEMPLATES_DIR.exists()
    assert STATIC_DIR.exists()
