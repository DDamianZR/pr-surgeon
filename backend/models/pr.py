"""
Pydantic models for GitHub Pull Request data.
Defines data contracts for PR information and file changes.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


def detect_language(filename: str) -> str | None:
    """
    Detect programming language from file extension.
    
    Args:
        filename: The filename or path to analyze
        
    Returns:
        Language name as string, or None if unknown
    """
    ext = Path(filename).suffix.lower()
    
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".java": "java",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".md": "markdown",
    }
    
    return language_map.get(ext)


class FileChange(BaseModel):
    """
    Represents a single file change in a Pull Request.
    
    Attributes:
        filename: Path to the changed file
        status: Type of change (added, modified, removed, etc.)
        additions: Number of lines added
        deletions: Number of lines deleted
        patch: Git diff patch for this file (may be None for binary files)
        language: Detected programming language (may be None)
    """
    filename: str
    status: Literal["added", "modified", "removed", "renamed", "changed", "copied", "unchanged"]
    additions: int
    deletions: int
    patch: str | None = None
    language: str | None = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "src/main.py",
                "status": "modified",
                "additions": 15,
                "deletions": 3,
                "patch": "@@ -1,5 +1,5 @@\n def main():\n-    print('old')\n+    print('new')",
                "language": "python"
            }
        }
    }


class PullRequestData(BaseModel):
    """
    Complete Pull Request data including metadata and file changes.
    
    Attributes:
        pr_number: GitHub PR number
        title: PR title
        body: PR description (may be None)
        base_branch: Target branch name
        head_branch: Source branch name
        repo_full_name: Repository in format "owner/repo"
        files: List of changed files
        total_additions: Total lines added across all files
        total_deletions: Total lines deleted across all files
        url: Full GitHub URL to the PR
        author: GitHub username of PR author
    """
    pr_number: int
    title: str
    body: str | None = None
    base_branch: str
    head_branch: str
    repo_full_name: str
    files: list[FileChange] = Field(default_factory=list)
    total_additions: int
    total_deletions: int
    url: str
    author: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "pr_number": 123,
                "title": "Add new feature",
                "body": "This PR adds a new feature",
                "base_branch": "main",
                "head_branch": "feature/new-thing",
                "repo_full_name": "owner/repo",
                "files": [],
                "total_additions": 150,
                "total_deletions": 30,
                "url": "https://github.com/owner/repo/pull/123",
                "author": "developer"
            }
        }
    }


# Made with Bob