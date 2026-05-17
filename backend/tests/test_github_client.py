"""
Unit tests for GitHub PR client.
Tests URL parsing logic without making network calls.
"""

import pytest

from services.github_client import GitHubPRClient


class TestParseURLs:
    """Test suite for parse_pr_url method."""
    
    def test_parse_valid_https_url(self) -> None:
        """Test parsing a standard HTTPS GitHub PR URL."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        url = "https://github.com/owner/repo/pull/123"
        owner, repo, pr_number = client.parse_pr_url(url)
        
        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == 123
    
    def test_parse_http_url(self) -> None:
        """Test parsing HTTP (non-secure) GitHub PR URL."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        url = "http://github.com/owner/repo/pull/456"
        owner, repo, pr_number = client.parse_pr_url(url)
        
        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == 456
    
    def test_parse_url_without_protocol(self) -> None:
        """Test parsing URL without http:// or https:// prefix."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        url = "github.com/owner/repo/pull/789"
        owner, repo, pr_number = client.parse_pr_url(url)
        
        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == 789
    
    def test_parse_url_with_www(self) -> None:
        """Test parsing URL with www prefix."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        url = "www.github.com/owner/repo/pull/999"
        owner, repo, pr_number = client.parse_pr_url(url)
        
        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == 999
    
    def test_parse_url_with_https_and_www(self) -> None:
        """Test parsing URL with both https and www."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        url = "https://www.github.com/owner/repo/pull/111"
        owner, repo, pr_number = client.parse_pr_url(url)
        
        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == 111
    
    def test_parse_url_with_trailing_slash(self) -> None:
        """Test parsing URL with trailing slash."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        url = "https://github.com/owner/repo/pull/222/"
        owner, repo, pr_number = client.parse_pr_url(url)
        
        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == 222
    
    def test_parse_invalid_url_raises_error(self) -> None:
        """Test that invalid URL format raises ValueError."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        invalid_url = "https://github.com/owner/repo"
        
        with pytest.raises(ValueError) as exc_info:
            client.parse_pr_url(invalid_url)
        
        assert "Invalid GitHub PR URL format" in str(exc_info.value)
    
    def test_parse_issues_url_raises_error(self) -> None:
        """Test that issues URL (not pull request) raises ValueError."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        issues_url = "https://github.com/owner/repo/issues/123"
        
        with pytest.raises(ValueError) as exc_info:
            client.parse_pr_url(issues_url)
        
        assert "Invalid GitHub PR URL format" in str(exc_info.value)
    
    def test_parse_malformed_url_raises_error(self) -> None:
        """Test that malformed URL raises ValueError."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        malformed_url = "not-a-valid-url"
        
        with pytest.raises(ValueError) as exc_info:
            client.parse_pr_url(malformed_url)
        
        assert "Invalid GitHub PR URL format" in str(exc_info.value)
    
    def test_parse_url_missing_pr_number_raises_error(self) -> None:
        """Test that URL without PR number raises ValueError."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        url = "https://github.com/owner/repo/pull/"
        
        with pytest.raises(ValueError) as exc_info:
            client.parse_pr_url(url)
        
        assert "Invalid GitHub PR URL format" in str(exc_info.value)
    
    def test_parse_url_with_special_characters_in_names(self) -> None:
        """Test parsing URL with hyphens and underscores in owner/repo names."""
        client = GitHubPRClient(github_token="fake_token_for_testing")
        
        url = "https://github.com/my-org_name/my-repo_name/pull/42"
        owner, repo, pr_number = client.parse_pr_url(url)
        
        assert owner == "my-org_name"
        assert repo == "my-repo_name"
        assert pr_number == 42


class TestClientInitialization:
    """Test suite for GitHubPRClient initialization."""
    
    def test_init_with_token_parameter(self) -> None:
        """Test initialization with explicit token parameter."""
        client = GitHubPRClient(github_token="test_token_123")
        assert client is not None
    
    def test_init_without_token_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that initialization without token raises ValueError."""
        # Remove GITHUB_TOKEN from environment
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        # Also clear any .env file loading by mocking getenv
        monkeypatch.setenv("GITHUB_TOKEN", "")
        
        with pytest.raises(ValueError) as exc_info:
            GitHubPRClient()
        
        assert "GitHub token required" in str(exc_info.value)


# Made with Bob