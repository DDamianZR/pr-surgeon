"""
Pydantic models for Sub-PR decomposition.
Defines data contracts for sub-PRs and their enriched versions.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class SubPR(BaseModel):
    """
    Represents a sub-PR in the decomposition.
    
    Attributes:
        id: Deterministic hash of the file set
        suggested_title: Human-readable title for the sub-PR
        files: List of filenames in this sub-PR
        merge_order: Sequential order for merging (1-based)
        rationale: Explanation of why these files are grouped
        risk_level: Assessment of merge risk
        estimated_review_time_min: Estimated review time in minutes
        layer: Architectural layer classification
        size_lines: Total lines changed (additions + deletions)
    """
    
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": "abc123def456",
        "suggested_title": "Schema: composite PK migrations",
        "files": ["django/db/backends/base/schema.py"],
        "merge_order": 1,
        "rationale": "This sub-PR groups 5 files from the schema layer.",
        "risk_level": "high",
        "estimated_review_time_min": 60,
        "layer": "schema",
        "size_lines": 247
    }]})
    
    id: str
    suggested_title: str
    files: list[str]
    merge_order: int
    rationale: str
    risk_level: Literal["low", "medium", "high"]
    estimated_review_time_min: int
    layer: str
    size_lines: int


class EnrichedSubPR(SubPR):
    """
    Sub-PR with additional LLM-generated enrichments.
    
    Extends SubPR with detailed descriptions, recommendations, and reviewer guidance.
    
    Attributes:
        description_markdown: Detailed markdown description
        testing_recommendations: List of testing suggestions
        potential_issues: List of potential problems to watch for
        suggested_reviewer_profile: Description of ideal reviewer
    """
    
    description_markdown: str
    testing_recommendations: list[str]
    potential_issues: list[str]
    suggested_reviewer_profile: str


# Made with Bob