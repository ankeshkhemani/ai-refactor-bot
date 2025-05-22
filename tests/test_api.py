import os
import time

import httpx
import jwt
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.api.main import app

load_dotenv()


class TestConfig:
    def __init__(self):
        self.app_id = os.getenv("GITHUB_APP_ID")
        self.private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
        self.installation_id = os.getenv("GITHUB_INSTALLATION_ID")
        self.repo_owner = "ankeshkhemani"
        self.repo_name = "CarND-Behavioral-Cloning-Project"

    def generate_jwt(self):
        with open(self.private_key_path, "rb") as f:
            private_key = f.read()

        payload = {
            "iat": int(time.time()) - 60,
            "exp": int(time.time()) + (10 * 60),
            "iss": self.app_id,
        }

        return jwt.encode(payload, private_key, algorithm="RS256")

    def get_headers(self):
        jwt_token = self.generate_jwt()
        return {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }


# Create a test client
client = TestClient(app)


@pytest.mark.pure
def test_app_initialization():
    """Test that the FastAPI app initializes correctly."""
    assert app is not None
    assert app.title == "AI Refactoring Bot"
    assert app.version == "1.0.0"


@pytest.mark.pure
def test_ping_endpoint():
    """Test the health check endpoint."""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "pong"}


@pytest.mark.pure
def test_webhook_missing_headers():
    """Test webhook endpoint with missing headers."""
    response = client.post("/webhook")
    assert response.status_code == 400
    assert response.json() == {"detail": "Missing required GitHub headers"}


@pytest.mark.integration
def test_github_integration():
    """Test GitHub API integration (requires credentials)."""
    config = TestConfig()
    headers = config.get_headers()

    installation_url = (
        "https://api.github.com/app/installations/"
        f"{config.installation_id}/access_tokens"
    )
    response = httpx.post(installation_url, headers=headers)
    access_token = response.json()["token"]

    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json",
    }

    repo_url = (
        "https://api.github.com/repos/" f"{config.repo_owner}/" f"{config.repo_name}"
    )
    r = httpx.get(repo_url, headers=headers)
    assert r.status_code == 200


@pytest.mark.integration
def test_environment_variables():
    """Test environment variable handling (requires .env file)."""
    config = TestConfig()
    assert config.app_id is not None
    assert config.private_key_path is not None
    assert config.installation_id is not None


@pytest.mark.integration
def test_generate_jwt():
    """Test JWT token generation (requires environment variables)."""
    config = TestConfig()
    jwt_token = config.generate_jwt()
    assert jwt_token is not None
