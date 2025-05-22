"""FastAPI application for the AI Refactor Bot."""

import hashlib
import hmac
import os
import time

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.code_scanner import GitHubConfig, fetch_python_files
from core.github_pr import GitHubPRConfig, create_pr_for_file_change

load_dotenv()

app = FastAPI(
    title="AI Refactoring Bot",
    description=(
        "GitHub-integrated tool that automatically scans Python repositories "
        "for technical debt and generates refactoring suggestions"
    ),
    version="1.0.0",
)


class WebhookPayload(BaseModel):
    action: str
    pull_request: dict = None
    repository: dict = None


class AppConfig:
    def __init__(self):
        self.github_app_id = os.getenv("GITHUB_APP_ID")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET")
        self.private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
        self.installation_id = os.getenv("GITHUB_INSTALLATION_ID")
        self.repo_owner = os.getenv("REPO_OWNER")
        self.repo_name = os.getenv("REPO_NAME")

        if not all(
            [
                self.github_app_id,
                self.webhook_secret,
                self.private_key_path,
                self.installation_id,
                self.repo_owner,
                self.repo_name,
            ]
        ):
            raise ValueError(
                "Missing required environment variables. Please set GITHUB_APP_ID, "
                "WEBHOOK_SECRET, GITHUB_PRIVATE_KEY_PATH, GITHUB_INSTALLATION_ID, "
                "REPO_OWNER, and REPO_NAME."
            )

        self.github_config = GitHubConfig()
        self.pr_config = GitHubPRConfig()


config = AppConfig()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook(request: Request):
    """Handle GitHub webhook events."""
    # Verify webhook signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=401, detail="No signature provided")

    payload = await request.body()
    expected_signature = hmac.new(
        config.webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(f"sha256={expected_signature}", signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse webhook payload
    data = await request.json()
    webhook_data = WebhookPayload(**data)

    # Handle pull request events
    if webhook_data.action == "opened":
        # Get changed files
        files = await fetch_python_files(config.github_config)

        # Create PR for each changed file
        for file_path, content in files.items():
            # TODO: Implement actual refactoring logic
            new_content = content  # Placeholder

            await create_pr_for_file_change(
                config.pr_config,
                file_path,
                new_content,
                f"Refactor {file_path}",
                f"Automated refactoring of {file_path}",
                f"Refactored {file_path}",
            )

    return JSONResponse(content={"status": "success"})


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Refactor Bot is running"}


def generate_jwt() -> str:
    """Generate a JWT for GitHub App authentication."""
    with open(config.private_key_path) as f:
        private_key = f.read()

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": config.github_app_id,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,  # Enable auto-reload during development
    )
