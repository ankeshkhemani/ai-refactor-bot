"""GitHub PR utilities for the AI Refactor Bot."""

import os
from typing import Dict

import httpx
import requests

# Required environment variables:
# - GITHUB_TOKEN
# - REPO_OWNER
# - REPO_NAME

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"


async def create_pr_for_file_change(
    file_path: str, new_content: str, commit_message: str, pr_title: str, pr_body: str
) -> str:
    async with httpx.AsyncClient() as client:
        # 1. Get the latest commit SHA from main
        ref_resp = await client.get(f"{API_BASE}/git/ref/heads/main", headers=HEADERS)
        ref_resp.raise_for_status()
        base_sha = ref_resp.json()["object"]["sha"]

        # 2. Create a new branch from latest SHA
        new_branch = f"refactor/{file_path.replace('/', '_').replace('.', '_')}"
        await client.post(
            f"{API_BASE}/git/refs",
            headers=HEADERS,
            json={"ref": f"refs/heads/{new_branch}", "sha": base_sha},
        )

        # 3. Create a blob for the new file content
        blob_resp = await client.post(
            f"{API_BASE}/git/blobs",
            headers=HEADERS,
            json={"content": new_content, "encoding": "utf-8"},
        )
        blob_sha = blob_resp.json()["sha"]

        # 4. Get base tree SHA from latest commit
        commit_resp = await client.get(
            f"{API_BASE}/git/commits/{base_sha}", headers=HEADERS
        )
        base_tree_sha = commit_resp.json()["tree"]["sha"]

        # 5. Create new tree that updates just this file
        tree_resp = await client.post(
            f"{API_BASE}/git/trees",
            headers=HEADERS,
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
            f"{API_BASE}/git/commits",
            headers=HEADERS,
            json={
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [base_sha],
            },
        )
        new_commit_sha = commit_resp.json()["sha"]

        # 7. Update the new branch to point to the new commit
        await client.patch(
            f"{API_BASE}/git/refs/heads/{new_branch}",
            headers=HEADERS,
            json={"sha": new_commit_sha, "force": False},
        )

        # 8. Create the Pull Request
        pr_resp = await client.post(
            f"{API_BASE}/pulls",
            headers=HEADERS,
            json={
                "title": pr_title,
                "head": new_branch,
                "base": "main",
                "body": pr_body,
            },
        )

        return pr_resp.json()["html_url"]


def create_pr(
    repo_owner: str,
    repo_name: str,
    base_branch: str,
    head_branch: str,
    title: str,
    body: str,
    token: str,
) -> Dict:
    """Create a pull request on GitHub."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch,
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def update_pr(
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    title: str,
    body: str,
    token: str,
) -> Dict:
    """Update an existing pull request on GitHub."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {
        "title": title,
        "body": body,
    }
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_pr(
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    token: str,
) -> Dict:
    """Get details of a pull request from GitHub."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
