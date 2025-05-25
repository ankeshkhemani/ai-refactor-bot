"""Service for handling code analysis.

This service is responsible for:
1. Scanning repositories for code quality issues using Radon and Flake8
2. Grouping issues by file for efficient processing
3. Using AI to generate fixes for identified issues
4. Enqueuing fixes for PR creation

The service uses a queue-based architecture to ensure reliable processing and
handles the following types of issues:
- Cyclomatic Complexity (using Radon)
- Code Style and Potential Bugs (using Flake8)

Each file's issues are processed together to generate comprehensive fixes
that address multiple issues in a single PR.
"""

import logging

from .code_scanner import scan_repository
from .github_config import GitHubConfig
from .queue_service import QueueService

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, queue_service: QueueService):
        """Initialize the analysis service.

        Args:
            queue_service: Queue service for message handling
        """
        self.queue_service = queue_service

    async def process_repository(
        self, repo_owner: str, repo_name: str, installation_id: str
    ):
        """Process a repository and fix the most compelling issue."""
        try:
            # Create GitHub config
            github_config = GitHubConfig()
            github_config.repo_owner = repo_owner
            github_config.repo_name = repo_name
            github_config.installation_id = installation_id
            github_config.api_url = (
                f"https://api.github.com/repos/{repo_owner}/{repo_name}"
            )
            github_config.head_ref = "main"  # Default to main branch
            github_config.setup_headers()

            # Scan repository
            analysis_results = await scan_repository(github_config)
            if not analysis_results:
                logger.warning(f"No issues found in {repo_owner}/{repo_name}")
                return

            # Flatten and score all issues
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
                                "target_complexity": 10,
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
            selected_issue = None
            highest_score = 0

            for issue in all_issues:
                score = 0
                if issue["type"] == "Cyclomatic Complexity":
                    # Prioritize high complexity functions
                    complexity = issue.get("complexity", 0)
                    rank_score = {
                        "A": 1.0,
                        "B": 2.0,
                        "C": 3.0,
                        "D": 4.0,
                        "E": 5.0,
                        "F": 6.0,
                    }.get(issue.get("rank", "A"), 1.0)
                    score = complexity * rank_score
                elif issue["type"] == "Flake8 Issues":
                    # Prioritize certain Flake8 codes
                    code = issue.get("code", "")
                    severity = {
                        "F": 3.0,  # PyFlakes errors
                        "E": 2.0,  # pycodestyle errors
                        "W": 1.0,  # pycodestyle warnings
                    }.get(code[0] if code else "W", 1.0)
                    score = 10.0 * severity

                if score > highest_score:
                    highest_score = score
                    selected_issue = issue

            if not selected_issue:
                logger.warning(
                    f"No compelling issues found in {repo_owner}/{repo_name}"
                )
                return

            # Get file content for the selected issue
            file_content = await github_config.get_file_content(selected_issue["file"])
            if not file_content:
                logger.warning(f"Could not get content for {selected_issue['file']}")
                return

            # Create config for PR creation
            config_dict = {
                "repo": f"{repo_owner}/{repo_name}",
                "github_config": github_config,
                "gpt_model": "o4-mini",
                "temperature": 0.7,
                "max_tokens": 2000,
            }

            # Enqueue the fix job
            await self.queue_service.enqueue(
                "fix",
                {
                    "repo_owner": repo_owner,
                    "repo_name": repo_name,
                    "installation_id": installation_id,
                    "file_path": selected_issue["file"],
                    "issue": selected_issue,
                    "original_code": file_content,
                    "config": config_dict,
                },
            )
            logger.info(f"Enqueued fix job for {selected_issue['file']}")

        except Exception as e:
            logger.error(
                f"Error processing repository {repo_owner}/{repo_name}: {str(e)}"
            )
            logger.exception("Full traceback:")
            raise
