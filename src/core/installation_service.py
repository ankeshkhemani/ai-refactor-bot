"""Service for handling GitHub App installations and repositories."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

import httpx
from sqlalchemy.orm import Session

from ..models.database import Installation, Repository
from ..utils.jwt_helper import generate_github_jwt

logger = logging.getLogger(__name__)


class InstallationService:
    def __init__(self, app_id: str, private_key: str, db_session: Session):
        self.app_id = app_id
        self.private_key = private_key
        self.db = db_session
        self.client = httpx.AsyncClient()

    async def _get_installation_token(self, installation_id: int) -> str:
        """Get an installation access token."""
        jwt = generate_github_jwt(self.app_id, self.private_key)
        headers = {
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/vnd.github+json",
        }
        response = await self.client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()["token"]

    async def handle_installation_created(self, payload: dict):
        """Handle installation created event."""
        try:
            installation = payload["installation"]
            account = payload["sender"]
            logger.info(
                f"Handling installation created event for installation ID: {installation['id']}"
            )

            # Create installation record
            db_installation = Installation(
                installation_id=installation["id"],
                account_id=account["id"],
                account_type=account["type"],
                account_login=account["login"],
                target_type=installation["target_type"],
                target_id=installation["target_id"],
                target_login=installation["account"]["login"],
                repository_selection=installation["repository_selection"],
            )
            self.db.add(db_installation)
            self.db.commit()
            logger.info(
                f"Created installation record in database with ID: {db_installation.id}"
            )

            # Process repositories from the payload
            if "repositories" in payload:
                logger.info(
                    f"Processing {len(payload['repositories'])} repositories from installation event"
                )
                for repo in payload["repositories"]:
                    # Check if repo already exists
                    db_repo = (
                        self.db.query(Repository).filter_by(repo_id=repo["id"]).first()
                    )
                    if db_repo:
                        # Update existing repository info
                        db_repo.name = repo["name"]
                        db_repo.full_name = repo["full_name"]
                        db_repo.private = repo["private"]
                        db_repo.owner_id = installation["account"]["id"]
                        db_repo.owner_login = installation["account"]["login"]
                        db_repo.installation_id = installation["id"]
                        db_repo.updated_at = datetime.utcnow()
                        logger.info(
                            f"Updated repository in database: {repo['full_name']}"
                        )
                    else:
                        db_repo = Repository(
                            repo_id=repo["id"],
                            name=repo["name"],
                            full_name=repo["full_name"],
                            private=repo["private"],
                            owner_id=installation["account"]["id"],
                            owner_login=installation["account"]["login"],
                            installation_id=installation["id"],
                        )
                        self.db.add(db_repo)
                        logger.info(
                            f"Added new repository to database: {repo['full_name']}"
                        )
                self.db.commit()
                logger.info("Saved repositories to database")

                # Trigger analysis for each repository
                for repo in payload["repositories"]:
                    logger.info(
                        f"Triggering analysis for repository: {repo['full_name']}"
                    )
                    await self.trigger_repository_analysis(repo["full_name"])

            # If installation is for all repositories, fetch them
            if installation["repository_selection"] == "all":
                logger.info(
                    "Installation is for all repositories, fetching complete list"
                )
                await self.fetch_all_repositories(installation["id"])
        except Exception as e:
            logger.error(f"Error handling installation created event: {str(e)}")
            logger.exception("Full traceback:")

    async def handle_installation_deleted(self, payload: dict):
        """Handle installation deleted event."""
        try:
            installation_id = payload["installation"]["id"]
            logger.info(
                f"Handling installation deleted event for installation ID: {installation_id}"
            )

            # Mark installation as suspended
            installation = (
                self.db.query(Installation)
                .filter_by(installation_id=installation_id)
                .first()
            )
            if installation:
                installation.suspended_at = datetime.utcnow()
                installation.suspended_by = payload["sender"]["id"]
                self.db.commit()
                logger.info(f"Marked installation {installation_id} as suspended")
            else:
                logger.warning(f"Installation {installation_id} not found in database")

            # Delete all repositories associated with this installation
            self.db.query(Repository).filter_by(
                installation_id=installation_id
            ).delete()
            self.db.commit()
            logger.info(f"Deleted all repositories for installation {installation_id}")
        except Exception as e:
            logger.error(f"Error handling installation deleted event: {str(e)}")
            logger.exception("Full traceback:")

    async def fetch_all_repositories(self, installation_id: int):
        """Fetch all repositories for an installation."""
        try:
            token = await self._get_installation_token(installation_id)
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }

            # Get all repositories
            response = await self.client.get(
                "https://api.github.com/installation/repositories",
                headers=headers,
            )
            response.raise_for_status()
            repos = response.json()["repositories"]

            # Save repositories to database
            for repo in repos:
                db_repo = Repository(
                    repo_id=repo["id"],
                    name=repo["name"],
                    full_name=repo["full_name"],
                    private=repo["private"],
                    owner_id=repo["owner"]["id"],
                    owner_login=repo["owner"]["login"],
                    installation_id=installation_id,
                )
                self.db.add(db_repo)

            self.db.commit()
            logger.info(
                f"Fetched and saved {len(repos)} repositories for installation {installation_id}"
            )

            # Trigger initial analysis for each repository
            for repo in repos:
                asyncio.create_task(self.trigger_repository_analysis(repo["full_name"]))

        except Exception as e:
            logger.error(
                f"Error fetching repositories for installation {installation_id}: {str(e)}"
            )

    async def trigger_repository_analysis(self, repo_full_name: str):
        """Trigger analysis for a repository."""
        try:
            if "/" not in repo_full_name:
                logger.error(f"Invalid repo_full_name: {repo_full_name}")
                return
            repo_owner, repo_name = repo_full_name.split("/", 1)
            logger.info(f"Starting analysis for repository: {repo_full_name}")

            # Check if repository exists in database
            repo = self.db.query(Repository).filter_by(full_name=repo_full_name).first()
            if not repo:
                logger.error(f"Repository {repo_full_name} not found in database")
                return

            logger.info(f"Found repository in database with ID: {repo.id}")

            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
                logger.info("Sending analysis request to /analyze endpoint")
                response = await client.post(
                    "http://localhost:8000/analyze",
                    json={
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "installation_id": str(repo.installation_id),
                    },
                )
                response.raise_for_status()
                logger.info(f"Analysis request successful for {repo_full_name}")
                logger.info(f"Response: {response.json()}")
        except Exception as e:
            logger.error(f"Error triggering analysis for {repo_full_name}: {str(e)}")
            logger.exception("Full traceback:")

    def get_active_installations(self) -> List[Installation]:
        """Get all active installations."""
        return self.db.query(Installation).filter_by(suspended_at=None).all()

    def get_repositories_for_analysis(self) -> List[Repository]:
        """Get repositories that need analysis."""
        # Get repositories that haven't been analyzed in the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        return (
            self.db.query(Repository)
            .filter(
                (Repository.last_analyzed_at is None)
                | (Repository.last_analyzed_at < week_ago)
            )
            .all()
        )
