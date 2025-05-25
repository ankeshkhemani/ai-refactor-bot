"""GitHub PR utilities for the AI Refactor Bot."""

import logging
import os
import time
from typing import Dict

import httpx
import requests
from dotenv import load_dotenv

from ..utils.jwt_helper import generate_github_jwt

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Force reload environment variables
if "GITHUB_PRIVATE_KEY" in os.environ:
    del os.environ["GITHUB_PRIVATE_KEY"]
load_dotenv(override=True)

# Load private key from file if it exists
private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH", "github-private-key.pem")
if os.path.exists(private_key_path):
    with open(private_key_path, "r") as f:
        os.environ["GITHUB_PRIVATE_KEY"] = f.read()
    logging.info(f"Loaded private key from {private_key_path}")
else:
    logging.warning(f"Private key file not found at {private_key_path}")

# Debug print to check what is loaded from the .env file
if os.getenv("GITHUB_PRIVATE_KEY"):
    logging.info("GITHUB_PRIVATE_KEY loaded successfully")
    logging.info("Key starts with: " + repr(os.getenv("GITHUB_PRIVATE_KEY")[:50]))
    logging.info("Key ends with: " + repr(os.getenv("GITHUB_PRIVATE_KEY")[-50:]))
else:
    logging.error("GITHUB_PRIVATE_KEY not found in environment")


class GitHubPRConfig:
    def __init__(
        self, token: str = None, repo_owner: str = None, repo_name: str = None
    ):
        logging.info("Initializing GitHubPRConfig...")
        self.repo_owner = repo_owner or os.getenv("REPO_OWNER")
        self.repo_name = repo_name or os.getenv("REPO_NAME")
        self.app_id = os.getenv("GITHUB_APP_ID")
        self.private_key = os.getenv("GITHUB_PRIVATE_KEY")
        self.installation_id = os.getenv("GITHUB_INSTALLATION_ID")
        self.api_base = (
            f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        )
        self.api_url = self.api_base  # For compatibility with async PR creation
        self.session = httpx.AsyncClient()
        self.headers = None
        logging.info(f"Repo: {self.repo_owner}/{self.repo_name}")
        logging.info(f"App ID: {self.app_id}")
        logging.info(f"Installation ID: {self.installation_id}")
        logging.info("Private key present: " + ("Yes" if self.private_key else "No"))
        if not all([self.app_id, self.private_key, self.installation_id]):
            missing = []
            if not self.app_id:
                missing.append("GITHUB_APP_ID")
            if not self.private_key:
                missing.append("GITHUB_PRIVATE_KEY")
            if not self.installation_id:
                missing.append("GITHUB_INSTALLATION_ID")
            raise ValueError(
                f"Missing GitHub App credentials: {', '.join(missing)}. "
                "Please set all required environment variables."
            )
        self._setup_headers()

    def _setup_headers(self):
        """Set up GitHub App authentication headers."""
        logging.info("Setting up GitHub authentication headers...")
        try:
            jwt_token = generate_github_jwt(self.app_id, self.private_key)
            logging.info("JWT token generated successfully")
            # Get installation access token
            logging.info("Requesting installation access token...")
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            }
            response = requests.post(
                f"https://api.github.com/app/installations/"
                f"{self.installation_id}/access_tokens",
                headers=headers,
            )
            response.raise_for_status()
            installation_token = response.json()["token"]
            logging.info("Installation access token received successfully")
            # Set headers for API calls
            self.headers = {
                "Authorization": f"Bearer {installation_token}",
                "Accept": "application/vnd.github+json",
            }
            logging.info("GitHub authentication headers set up successfully")
        except Exception as e:
            logging.error(f"Error setting up GitHub authentication: {str(e)}")
            logging.error(
                "Please check your GITHUB_PRIVATE_KEY format. "
                "It should be a valid RSA private key."
            )
            raise


