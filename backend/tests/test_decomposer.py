"""
Tests for PR Decomposer service.
"""

import pytest

from models.analysis import AnalysisResult, DependencyGraph, FileCluster
from models.pr import FileChange, PullRequestData
from services.decomposer import PRDecomposer


class TestPRDecomposer:
    """Test PR decomposition logic."""
    
    def test_decompose_with_known_layers(self):
        """Test decomposition with clusters of known layers."""
        decomposer = PRDecomposer()
        
        # Create synthetic PR data
        pr_data = PullRequestData(
            pr_number=123,
            title="Test PR",
            body="Test",
            base_branch="main",
            head_branch="feature",
            repo_full_name="test/repo",
            files=[
                FileChange(filename="schema/migration_001.sql", status="added", additions=50, deletions=0, language=None),
                FileChange(filename="backend/api/routes.py", status="modified", additions=30, deletions=10, language="python"),
                FileChange(filename="frontend/components/Button.tsx", status="modified", additions=20, deletions=5, language="typescript"),
            ],
            total_additions=100,
            total_deletions=15,
            url="https://github.com/test/repo/pull/123",
            author="testuser"
        )
        
        # Create synthetic analysis with 3 clusters
        analysis = AnalysisResult(
            graph=DependencyGraph(nodes=[], edges=[]),
            clusters=[
                FileCluster(
                    cluster_id="cluster1",
                    files=["schema/migration_001.sql"],
                    layer="schema",
                    total_additions=50,
                    total_deletions=0,
                    internal_edges=0,
                    external_edges=0
                ),
                FileCluster(
                    cluster_id="cluster2",
                    files=["backend/api/routes.py"],
                    layer="backend",
                    total_additions=30,
                    total_deletions=10,
                    internal_edges=0,
                    external_edges=0
                ),
                FileCluster(
                    cluster_id="cluster3",
                    files=["frontend/components/Button.tsx"],
                    layer="frontend",
                    total_additions=20,
                    total_deletions=5,
                    internal_edges=0,
                    external_edges=0
                ),
            ],
            total_files=3,
            total_edges=0,
            isolated_files=[]
        )
        
        # Decompose
        sub_prs = decomposer.decompose(pr_data, analysis)
        
        # Verify we got 3 sub-PRs
        assert len(sub_prs) == 3
        
        # Verify merge order is sequential
        merge_orders = [sp.merge_order for sp in sub_prs]
        assert merge_orders == [1, 2, 3]
        
        # Verify layer priority (schema first, then backend, then frontend)
        assert sub_prs[0].layer == "schema"
        assert sub_prs[1].layer == "backend"
        assert sub_prs[2].layer == "frontend"
    
    def test_merge_order_respects_layer_priority(self):
        """Test that merge order follows layer priority."""
        decomposer = PRDecomposer()
        
        pr_data = PullRequestData(
            pr_number=123,
            title="Test",
            body="Test",
            base_branch="main",
            head_branch="feature",
            repo_full_name="test/repo",
            files=[
                FileChange(filename="tests/test_api.py", status="added", additions=100, deletions=0, language="python"),
                FileChange(filename="schema/init.sql", status="added", additions=50, deletions=0, language=None),
                FileChange(filename="docs/README.md", status="modified", additions=10, deletions=2, language="markdown"),
            ],
            total_additions=160,
            total_deletions=2,
            url="https://github.com/test/repo/pull/123",
            author="testuser"
        )
        
        analysis = AnalysisResult(
            graph=DependencyGraph(nodes=[], edges=[]),
            clusters=[
                FileCluster(cluster_id="c1", files=["tests/test_api.py"], layer="tests", 
                           total_additions=100, total_deletions=0, internal_edges=0, external_edges=0),
                FileCluster(cluster_id="c2", files=["schema/init.sql"], layer="schema",
                           total_additions=50, total_deletions=0, internal_edges=0, external_edges=0),
                FileCluster(cluster_id="c3", files=["docs/README.md"], layer="docs",
                           total_additions=10, total_deletions=2, internal_edges=0, external_edges=0),
            ],
            total_files=3,
            total_edges=0,
            isolated_files=[]
        )
        
        sub_prs = decomposer.decompose(pr_data, analysis)
        
        # Schema should be first (priority 1)
        assert sub_prs[0].layer == "schema"
        assert sub_prs[0].merge_order == 1
        
        # Tests should be second (priority 5)
        assert sub_prs[1].layer == "tests"
        assert sub_prs[1].merge_order == 2
        
        # Docs should be last (priority 6)
        assert sub_prs[2].layer == "docs"
        assert sub_prs[2].merge_order == 3
    
    def test_risk_classification(self):
        """Test risk level classification rules."""
        decomposer = PRDecomposer()
        
        # Schema with 3+ files → high risk
        assert decomposer._assess_risk("schema", 3) == "high"
        assert decomposer._assess_risk("schema", 2) == "medium"
        
        # Config with 5+ files → high risk
        assert decomposer._assess_risk("config", 5) == "high"
        assert decomposer._assess_risk("config", 4) == "medium"
        
        # Tests and docs → low risk
        assert decomposer._assess_risk("tests", 10) == "low"
        assert decomposer._assess_risk("docs", 10) == "low"
        
        # Everything else → medium
        assert decomposer._assess_risk("backend", 5) == "medium"
        assert decomposer._assess_risk("frontend", 5) == "medium"
    
    def test_estimated_review_time_has_cap(self):
        """Test that review time estimate is capped at 240 minutes."""
        decomposer = PRDecomposer()
        
        # Large PR should be capped
        time = decomposer._estimate_review_time(num_files=100, total_lines=50000)
        assert time == 240
        
        # Small PR should not hit cap
        time = decomposer._estimate_review_time(num_files=5, total_lines=200)
        assert time < 240
        assert time > 0
    
    def test_deterministic_id_generation(self):
        """Test that sub-PR IDs are deterministic."""
        decomposer = PRDecomposer()
        
        files1 = ["a.py", "b.py", "c.py"]
        files2 = ["c.py", "a.py", "b.py"]  # Same files, different order
        
        id1 = decomposer._generate_id(files1)
        id2 = decomposer._generate_id(files2)
        
        # Should be identical (deterministic)
        assert id1 == id2
        assert len(id1) == 12  # 12-character hex


# Made with Bob