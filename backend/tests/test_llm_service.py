"""
Tests for LLM Service.
"""

import json
import tempfile
from pathlib import Path

import pytest

from models.subpr import SubPR
from services.llm_service import LLMService


class TestLLMService:
    """Test LLM service enrichment."""
    
    def test_template_mode_for_each_layer(self):
        """Test template generation for all layers."""
        service = LLMService(mode="template")
        
        layers = ["schema", "backend", "frontend", "tests", "config", "docs", "mixed"]
        
        for layer in layers:
            sub_pr = SubPR(
                id=f"test_{layer}",
                suggested_title=f"Test {layer}",
                files=[f"{layer}/file.py"],
                merge_order=1,
                rationale="Test",
                risk_level="medium",
                estimated_review_time_min=30,
                layer=layer,
                size_lines=100
            )
            
            enriched = service.enrich_subprs("https://github.com/test/repo/pull/1", [sub_pr])
            
            assert len(enriched) == 1
            assert enriched[0].description_markdown
            assert enriched[0].testing_recommendations
            assert enriched[0].suggested_reviewer_profile
            assert layer in enriched[0].description_markdown.lower()
    
    def test_pregenerated_mode_reads_json_correctly(self, tmp_path):
        """Test that pregenerated mode loads from JSON."""
        # Create temporary enrichments directory
        enrichments_dir = tmp_path / "demo_data" / "enrichments"
        enrichments_dir.mkdir(parents=True)
        
        # Create test data
        pr_url = "https://github.com/test/repo/pull/123"
        import hashlib
        pr_id = hashlib.sha256(pr_url.encode()).hexdigest()[:12]
        
        test_data = [{
            "id": "test123",
            "suggested_title": "Test PR",
            "files": ["test.py"],
            "merge_order": 1,
            "rationale": "Test rationale",
            "risk_level": "low",
            "estimated_review_time_min": 20,
            "layer": "backend",
            "size_lines": 50,
            "description_markdown": "# Test Description",
            "testing_recommendations": ["Test rec 1"],
            "potential_issues": [],
            "suggested_reviewer_profile": "Backend engineer"
        }]
        
        cache_file = enrichments_dir / f"{pr_id}.json"
        with open(cache_file, 'w') as f:
            json.dump(test_data, f)
        
        # Temporarily change working directory
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            service = LLMService(mode="bob_pregenerated")
            sub_pr = SubPR(
                id="test123",
                suggested_title="Test",
                files=["test.py"],
                merge_order=1,
                rationale="Test",
                risk_level="low",
                estimated_review_time_min=20,
                layer="backend",
                size_lines=50
            )
            
            enriched = service.enrich_subprs(pr_url, [sub_pr])
            
            assert len(enriched) == 1
            assert enriched[0].description_markdown == "# Test Description"
            assert enriched[0].testing_recommendations == ["Test rec 1"]
        finally:
            os.chdir(old_cwd)
    
    def test_pregenerated_mode_falls_back_to_template(self):
        """Test fallback to template mode when JSON missing."""
        service = LLMService(mode="bob_pregenerated")
        
        sub_pr = SubPR(
            id="nonexistent",
            suggested_title="Test",
            files=["test.py"],
            merge_order=1,
            rationale="Test",
            risk_level="medium",
            estimated_review_time_min=30,
            layer="backend",
            size_lines=100
        )
        
        # Should fall back to template mode
        enriched = service.enrich_subprs("https://github.com/nonexistent/repo/pull/999", [sub_pr])
        
        assert len(enriched) == 1
        assert enriched[0].description_markdown
        assert "backend" in enriched[0].description_markdown.lower()
    
    def test_cache_returns_same_object_on_repeated_call(self):
        """Test that cache works correctly."""
        service = LLMService(mode="template")
        
        sub_pr = SubPR(
            id="cached_test",
            suggested_title="Test",
            files=["test.py"],
            merge_order=1,
            rationale="Test",
            risk_level="low",
            estimated_review_time_min=20,
            layer="tests",
            size_lines=50
        )
        
        # First call
        enriched1 = service.enrich_subprs("https://github.com/test/repo/pull/1", [sub_pr])
        
        # Second call with same sub_pr
        enriched2 = service.enrich_subprs("https://github.com/test/repo/pull/1", [sub_pr])
        
        # Should return same cached object
        assert enriched1[0] is enriched2[0]
    
    def test_risk_level_affects_potential_issues(self):
        """Test that risk level determines potential issues."""
        service = LLMService(mode="template")
        
        # High risk
        high_risk = SubPR(
            id="high", suggested_title="Test", files=["test.py"],
            merge_order=1, rationale="Test", risk_level="high",
            estimated_review_time_min=60, layer="schema", size_lines=200
        )
        
        # Low risk
        low_risk = SubPR(
            id="low", suggested_title="Test", files=["test.py"],
            merge_order=1, rationale="Test", risk_level="low",
            estimated_review_time_min=20, layer="docs", size_lines=50
        )
        
        high_enriched = service.enrich_subprs("https://github.com/test/repo/pull/1", [high_risk])
        low_enriched = service.enrich_subprs("https://github.com/test/repo/pull/1", [low_risk])
        
        # High risk should have more potential issues
        assert len(high_enriched[0].potential_issues) > len(low_enriched[0].potential_issues)
        assert len(low_enriched[0].potential_issues) == 0


# Made with Bob