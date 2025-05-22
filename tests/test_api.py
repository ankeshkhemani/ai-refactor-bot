import os
import time

import httpx
import jwt
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.api.main import app

load_dotenv()

APP_ID = os.getenv("GITHUB_APP_ID")
PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")
# you'll set this manually for now
INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")

# Generate JWT
if not PRIVATE_KEY_PATH:
    raise ValueError("GITHUB_PRIVATE_KEY_PATH environment variable is not set")

with open(PRIVATE_KEY_PATH, "rb") as f:
    private_key = f.read()

payload = {
    "iat": int(time.time()) - 60,
    "exp": int(time.time()) + (10 * 60),
    "iss": APP_ID,
}

jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

# Get installation access token
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Accept": "application/vnd.github+json",
}

installation_url = (
    f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
)

response = httpx.post(installation_url, headers=headers)
access_token = response.json()["token"]

# Use the token to fetch repo info
repo_owner = "ankeshkhemani"
repo_name = "CarND-Behavioral-Cloning-Project"

headers = {
    "Authorization": f"token {access_token}",
    "Accept": "application/vnd.github+json",
}

repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
r = httpx.get(repo_url, headers=headers)

print("Repo info:", r.json())

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
    pass


@pytest.mark.integration
def test_environment_variables():
    """Test environment variable handling (requires .env file)."""
    pass


@pytest.mark.integration
def test_generate_jwt():
    """Test JWT token generation (requires environment variables)."""
    pass