async def create_pr_for_file_change(
    repo: str,
    file_path: str,
    new_content: str,
    commit_message: str,
    pr_title: str,
    pr_body: str,
    config: GitHubPRConfig,
) -> str:
    """Create a PR with the given file changes."""
    # Debug: Log content being sent to GitHub
    logging.debug(f"Creating PR for {file_path}")
    logging.debug(f"Content line endings: {repr(new_content[:100])}")
    logging.debug(f"Content whitespace: {repr(new_content.splitlines()[:5])}")

    # Generate a unique branch name using timestamp
    timestamp = int(time.time())
    branch_name = f"fix-complexity-{timestamp}"

    # Get the base branch (main)
    base_branch = "main"

    # Get the latest commit SHA from the base branch
    base_resp = await config.session.get(
        f"{config.api_url}/git/ref/heads/{base_branch}",
        headers=config.headers,
    )
    if base_resp.status_code != 200:
        raise RuntimeError(f"Failed to get base branch: {base_resp.text}")
    base_sha = base_resp.json()["object"]["sha"]

    # Create a new branch from the base branch
    branch_resp = await config.session.post(
        f"{config.api_url}/git/refs",
        headers=config.headers,
        json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
    )
    if branch_resp.status_code != 201:
        raise RuntimeError(f"Failed to create branch: {branch_resp.text}")

    # 3. Create a blob for the new file content
    blob_resp = await config.session.post(
        f"{config.api_url}/git/blobs",
        headers=config.headers,
        json={"content": new_content, "encoding": "utf-8"},
    )
    if blob_resp.status_code != 201:
        logging.error(
            f"Failed to create blob: {blob_resp.status_code} - {blob_resp.text}"
        )
        raise RuntimeError(f"Failed to create blob: {blob_resp.text}")
    blob_sha = blob_resp.json()["sha"]

    # 4. Get base tree SHA from latest commit
    commit_resp = await config.session.get(
        f"{config.api_url}/git/commits/{base_sha}", headers=config.headers
    )
    if commit_resp.status_code != 200:
        logging.error(
            f"Failed to get commit: {commit_resp.status_code} - {commit_resp.text}"
        )
        raise RuntimeError(f"Failed to get commit: {commit_resp.text}")
    base_tree_sha = commit_resp.json()["tree"]["sha"]

    # 5. Create new tree that updates just this file
    tree_resp = await config.session.post(
        f"{config.api_url}/git/trees",
        headers=config.headers,
        json={
            "base_tree": base_tree_sha,
            "tree": [
                {
                    "path": file_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha,
                }
            ],
        },
    )
    if tree_resp.status_code != 201:
        logging.error(
            f"Failed to create tree: {tree_resp.status_code} - {tree_resp.text}"
        )
        raise RuntimeError(f"Failed to create tree: {tree_resp.text}")
    new_tree_sha = tree_resp.json()["sha"]

    # 6. Create a commit with the new tree
    commit_resp = await config.session.post(
        f"{config.api_url}/git/commits",
        headers=config.headers,
        json={
            "message": commit_message,
            "tree": new_tree_sha,
            "parents": [base_sha],
        },
    )
    if commit_resp.status_code != 201:
        logging.error(
            f"Failed to create commit: {commit_resp.status_code} - {commit_resp.text}"
        )
        raise RuntimeError(f"Failed to create commit: {commit_resp.text}")
    new_commit_sha = commit_resp.json()["sha"]

    # 7. Update the new branch to point to the new commit
    update_resp = await config.session.patch(
        f"{config.api_url}/git/refs/heads/{branch_name}",
        headers=config.headers,
        json={"sha": new_commit_sha, "force": False},
    )
    if update_resp.status_code != 200:
        logging.error(
            f"Failed to update branch: {update_resp.status_code} - {update_resp.text}"
        )
        raise RuntimeError(f"Failed to update branch: {update_resp.text}")

    # 8. Create the Pull Request
    pr_resp = await config.session.post(
        f"{config.api_url}/pulls",
        headers=config.headers,
        json={
            "title": pr_title,
            "head": branch_name,
            "base": "main",
            "body": pr_body,
        },
    )
    if pr_resp.status_code != 201:
        logging.error(f"Failed to create PR: {pr_resp.status_code} - {pr_resp.text}")
        raise RuntimeError(f"Failed to create PR: {pr_resp.text}")

    return pr_resp.json()["html_url"]


def create_pr(
    config: GitHubPRConfig,
    base_branch: str,
    head_branch: str,
    title: str,
    body: str,
) -> Dict:
    """Create a pull request on GitHub."""
    url = f"{config.api_base}/pulls"
    data = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch,
    }
    response = requests.post(url, headers=config.headers, json=data)
    response.raise_for_status()
    return response.json()


def update_pr(
    config: GitHubPRConfig,
    pr_number: int,
    title: str,
    body: str,
) -> Dict:
    """Update an existing pull request on GitHub."""
    url = f"{config.api_base}/pulls/{pr_number}"
    data = {
        "title": title,
        "body": body,
    }
    response = requests.patch(url, headers=config.headers, json=data)
    response.raise_for_status()
    return response.json()


def get_pr(
    config: GitHubPRConfig,
    pr_number: int,
) -> Dict:
    """Get details of a pull request from GitHub."""
    url = f"{config.api_base}/pulls/{pr_number}"
    response = requests.get(url, headers=config.headers)
    response.raise_for_status()
    return response.json()
