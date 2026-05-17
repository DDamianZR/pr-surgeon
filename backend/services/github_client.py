"""
GitHub Pull Request client service.
Fetches PR data from GitHub API using PyGithub and converts to Pydantic models.
"""

import os
import re
from typing import Any

from dotenv import load_dotenv
from github import Auth, Github, GithubException, RateLimitExceededException
from github.PullRequest import PullRequest
from loguru import logger

from models.pr import FileChange, PullRequestData, detect_language


class GitHubPRClient:
    """
    Client for fetching Pull Request data from GitHub.
    
    Handles authentication, URL parsing, and conversion of GitHub API
    responses to Pydantic models.
    """
    
    def __init__(self, github_token: str | None = None) -> None:
        """
        Initialize GitHub client with authentication.
        
        Args:
            github_token: GitHub personal access token. If None, reads from
                         GITHUB_TOKEN environment variable.
                         
        Raises:
            ValueError: If no token is provided and GITHUB_TOKEN env var is not set
        """
        load_dotenv()
        
        token = github_token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                "GitHub token required. Provide via github_token parameter "
                "or set GITHUB_TOKEN environment variable."
            )
        
        auth = Auth.Token(token)
        self._client = Github(auth=auth)
        
        logger.info("GitHubPRClient initialized")
    
    def parse_pr_url(self, url: str) -> tuple[str, str, int]:
        """
        Parse GitHub PR URL to extract owner, repo, and PR number.
        
        Accepts various URL formats:
        - https://github.com/owner/repo/pull/123
        - http://github.com/owner/repo/pull/123
        - github.com/owner/repo/pull/123
        - www.github.com/owner/repo/pull/123
        
        Args:
            url: GitHub PR URL in any supported format
            
        Returns:
            Tuple of (owner, repo, pr_number)
            
        Raises:
            ValueError: If URL format is invalid or not a pull request URL
        """
        # Remove protocol and www if present
        url_clean = re.sub(r'^https?://', '', url)
        url_clean = re.sub(r'^www\.', '', url_clean)
        
        # Match github.com/owner/repo/pull/number
        pattern = r'^github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$'
        match = re.match(pattern, url_clean)
        
        if not match:
            raise ValueError(
                f"Invalid GitHub PR URL format: {url}. "
                "Expected format: https://github.com/owner/repo/pull/123"
            )
        
        owner, repo, pr_number_str = match.groups()
        pr_number = int(pr_number_str)
        
        logger.debug(
            "Parsed PR URL",
            extra={
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "original_url": url
            }
        )
        
        return owner, repo, pr_number
    
    def fetch_pr(self, pr_url: str, max_files: int = 500) -> PullRequestData:
        """
        Fetch complete Pull Request data from GitHub.
        
        Args:
            pr_url: GitHub PR URL
            max_files: Maximum number of files to fetch (prevents memory issues)
            
        Returns:
            PullRequestData model with all PR information and file changes
            
        Raises:
            ValueError: If URL is invalid
            GithubException: If GitHub API request fails
            RateLimitExceededException: If GitHub API rate limit is exceeded
        """
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        
        logger.info(
            "Fetching PR data",
            extra={
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number
            }
        )
        
        try:
            # Fetch repository and PR
            repository = self._client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            
            # Convert PR data to our models
            pr_data = self._convert_pr_to_model(pr, max_files)
            
            logger.info(
                "Successfully fetched PR data",
                extra={
                    "pr_number": pr_number,
                    "file_count": len(pr_data.files),
                    "total_additions": pr_data.total_additions,
                    "total_deletions": pr_data.total_deletions
                }
            )
            
            return pr_data
            
        except RateLimitExceededException as e:
            logger.error(
                "GitHub API rate limit exceeded",
                extra={"error": str(e)}
            )
            raise
            
        except GithubException as e:
            logger.error(
                "GitHub API error",
                extra={
                    "status": e.status,
                    "data": e.data,
                    "error": str(e)
                }
            )
            raise
    
    def _convert_pr_to_model(
        self,
        pr: PullRequest,
        max_files: int
    ) -> PullRequestData:
        """
        Convert PyGithub PullRequest object to PullRequestData model.
        
        Args:
            pr: PyGithub PullRequest object
            max_files: Maximum number of files to include
            
        Returns:
            PullRequestData model
        """
        # Fetch all changed files
        files_list = list(pr.get_files())
        
        # Warn if truncating
        if len(files_list) > max_files:
            logger.warning(
                "PR has more files than max_files limit, truncating",
                extra={
                    "total_files": len(files_list),
                    "max_files": max_files,
                    "pr_number": pr.number
                }
            )
            files_list = files_list[:max_files]
        
        # Convert files to FileChange models
        file_changes: list[FileChange] = []
        for file in files_list:
            language = detect_language(file.filename)
            
            file_change = FileChange(
                filename=file.filename,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                patch=file.patch,
                language=language
            )
            file_changes.append(file_change)
        
        # Build PullRequestData model
        pr_data = PullRequestData(
            pr_number=pr.number,
            title=pr.title,
            body=pr.body,
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            repo_full_name=pr.base.repo.full_name,
            files=file_changes,
            total_additions=pr.additions,
            total_deletions=pr.deletions,
            url=pr.html_url,
            author=pr.user.login
        )
        
        return pr_data


# Made with Bob