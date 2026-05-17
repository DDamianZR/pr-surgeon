"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field

from models.subpr import EnrichedSubPR


class AnalyzeRequest(BaseModel):
    """
    Request body for /api/analyze endpoint.
    
    Attributes:
        pr_url: GitHub PR URL to analyze
        max_files: Maximum number of files to process (default 200)
    """
    pr_url: str
    max_files: int = 200
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "pr_url": "https://github.com/django/django/pull/18056",
                "max_files": 200
            }
        }
    }


class ReactFlowNode(BaseModel):
    """
    React Flow node format for frontend visualization.
    
    Attributes:
        id: Unique node identifier (filename)
        data: Node data (label, layer, etc.)
        position: Node position (x, y coordinates)
        type: Node type for React Flow
    """
    id: str
    data: dict
    position: dict = Field(default={"x": 0, "y": 0})
    type: str = "default"


class ReactFlowEdge(BaseModel):
    """
    React Flow edge format for frontend visualization.
    
    Attributes:
        id: Unique edge identifier
        source: Source node ID (filename)
        target: Target node ID (filename)
        animated: Whether edge should be animated
    """
    id: str
    source: str
    target: str
    animated: bool = False


class AnalyzeResponse(BaseModel):
    """
    Response body for /api/analyze endpoint.
    
    Attributes:
        pr_url: Original PR URL
        pr_title: PR title from GitHub
        repo_full_name: Repository in format "owner/repo"
        total_files: Total number of files changed
        total_additions: Total lines added
        total_deletions: Total lines deleted
        sub_prs: List of enriched sub-PRs
        graph_nodes: React Flow nodes for visualization
        graph_edges: React Flow edges for visualization
        analysis_duration_ms: Time taken for analysis in milliseconds
    """
    pr_url: str
    pr_title: str
    repo_full_name: str
    total_files: int
    total_additions: int
    total_deletions: int
    sub_prs: list[EnrichedSubPR]
    graph_nodes: list[ReactFlowNode]
    graph_edges: list[ReactFlowEdge]
    analysis_duration_ms: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "pr_url": "https://github.com/django/django/pull/18056",
                "pr_title": "Fixed composite primary key migrations",
                "repo_full_name": "django/django",
                "total_files": 43,
                "total_additions": 523,
                "total_deletions": 187,
                "sub_prs": [],
                "graph_nodes": [],
                "graph_edges": [],
                "analysis_duration_ms": 1234
            }
        }
    }


class HealthResponse(BaseModel):
    """
    Response body for /api/health endpoint.
    
    Attributes:
        status: Health status ("ok" or "error")
        github_configured: Whether GitHub token is configured
        llm_mode: Current LLM mode ("template" or "bob_pregenerated")
        version: API version
    """
    status: str
    github_configured: bool
    llm_mode: str
    version: str = "0.1.0"


# Made with Bob