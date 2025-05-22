import os
import time

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from gidgethub import routing, sansio
from pydantic import BaseModel

from core.code_scanner import scan_repository

load_dotenv()

app = FastAPI(
    title="AI Refactoring Bot",
    description=(
        "GitHub-integrated tool that automatically scans Python repositories "
        "for technical debt and generates refactoring suggestions"
    ),
    version="1.0.0",
)

router = routing.Router()

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

"""
# For Private Repo
PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")

with open(PRIVATE_KEY_PATH, "rb") as key_file:
    PRIVATE_KEY = key_file.read()
"""

# For Public repo using railway
PRIVATE_KEY: bytes
private_key_str = os.getenv("PRIVATE_KEY")
if not private_key_str:
    raise ValueError("PRIVATE_KEY environment variable is not set")
PRIVATE_KEY = private_key_str.encode()


class GitHubEvent(BaseModel):
    """Represents a GitHub webhook event payload."""


async def installation_handler(event: sansio.Event) -> JSONResponse:
    """Handle GitHub App installation events"""
    # Check if installation is for selected repositories or all repositories.
    # If for all repositories, then fetch all repository names using Github API.
    # For each repository, begin code_scanning using scan_repository function
    # Generate JWT token to call Github API
    # Call scan_repository function for each repository
    """
    Installation event payload
    {
        "action": "created",  # also possible: "deleted"
        "installation": {
            "id": 12345678,
            "account": {
                "login": "username",
                ...
            },
            "repository_selection": "selected",  # or "all"
            "app_id": 9876,
            ...
        },
        "repositories": [
            {
                "id": 11111111,
                "name": "example-repo",
                ...
            }
        ],
        "sender": {
            "login": "username"
        }
    }
    """
    # Get the installation ID from the event
    # installation_id = event.data["installation"]["id"]
    # Get the installation access token
    # installation_access_token = get_installation_access_token(installation_id)
    # Call scan_repository function for each repository
    scan_repository()  # No arguments needed as it uses environment variables
    # Return success
    return JSONResponse(
        content={"status": "success", "event": "installation"}, status_code=200
    )


@app.get("/ping")
async def ping():
    """Health check endpoint that returns a pong message."""
    return {"status": "ok", "message": "pong"}


@app.post("/webhook")
async def webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_github_delivery: str = Header(None),
    x_hub_signature: str = Header(None),
):
    """
    Handle GitHub webhook events
    """
    if not all([x_github_event, x_github_delivery, x_hub_signature]):
        raise HTTPException(status_code=400, detail="Missing required GitHub headers")

    # Get the raw payload
    payload = await request.body()

    try:
        # Verify the webhook signature
        event = sansio.Event.from_http(
            {
                "X-GitHub-Event": x_github_event,
                "X-GitHub-Delivery": x_github_delivery,
                "X-Hub-Signature": x_hub_signature,
            },
            payload,
            secret=WEBHOOK_SECRET,
        )

        # Process the event
        print(f"📦 Received GitHub event: {x_github_event}")
        print(f"Delivery ID: {x_github_delivery}")
        # For installation event, we run the installation_handler
        if x_github_event == "installation":
            return await installation_handler(event)

        # For other events, we return success
        return JSONResponse(
            content={"status": "success", "event": x_github_event}, status_code=200
        )

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


def generate_jwt() -> str:
    """Generate a JWT token for GitHub App authentication"""
    return jwt.encode(
        {
            "iat": int(time.time()),
            "exp": int(time.time()) + (10 * 60),
            "iss": GITHUB_APP_ID,
        },
        PRIVATE_KEY,
        algorithm="RS256",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,  # Enable auto-reload during development
    )
