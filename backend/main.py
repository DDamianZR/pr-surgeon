"""
PR Surgeon Backend API
FastAPI application for decomposing monster Pull Requests into safe, reviewable sub-PRs.
"""

import os
import sys
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

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
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint - verifies configuration and service availability.
    
    Returns:
        dict: Health status including GitHub and LLM configuration
    """
    github_token = os.getenv("GITHUB_TOKEN")
    llm_mode = os.getenv("LLM_MODE", "fallback")
    
    github_configured = bool(github_token and len(github_token) > 0)
    
    logger.info(
        "Health check",
        extra={
            "github_configured": github_configured,
            "llm_mode": llm_mode
        }
    )
    
    return {
        "status": "ok",
        "github_configured": github_configured,
        "llm_mode": llm_mode
    }


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
