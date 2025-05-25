"""Service for handling PR creation.

This service is responsible for:
1. Processing fixes from the queue
2. Creating pull requests with AI-generated improvements
3. Handling retries and error recovery
4. Managing GitHub API interactions

The service receives pre-generated fixes from the Analysis Service and creates
pull requests with the following information:
- File content changes
- Commit message
- PR title and description
- Installation ID for GitHub API access

The service implements retry logic by re-enqueueing failed PR creation attempts,
ensuring reliable delivery of improvements to the repository.
"""

import logging
from typing import Dict

from .github_pr import GitHubPRConfig
from .issue_fixer import create_fix_pr
from .queue_service import QueueService

logger = logging.getLogger(__name__)


class PRService:
    def __init__(self, queue_service: QueueService):
        """Initialize the PR service.

        Args:
            queue_service: Queue service for message handling
        """
        self.queue_service = queue_service

    async def process_issue(
        self,
        repo_owner: str,
        repo_name: str,
        installation_id: str,
        file_path: str,
        issue: Dict,
        original_code: str,
    ):
        """Process an issue and create a PR.

        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            installation_id: GitHub App installation ID
            file_path: Path to the file being fixed
            issue: The issue to fix
            original_code: Original content of the file
        """
        try:
            logger.info(f"Processing fix for {file_path} in {repo_owner}/{repo_name}")

            # Create PR with the fix
            pr_url = await create_fix_pr(
                issue=issue,
                original_code=original_code,
                config={
                    "repo": f"{repo_owner}/{repo_name}",
                    "github_config": GitHubPRConfig(
                        installation_id=installation_id,
                        repo_owner=repo_owner,
                        repo_name=repo_name,
                    ),
                    "gpt_model": "o4-mini",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            )

            if pr_url:
                logger.info(f"Created PR: {pr_url}")
            else:
                logger.warning("No PR created - issue might have been skipped")

        except Exception as e:
            logger.error(f"Error processing issue: {str(e)}")
            logger.exception("Full traceback:")
            # Re-enqueue the issue for retry
            await self.queue_service.enqueue(
                "fix",
                {
                    "repo_owner": repo_owner,
                    "repo_name": repo_name,
                    "installation_id": installation_id,
                    "file_path": file_path,
                    "issue": issue,
                    "original_code": original_code,
                },
            )
            raise
