"""
PR Surgeon Backend API
FastAPI application for decomposing monster Pull Requests into safe, reviewable sub-PRs.
"""

import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from github import GithubException
from loguru import logger

from models.api import AnalyzeRequest, AnalyzeResponse, HealthResponse, ReactFlowEdge, ReactFlowNode
from services.decomposer import PRDecomposer
from services.dependency_analyzer import DependencyAnalyzer
from services.github_client import GitHubPRClient
from services.llm_service import LLMService

# Load environment variables
load_dotenv()

# Configure loguru for structured logging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    serialize=False,  # Set to True for JSON output in production
)

# Initialize FastAPI app
app = FastAPI(
    title="PR Surgeon API",
    description="Decompose monster Pull Requests into safe, reviewable sub-PRs",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add FRONTEND_URL from environment if present
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, Any]:
    """
    Root endpoint - API status check.
    
    Returns:
        dict: Status information including version
    """
    logger.info("Root endpoint accessed")
    return {
        "status": "PR Surgeon API alive",
        "version": "0.1.0"
    }


@app.get("/api/health")
async def health_check() -> HealthResponse:
    """
    Health check endpoint - verifies configuration and service availability.
    
    Returns:
        HealthResponse: Health status including GitHub and LLM configuration
    """
    github_token = os.getenv("GITHUB_TOKEN")
    llm_mode = os.getenv("LLM_MODE", "template")
    
    github_configured = bool(github_token and len(github_token) > 0)
    
    logger.info(
        "Health check",
        extra={
            "github_configured": github_configured,
            "llm_mode": llm_mode
        }
    )
    
    return HealthResponse(
        status="ok",
        github_configured=github_configured,
        llm_mode=llm_mode,
        version="0.1.0"
    )


@app.post("/api/analyze")
async def analyze_pr(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a Pull Request and decompose it into sub-PRs.
    
    Args:
        request: AnalyzeRequest with pr_url and optional max_files
        
    Returns:
        AnalyzeResponse with sub-PRs and dependency graph
        
    Raises:
        HTTPException: 400 for invalid URL, 404 for PR not found, 403 for auth issues, 500 for other errors
    """
    start_time = time.time()
    
    try:
        logger.info(f"Analyzing PR: {request.pr_url}")
        
        # Initialize services
        github_client = GitHubPRClient()
        analyzer = DependencyAnalyzer()
        decomposer = PRDecomposer()
        llm_service = LLMService()
        
        # Step 1: Fetch PR data
        logger.info("Fetching PR data from GitHub")
        pr_data = github_client.fetch_pr(request.pr_url)
        
        # Check file limit
        if len(pr_data.files) > request.max_files:
            raise HTTPException(
                status_code=400,
                detail=f"PR has {len(pr_data.files)} files, exceeds max_files limit of {request.max_files}"
            )
        
        # Step 2: Analyze dependencies
        logger.info(f"Analyzing dependencies for {len(pr_data.files)} files")
        analysis = analyzer.analyze(pr_data.files)
        
        # Step 3: Decompose into sub-PRs
        logger.info(f"Decomposing into sub-PRs from {len(analysis.clusters)} clusters")
        sub_prs = decomposer.decompose(pr_data, analysis)
        
        # Step 4: Enrich sub-PRs
        logger.info(f"Enriching {len(sub_prs)} sub-PRs")
        enriched_sub_prs = llm_service.enrich_subprs(request.pr_url, sub_prs)
        
        # Step 5: Build React Flow data
        logger.info("Building React Flow visualization data")
        
        # Create file-to-layer mapping
        file_to_layer = {}
        for cluster in analysis.clusters:
            for file in cluster.files:
                file_to_layer[file] = cluster.layer
        
        # Build nodes
        graph_nodes = [
            ReactFlowNode(
                id=node.id,
                data={
                    "label": node.label,
                    "layer": file_to_layer.get(node.id, "unknown"),
                    "full_path": node.id,
                    "language": node.language,
                },
                position={"x": 0, "y": 0},
                type="default"
            )
            for node in analysis.graph.nodes
        ]
        
        # Build edges
        graph_edges = [
            ReactFlowEdge(
                id=f"{edge.source}->{edge.target}",
                source=edge.source,
                target=edge.target,
                animated=False
            )
            for edge in analysis.graph.edges
        ]
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Analysis complete in {duration_ms}ms: {len(enriched_sub_prs)} sub-PRs created")
        
        return AnalyzeResponse(
            pr_url=request.pr_url,
            pr_title=pr_data.title,
            repo_full_name=pr_data.repo_full_name,
            total_files=len(pr_data.files),
            total_additions=pr_data.total_additions,
            total_deletions=pr_data.total_deletions,
            sub_prs=enriched_sub_prs,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            analysis_duration_ms=duration_ms
        )
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except GithubException as e:
        if e.status == 404:
            logger.error(f"PR not found: {request.pr_url}")
            raise HTTPException(status_code=404, detail="Pull Request not found")
        elif e.status == 403:
            logger.error(f"GitHub auth issue: {e}")
            raise HTTPException(status_code=403, detail="GitHub authentication failed or rate limited")
        else:
            logger.error(f"GitHub API error: {e}")
            raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error analyzing PR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during analysis")


@app.on_event("startup")
async def startup_event() -> None:
    """Log startup information."""
    logger.info("PR Surgeon API starting up")
    logger.info(f"CORS allowed origins: {allowed_origins}")
    logger.info(f"GitHub configured: {bool(os.getenv('GITHUB_TOKEN'))}")
    logger.info(f"LLM mode: {os.getenv('LLM_MODE', 'fallback')}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Log shutdown information."""
    logger.info("PR Surgeon API shutting down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Made with Bob
