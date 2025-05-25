"""FastAPI application for the AI Refactor Bot."""

import hashlib
import hmac
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from ..core.code_scanner import GitHubConfig, scan_repository
from ..core.github_pr import GitHubPRConfig
from ..core.issue_fixer import create_fix_pr

load_dotenv()

app = FastAPI(
    title="AI Refactoring Bot",
    description=(
        "GitHub-integrated tool that automatically scans Python repositories "
        "for technical debt and generates refactoring suggestions"
    ),
    version="1.0.0",
)


class AppConfig:
    def __init__(self):
        self.github_app_id = os.getenv("GITHUB_APP_ID")
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
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
                "Missing required environment variables. "
                "Please set GITHUB_APP_ID, GITHUB_WEBHOOK_SECRET, "
                "GITHUB_PRIVATE_KEY_PATH, GITHUB_INSTALLATION_ID, "
                "REPO_OWNER, and REPO_NAME."
            )

        self.github_config = GitHubConfig()
        self.pr_config = GitHubPRConfig()


config = AppConfig()


def calculate_issue_score(issue: Dict) -> float:
    """Calculate a score for an issue based on its type and severity.

    Higher scores indicate more compelling issues that should be fixed first.
    """
    base_score = 0.0

    if issue["type"] == "Cyclomatic Complexity":
        # Higher complexity = higher score
        complexity = issue.get("complexity", 0)
        rank_score = {"A": 1.0, "B": 2.0, "C": 3.0, "D": 4.0, "E": 5.0, "F": 6.0}.get(
            issue.get("rank", "A"), 1.0
        )
        base_score = complexity * rank_score

    elif issue["type"] == "Flake8 Issues":
        # Prioritize certain Flake8 codes
        code = issue.get("code", "")
        severity = {
            "F": 3.0,  # PyFlakes errors
            "E": 2.0,  # pycodestyle errors
            "W": 1.0,  # pycodestyle warnings
        }.get(code[0] if code else "W", 1.0)
        base_score = 10.0 * severity

    return base_score


def select_most_compelling_issue(issues: List[Dict]) -> Optional[Dict]:
    """Select the most compelling issue from a list of issues.

    Args:
        issues: List of issues from code scanner

    Returns:
        The most compelling issue, or None if no issues found
    """
    if not issues:
        return None

    # Calculate scores for all issues
    scored_issues = [(issue, calculate_issue_score(issue)) for issue in issues]

    # Sort by score in descending order
    scored_issues.sort(key=lambda x: x[1], reverse=True)

    # Return the highest scoring issue
    return scored_issues[0][0]


async def process_repository() -> Optional[str]:
    """Process the repository and create a PR for the most compelling issue.

    Returns:
        URL of the created PR, or None if no issues found
    """
    # Scan repository for issues
    analysis_results = scan_repository()

    # Flatten the results into a list of issues
    all_issues = []
    for file_path, metrics in analysis_results.items():
        # Process Cyclomatic Complexity
        for tmp_path, entries in metrics["radon"]["complexity"].items():
            for fn in entries:
                all_issues.append(
                    {
                        "file": file_path,
                        "line": fn["lineno"],
                        "type": "Cyclomatic Complexity",
                        "complexity": fn["complexity"],
                        "rank": fn["rank"],
                        "function": fn["name"],
                    }
                )

        # Process Flake8 Issues
        for issue in metrics["flake8"]:
            parts = issue.split(":")
            if len(parts) >= 4:
                line = int(parts[1])
                code_desc = parts[3].strip()
                code = code_desc.split()[0]
                description = " ".join(code_desc.split()[1:])
                all_issues.append(
                    {
                        "file": file_path,
                        "line": line,
                        "type": "Flake8 Issues",
                        "code": code,
                        "description": description,
                    }
                )

    # Select the most compelling issue
    selected_issue = select_most_compelling_issue(all_issues)
    if not selected_issue:
        return None

    # Create PR for the selected issue
    config_dict = {
        "repo": f"{config.repo_owner}/{config.repo_name}",
        "github_config": config.github_config,
        "gpt_model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    return await create_fix_pr(selected_issue, "", config_dict)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze_repository():
    """Analyze repository and create a PR for the most compelling issue.

    This is an independent workflow that can be triggered manually or via a schedule.
    """
    try:
        pr_url = await process_repository()
        if pr_url:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": f"Created PR for most compelling issue: {pr_url}",
                    "pr_url": pr_url,
                }
            )
        else:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "No compelling issues found to fix",
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to process repository: {str(e)}",
            },
        )


@app.post("/webhook")
async def webhook(request: Request):
    """Handle GitHub webhook events.

    Note: This is a placeholder for future webhook integration.
    The actual workflow is currently handled by the /analyze endpoint.
    """
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

    # For now, just acknowledge the webhook
    return JSONResponse(
        content={
            "status": "success",
            "message": (
                "Webhook received. Analysis workflow is handled by /analyze endpoint."
            ),
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Refactor Bot is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
    )
