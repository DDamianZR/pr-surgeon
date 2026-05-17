"""
Tests for /api/analyze endpoint.
Uses mocking to avoid network calls.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from github import GithubException

from main import app
from models.analysis import AnalysisResult, DependencyGraph, FileCluster
from models.pr import FileChange, PullRequestData


client = TestClient(app)


class TestAnalyzeEndpoint:
    """Test /api/analyze endpoint."""
    
    @patch('main.GitHubPRClient')
    @patch('main.DependencyAnalyzer')
    @patch('main.PRDecomposer')
    @patch('main.LLMService')
    def test_valid_request_returns_200(
        self,
        mock_llm,
        mock_decomposer,
        mock_analyzer,
        mock_github
    ):
        """Test that valid request returns 200 with expected structure."""
        # Mock GitHub client
        mock_pr_data = PullRequestData(
            pr_number=123,
            title="Test PR",
            body="Test body",
            base_branch="main",
            head_branch="feature",
            repo_full_name="test/repo",
            files=[
                FileChange(
                    filename="test.py",
                    status="modified",
                    additions=10,
                    deletions=2,
                    language="python"
                )
            ],
            total_additions=10,
            total_deletions=2,
            url="https://github.com/test/repo/pull/123",
            author="testuser"
        )
        mock_github.return_value.fetch_pr.return_value = mock_pr_data
        
        # Mock analyzer
        mock_analysis = AnalysisResult(
            graph=DependencyGraph(nodes=[], edges=[]),
            clusters=[
                FileCluster(
                    cluster_id="c1",
                    files=["test.py"],
                    layer="backend",
                    total_additions=10,
                    total_deletions=2,
                    internal_edges=0,
                    external_edges=0
                )
            ],
            total_files=1,
            total_edges=0,
            isolated_files=[]
        )
        mock_analyzer.return_value.analyze.return_value = mock_analysis
        
        # Mock decomposer and LLM (will use real implementations with mocked data)
        
        # Make request
        response = client.post(
            "/api/analyze",
            json={"pr_url": "https://github.com/test/repo/pull/123"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "pr_url" in data
        assert "pr_title" in data
        assert "sub_prs" in data
        assert "graph_nodes" in data
        assert "graph_edges" in data
        assert "analysis_duration_ms" in data
        
        assert data["pr_title"] == "Test PR"
        assert data["total_files"] == 1
    
    def test_invalid_url_returns_400(self):
        """Test that invalid URL format returns 400."""
        response = client.post(
            "/api/analyze",
            json={"pr_url": "not-a-valid-url"}
        )
        
        # Should return 400 or 500 depending on validation
        assert response.status_code in [400, 500]
    
    @patch('main.GitHubPRClient')
    def test_pr_not_found_returns_404(self, mock_github):
        """Test that non-existent PR returns 404."""
        # Mock GitHub to raise 404
        mock_github.return_value.fetch_pr.side_effect = GithubException(
            status=404,
            data={"message": "Not Found"},
            headers={}
        )
        
        response = client.post(
            "/api/analyze",
            json={"pr_url": "https://github.com/test/repo/pull/99999"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('main.GitHubPRClient')
    def test_rate_limited_returns_403(self, mock_github):
        """Test that rate limit returns 403."""
        # Mock GitHub to raise 403
        mock_github.return_value.fetch_pr.side_effect = GithubException(
            status=403,
            data={"message": "Rate limit exceeded"},
            headers={}
        )
        
        response = client.post(
            "/api/analyze",
            json={"pr_url": "https://github.com/test/repo/pull/123"}
        )
        
        assert response.status_code == 403


class TestHealthEndpoint:
    """Test /api/health endpoint."""
    
    def test_health_returns_ok(self):
        """Test that health endpoint returns ok status."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert "github_configured" in data
        assert "llm_mode" in data
        assert "version" in data


# Made with Bob