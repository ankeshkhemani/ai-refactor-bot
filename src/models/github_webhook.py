"""GitHub webhook models for the AI Refactor Bot."""

from typing import Optional

from pydantic import BaseModel, Field


class Repository(BaseModel):
    """GitHub repository information."""

    id: int
    name: str
    full_name: str
    private: bool
    owner: dict
    html_url: str
    description: Optional[str] = None
    fork: bool
    url: str
    created_at: str
    updated_at: str
    pushed_at: str
    git_url: str
    ssh_url: str
    clone_url: str
    default_branch: str


class PullRequest(BaseModel):
    """GitHub pull request information."""

    id: int
    number: int
    state: str
    title: str
    user: dict
    body: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    merged_at: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    assignee: Optional[dict] = None
    assignees: list = Field(default_factory=list)
    requested_reviewers: list = Field(default_factory=list)
    head: dict
    base: dict
    draft: bool
    merged: bool
    mergeable: Optional[bool] = None
    mergeable_state: str
    comments: int
    review_comments: int
    commits: int
    additions: int
    deletions: int
    changed_files: int


class WebhookPayload(BaseModel):
    """GitHub webhook payload model."""

    action: str = Field(..., description="The action that triggered the webhook")
    pull_request: Optional[PullRequest] = Field(
        None, description="Pull request information if the event is PR-related"
    )
    repository: Optional[Repository] = Field(None, description="Repository information")
    sender: Optional[dict] = Field(None, description="User who triggered the webhook")
    installation: Optional[dict] = Field(
        None, description="GitHub App installation information"
    )
