"""Configuration and authentication for GitHub API access."""

import logging
import os
import time
from typing import Dict, Optional

import aiohttp
import jwt

logger = logging.getLogger(__name__)


class GitHubConfig:
    """Configuration for GitHub API access."""

    def __init__(self):
        """Initialize GitHub configuration."""
        self.repo_owner: Optional[str] = None
        self.repo_name: Optional[str] = None
        self.installation_id: Optional[str] = None
        self.api_url: Optional[str] = None
        self.head_ref = "main"  # Default to main branch
        self.headers: Dict[str, str] = {}

    def setup_headers(self):
        """Set up headers for GitHub API requests."""
        # Generate JWT for GitHub App authentication
        private_key = os.getenv("GITHUB_PRIVATE_KEY")
        if not private_key:
            raise ValueError("GITHUB_PRIVATE_KEY environment variable not set")

        app_id = os.getenv("GITHUB_APP_ID")
        if not app_id:
            raise ValueError("GITHUB_APP_ID environment variable not set")

        # Create JWT token with proper expiration time
        now = int(time.time())
        payload = {
            "iat": now,  # Issued at time
            "exp": now + 600,  # Expiration time (10 minutes from now)
            "iss": app_id,
        }

        try:
            jwt_token = jwt.encode(payload, private_key, algorithm="RS256")
            self.headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json",
            }
        except Exception as e:
            logger.error(f"Error generating JWT token: {str(e)}")
            raise

    async def get_installation_token(self) -> str:
        """Get installation access token from GitHub.

        Returns:
            Installation access token
        """
        if not self.installation_id:
            raise ValueError("Installation ID not set")

        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers) as response:
                if response.status != 201:
                    error_text = await response.text()
                    raise Exception(f"Failed to get installation token: {error_text}")

                data = await response.json()
                return data["token"]

    async def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a file from GitHub.

        Args:
            file_path: Path to the file in the repository

        Returns:
            File content as string, or None if file not found
        """
        if not self.api_url:
            raise ValueError("API URL not set")

        # Get installation token
        token = await self.get_installation_token()

        # Get file content
        url = f"{self.api_url}/contents/{file_path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    logger.warning(f"File not found: {file_path}")
                    return None

                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get file content: {error_text}")

                data = await response.json()
                import base64

                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
