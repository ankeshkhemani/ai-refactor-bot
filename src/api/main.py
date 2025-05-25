"""FastAPI application for the AI Refactor Bot.

This application implements a queue-based microservices architecture for automated code refactoring:

1. Analysis Service: Scans repositories for code quality issues and generates fixes
2. PR Service: Creates pull requests with AI-generated improvements
3. Queue Service: Manages message queues for reliable processing

The application exposes the following endpoints:
- POST /webhook: Handles GitHub webhook events
- POST /analyze: Triggers repository analysis
- GET /health: Health check endpoint
- GET /: Root endpoint

The application uses background tasks to process:
- Analysis queue: Processes repository analysis tasks
- PR queue: Processes PR creation tasks
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.analysis_service import AnalysisService
from ..core.code_scanner import scan_repository
from ..core.github_config import GitHubConfig
from ..core.installation_service import InstallationService
from ..core.issue_fixer import create_fix_pr
from ..core.pr_service import PRService
from ..core.queue_service import QueueService
from ..models.database import init_db

load_dotenv()

app = FastAPI(
    title="AI Refactoring Bot",
    description=(
        "GitHub-integrated tool that automatically scans Python repositories "
        "for technical debt and generates refactoring suggestions"
    ),
    version="1.0.0",
)

# Initialize database
SessionLocal = init_db(os.getenv("DATABASE_URL", "sqlite:///./ai_refactor_bot.db"))

# Initialize services
queue_service = QueueService()
analysis_service = AnalysisService(queue_service)
pr_service = PRService(queue_service)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_installation_service(db: Session = Depends(get_db)) -> InstallationService:
    return InstallationService(
        app_id=os.getenv("GITHUB_APP_ID"),
        private_key=os.getenv("GITHUB_PRIVATE_KEY"),
        db_session=db,
    )


class AppConfig:
    def __init__(self):
        self.github_app_id = os.getenv("GITHUB_APP_ID")
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        self.private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")

        if not all([self.github_app_id, self.webhook_secret, self.private_key_path]):
            raise ValueError(
                "Missing required environment variables. "
                "Please set GITHUB_APP_ID, GITHUB_WEBHOOK_SECRET, "
                "and GITHUB_PRIVATE_KEY_PATH."
            )

        # Load private key from file if it exists
        if os.path.exists(self.private_key_path):
            with open(self.private_key_path, "r") as f:
                os.environ["GITHUB_PRIVATE_KEY"] = f.read()
            logging.info(f"Loaded private key from {self.private_key_path}")


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


async def process_repository(
    repo_owner: str, repo_name: str, installation_id: str = None
) -> Optional[str]:
    """Process the repository and create a PR for the most compelling issue.

    Args:
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        installation_id: GitHub App installation ID
    Returns:
        URL of the created PR, or None if no issues found
    """
    # Scan repository for issues
    github_config = GitHubConfig()
    github_config.repo_owner = repo_owner
    github_config.repo_name = repo_name
    github_config.installation_id = installation_id
    github_config.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    github_config.setup_headers()

    analysis_results = scan_repository(github_config)

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
                        "target_complexity": 10,  # Set a reasonable target complexity
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
        "repo": f"{repo_owner}/{repo_name}",
        "github_config": github_config,
        "gpt_model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    return await create_fix_pr(selected_issue, "", config_dict)


@app.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Handle GitHub webhook events."""
    try:
        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event")

        if event_type == "installation":
            action = payload.get("action")
            installation_service = InstallationService(
                app_id=os.getenv("GITHUB_APP_ID"),
                private_key=os.getenv("GITHUB_PRIVATE_KEY"),
                db_session=db,
            )
            if action == "created":
                await installation_service.handle_installation_created(payload)
                # Enqueue repositories for analysis
                for repo in payload.get("repositories", []):
                    await queue_service.enqueue(
                        "analysis",
                        {
                            "repo_owner": payload["installation"]["account"]["login"],
                            "repo_name": repo["name"],
                            "installation_id": str(payload["installation"]["id"]),
                        },
                    )
            elif action == "deleted":
                await installation_service.handle_installation_deleted(payload)

        return JSONResponse(content={"status": "success"})

    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        logging.exception("Full traceback:")
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


class AnalyzeRequest(BaseModel):
    repo_owner: str
    repo_name: str
    installation_id: str


@app.post("/analyze")
async def analyze_repository(request: AnalyzeRequest):
    """Enqueue a repository for analysis."""
    try:
        await queue_service.enqueue(
            "analysis",
            {
                "repo_owner": request.repo_owner,
                "repo_name": request.repo_name,
                "installation_id": request.installation_id,
            },
        )
        return JSONResponse(
            content={"status": "success", "message": "Analysis job enqueued"}
        )
    except Exception as e:
        logging.error(f"Error enqueueing analysis: {str(e)}")
        logging.exception("Full traceback:")
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Refactor Bot is running"}


# Start background tasks
@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    asyncio.create_task(process_analysis_queue())
    asyncio.create_task(process_fix_queue())


async def process_analysis_queue():
    """Process messages from the analysis queue."""
    while True:
        try:
            message = await queue_service.dequeue("analysis")
            if message:
                await analysis_service.process_repository(
                    message["repo_owner"],
                    message["repo_name"],
                    message["installation_id"],
                )
            await asyncio.sleep(1)  # Prevent tight loop
        except Exception as e:
            logging.error(f"Error processing analysis queue: {str(e)}")
            logging.exception("Full traceback:")
            await asyncio.sleep(5)  # Back off on error


async def process_fix_queue():
    """Process messages from the fix queue."""
    while True:
        try:
            message = await queue_service.dequeue("fix")
            if message:
                await pr_service.process_issue(
                    message["repo_owner"],
                    message["repo_name"],
                    message["installation_id"],
                    message["file_path"],
                    message["issue"],
                    message["original_code"],
                )
            await asyncio.sleep(1)  # Prevent tight loop
        except Exception as e:
            logging.error(f"Error processing fix queue: {str(e)}")
            logging.exception("Full traceback:")
            await asyncio.sleep(5)  # Back off on error


if __name__ == "__main__":
    import uvicorn
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    # Set up scheduler for weekly analysis
    scheduler = AsyncIOScheduler()

    async def analyze_repositories():
        """Analyze all repositories that need analysis."""
        db = SessionLocal()
        try:
            installation_service = InstallationService(
                app_id=os.getenv("GITHUB_APP_ID"),
                private_key=os.getenv("GITHUB_PRIVATE_KEY"),
                db_session=db,
            )
            repos = installation_service.get_repositories_for_analysis()
            for repo in repos:
                await installation_service.trigger_repository_analysis(repo.full_name)
        finally:
            db.close()

    # Schedule weekly analysis (every Sunday at 00:00)
    scheduler.add_job(
        analyze_repositories,
        CronTrigger(day_of_week="sun", hour=0, minute=0),
        id="weekly_analysis",
        name="Weekly repository analysis",
    )

    scheduler.start()

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
    )
