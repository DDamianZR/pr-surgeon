"""
LLM Service for enriching sub-PRs.
Supports template mode (deterministic) and bob_pregenerated mode (cached).
"""

import hashlib
import json
import os
from pathlib import Path

from loguru import logger

from models.subpr import EnrichedSubPR, SubPR


class LLMService:
    """
    Service for enriching sub-PRs with descriptions and recommendations.
    
    Modes:
    - template: Deterministic string templates (default)
    - bob_pregenerated: Load from cached JSON files
    """
    
    def __init__(self, mode: str | None = None):
        """
        Initialize LLM service.
        
        Args:
            mode: "template" or "bob_pregenerated". Defaults to LLM_MODE env var or "template"
        """
        self.mode = mode or os.getenv("LLM_MODE", "template")
        self._cache: dict[str, EnrichedSubPR] = {}
        logger.info(f"LLMService initialized in {self.mode} mode")
    
    def enrich_subprs(self, pr_url: str, sub_prs: list[SubPR]) -> list[EnrichedSubPR]:
        """
        Enrich sub-PRs with descriptions and recommendations.
        
        Args:
            pr_url: Original PR URL
            sub_prs: List of SubPR objects to enrich
            
        Returns:
            List of EnrichedSubPR objects
        """
        if self.mode == "bob_pregenerated":
            # Try to load from cache
            cached = self._load_pregenerated(pr_url, sub_prs)
            if cached:
                logger.info(f"Loaded {len(cached)} enriched sub-PRs from cache")
                return cached
            
            # Fall back to template mode
            logger.warning(f"Pregenerated data not found for {pr_url}, falling back to template mode")
        
        # Use template mode
        enriched = []
        for sub_pr in sub_prs:
            # Check in-memory cache first
            if sub_pr.id in self._cache:
                enriched.append(self._cache[sub_pr.id])
            else:
                enriched_subpr = self._enrich_with_template(sub_pr)
                self._cache[sub_pr.id] = enriched_subpr
                enriched.append(enriched_subpr)
        
        return enriched
    
    def _load_pregenerated(self, pr_url: str, sub_prs: list[SubPR]) -> list[EnrichedSubPR] | None:
        """
        Load pregenerated enrichments from JSON file.
        
        Args:
            pr_url: PR URL to generate cache key
            sub_prs: List of sub-PRs (for validation)
            
        Returns:
            List of EnrichedSubPR if found, None otherwise
        """
        # Generate PR ID from URL
        pr_id = hashlib.sha256(pr_url.encode()).hexdigest()[:12]
        cache_file = Path("demo_data/enrichments") / f"{pr_id}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse as EnrichedSubPR objects
            enriched = [EnrichedSubPR(**item) for item in data]
            
            # Store in memory cache
            for item in enriched:
                self._cache[item.id] = item
            
            return enriched
        except Exception as e:
            logger.error(f"Failed to load pregenerated data from {cache_file}: {e}")
            return None
    
    def _enrich_with_template(self, sub_pr: SubPR) -> EnrichedSubPR:
        """
        Enrich a sub-PR using deterministic templates.
        
        Args:
            sub_pr: SubPR to enrich
            
        Returns:
            EnrichedSubPR with template-generated content
        """
        # Generate description
        description = self._generate_description(sub_pr)
        
        # Generate testing recommendations
        testing_recs = self._generate_testing_recommendations(sub_pr.layer)
        
        # Generate potential issues
        potential_issues = self._generate_potential_issues(sub_pr.risk_level)
        
        # Generate reviewer profile
        reviewer_profile = self._generate_reviewer_profile(sub_pr.layer)
        
        return EnrichedSubPR(
            **sub_pr.model_dump(),
            description_markdown=description,
            testing_recommendations=testing_recs,
            potential_issues=potential_issues,
            suggested_reviewer_profile=reviewer_profile,
        )
    
    @staticmethod
    def _generate_description(sub_pr: SubPR) -> str:
        """Generate markdown description for sub-PR."""
        risk_explanations = {
            "high": "Schema or core config changes. Coordinate with team before merging. Consider rollback plan.",
            "medium": "Standard review. Peer review recommended before merging.",
            "low": "Low-risk changes. Can merge after standard review.",
        }
        
        file_list = "\n".join(f"- `{f}`" for f in sub_pr.files)
        
        return f"""## Overview
This sub-PR contains {len(sub_pr.files)} file(s) from the **{sub_pr.layer}** layer.

## Files Changed
{file_list}

## Merge Order
This is sub-PR #{sub_pr.merge_order} in the decomposition.
Merge after lower-numbered sub-PRs are reviewed and merged.

## Risk Assessment
Risk level: **{sub_pr.risk_level}**

{risk_explanations[sub_pr.risk_level]}
"""
    
    @staticmethod
    def _generate_testing_recommendations(layer: str) -> list[str]:
        """Generate testing recommendations based on layer."""
        recommendations = {
            "schema": [
                "Run database migration tests",
                "Verify rollback procedure",
                "Test against production-like data"
            ],
            "backend": [
                "Run unit tests for affected modules",
                "Integration tests with downstream services",
                "Check API contract compatibility"
            ],
            "frontend": [
                "Visual regression tests",
                "Cross-browser testing",
                "Accessibility check"
            ],
            "tests": [
                "Verify test coverage didn't regress"
            ],
            "config": [
                "Validate config syntax",
                "Test deployment with new config"
            ],
            "docs": [
                "Review for clarity and accuracy"
            ],
        }
        
        return recommendations.get(layer, [
            "Standard test suite",
            "Manual smoke test"
        ])
    
    @staticmethod
    def _generate_potential_issues(risk_level: str) -> list[str]:
        """Generate potential issues based on risk level."""
        issues = {
            "high": [
                "Coordinate with team before merging",
                "Consider feature flag for rollout",
                "Plan rollback procedure"
            ],
            "medium": [
                "Review with at least one peer",
                "Verify no breaking API changes"
            ],
            "low": []
        }
        
        return issues[risk_level]
    
    @staticmethod
    def _generate_reviewer_profile(layer: str) -> str:
        """Generate suggested reviewer profile based on layer."""
        profiles = {
            "schema": "Senior backend engineer with database migration experience",
            "backend": "Backend engineer familiar with affected modules",
            "frontend": "Frontend engineer with UX awareness",
            "tests": "Any engineer with testing focus",
            "config": "DevOps or platform engineer",
            "docs": "Technical writer or product manager",
        }
        
        return profiles.get(layer, "Tech lead familiar with the codebase")


# Made with Bob