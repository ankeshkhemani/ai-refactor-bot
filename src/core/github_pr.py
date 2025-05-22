"""GitHub PR utilities for the AI Refactor Bot."""

import os
from typing import Dict

import httpx
import requests


class GitHubPRConfig:
    def __init__(
        self, token: str = None, repo_owner: str = None, repo_name: str = None
    ):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo_owner = repo_owner or os.getenv("REPO_OWNER")
        self.repo_name = repo_name or os.getenv("REPO_NAME")
        self.api_base = (
            f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        )
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }


async def create_pr_for_file_change(
    config: GitHubPRConfig,
    file_path: str,
    new_content: str,
    commit_message: str,
    pr_title: str,
    pr_body: str,
) -> str:
    async with httpx.AsyncClient() as client:
        # 1. Get the latest commit SHA from main
        ref_resp = await client.get(
            f"{config.api_base}/git/ref/heads/main", headers=config.headers
        )
        ref_resp.raise_for_status()
        base_sha = ref_resp.json()["object"]["sha"]

        # 2. Create a new branch from latest SHA
        new_branch = f"refactor/{file_path.replace('/', '_').replace('.', '_')}"
        await client.post(
            f"{config.api_base}/git/refs",
            headers=config.headers,
            json={"ref": f"refs/heads/{new_branch}", "sha": base_sha},
        )

        # 3. Create a blob for the new file content
        blob_resp = await client.post(
            f"{config.api_base}/git/blobs",
            headers=config.headers,
            json={"content": new_content, "encoding": "utf-8"},
        )
        blob_sha = blob_resp.json()["sha"]

        # 4. Get base tree SHA from latest commit
        commit_resp = await client.get(
            f"{config.api_base}/git/commits/{base_sha}", headers=config.headers
        )
        base_tree_sha = commit_resp.json()["tree"]["sha"]

        # 5. Create new tree that updates just this file
        tree_resp = await client.post(
            f"{config.api_base}/git/trees",
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
        new_tree_sha = tree_resp.json()["sha"]

        # 6. Create a commit with the new tree
        commit_resp = await client.post(
            f"{config.api_base}/git/commits",
            headers=config.headers,
            json={
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [base_sha],
            },
        )
        new_commit_sha = commit_resp.json()["sha"]

        # 7. Update the new branch to point to the new commit
        await client.patch(
            f"{config.api_base}/git/refs/heads/{new_branch}",
            headers=config.headers,
            json={"sha": new_commit_sha, "force": False},
        )

        # 8. Create the Pull Request
        pr_resp = await client.post(
            f"{config.api_base}/pulls",
            headers=config.headers,
            json={
                "title": pr_title,
                "head": new_branch,
                "base": "main",
                "body": pr_body,
            },
        )

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
