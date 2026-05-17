"""
PR Decomposer service.
Converts dependency analysis clusters into reviewable sub-PRs.
"""

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from loguru import logger

from models.analysis import AnalysisResult, FileCluster
from models.pr import FileChange, PullRequestData
from models.subpr import SubPR


class PRDecomposer:
    """
    Decomposes a Pull Request into smaller, reviewable sub-PRs.
    
    Takes dependency analysis results and creates a sequence of sub-PRs
    that respect architectural layers and merge order.
    """
    
    # Layer priority for merge ordering
    LAYER_PRIORITY = {
        "schema": 1,
        "config": 2,
        "backend": 3,
        "frontend": 4,
        "tests": 5,
        "docs": 6,
        "mixed": 7,
        "unknown": 8,
    }
    
    def decompose(
        self,
        pr_data: PullRequestData,
        analysis: AnalysisResult
    ) -> list[SubPR]:
        """
        Decompose a PR into sub-PRs based on dependency analysis.
        
        Args:
            pr_data: Original PR data with file changes
            analysis: Dependency analysis results with clusters
            
        Returns:
            List of SubPR objects in merge order
        """
        logger.info(f"Decomposing PR with {len(analysis.clusters)} clusters")
        
        # Build file map for quick lookup
        file_map = {f.filename: f for f in pr_data.files}
        
        # Convert each cluster to a SubPR
        sub_prs = []
        for cluster in analysis.clusters:
            sub_pr = self._cluster_to_subpr(cluster, file_map)
            sub_prs.append(sub_pr)
        
        # Sort by layer priority, then by size (smallest first within layer)
        sub_prs.sort(key=lambda sp: (
            self.LAYER_PRIORITY.get(sp.layer, 99),
            len(sp.files)
        ))
        
        # Assign sequential merge order
        for i, sub_pr in enumerate(sub_prs, start=1):
            sub_pr.merge_order = i
        
        logger.info(f"Created {len(sub_prs)} sub-PRs")
        return sub_prs
    
    def _cluster_to_subpr(
        self,
        cluster: FileCluster,
        file_map: dict[str, Any]
    ) -> SubPR:
        """
        Convert a FileCluster to a SubPR.
        
        Args:
            cluster: FileCluster from dependency analysis
            file_map: Map of filename to FileChange object
            
        Returns:
            SubPR object
        """
        # Generate deterministic ID
        subpr_id = self._generate_id(cluster.files)
        
        # Find common prefix and extract descriptive name
        descriptive_name = self._find_descriptive_name(cluster.files)
        
        # Generate title based on layer
        title = self._generate_title(cluster.layer, descriptive_name)
        
        # Calculate total lines changed
        size_lines = sum(
            file_map[f].additions + file_map[f].deletions
            for f in cluster.files
            if f in file_map
        )
        
        # Estimate review time
        review_time = self._estimate_review_time(len(cluster.files), size_lines)
        
        # Assess risk level
        risk_level = self._assess_risk(cluster.layer, len(cluster.files))
        
        # Generate rationale
        rationale = self._generate_rationale(
            cluster.layer,
            len(cluster.files),
            descriptive_name,
            review_time
        )
        
        return SubPR(
            id=subpr_id,
            suggested_title=title,
            files=sorted(cluster.files),
            merge_order=0,  # Will be set later during sorting
            rationale=rationale,
            risk_level=risk_level,
            estimated_review_time_min=review_time,
            layer=cluster.layer,
            size_lines=size_lines,
        )
    
    @staticmethod
    def _generate_id(files: list[str]) -> str:
        """
        Generate deterministic ID from file list.
        
        Args:
            files: List of filenames
            
        Returns:
            12-character hex hash
        """
        sorted_files = sorted(files)
        content = "|".join(sorted_files).encode()
        return hashlib.sha256(content).hexdigest()[:12]
    
    @staticmethod
    def _find_descriptive_name(files: list[str]) -> str:
        """
        Find the most specific common prefix among files and extract descriptive name.
        
        Uses the last segment of the common prefix as the descriptive name.
        This avoids duplicate titles like "Tests: tests test suite".
        
        Examples:
            ["tests/composite_pk/test_create.py", "tests/composite_pk/test_delete.py"]
            → common prefix: "tests/composite_pk" → name: "composite_pk"
            
            ["django/db/models/base.py", "django/db/models/options.py"]
            → common prefix: "django/db/models" → name: "models"
            
            ["docs/ref/models/fields.md", "docs/ref/models/queries.md"]
            → common prefix: "docs/ref/models" → name: "models"
        
        Args:
            files: List of file paths
            
        Returns:
            Descriptive name extracted from common prefix
        """
        if not files:
            return "root"
        
        # Convert to Path objects
        paths = [Path(file) for file in files]
        
        # Find common prefix by comparing path parts
        if len(paths) == 1:
            # Single file: use parent directory name or filename without extension
            parts = paths[0].parts
            if len(parts) > 1:
                return parts[-2]  # Parent directory
            return paths[0].stem  # Filename without extension
        
        # Multiple files: find longest common prefix
        common_parts = []
        first_parts = paths[0].parts
        
        for i, part in enumerate(first_parts[:-1]):  # Exclude filename
            if all(len(p.parts) > i and p.parts[i] == part for p in paths):
                common_parts.append(part)
            else:
                break
        
        if not common_parts:
            # No common prefix, use most common first segment
            first_segments = [p.parts[0] for p in paths if len(p.parts) > 0]
            if first_segments:
                counter = Counter(first_segments)
                return counter.most_common(1)[0][0]
            return "root"
        
        # Return last segment of common prefix as descriptive name
        return common_parts[-1]
    
    @staticmethod
    def _generate_title(layer: str, descriptive_name: str) -> str:
        """
        Generate suggested title based on layer and descriptive name.
        
        Uses the last segment of the common prefix to create unique,
        meaningful titles that avoid duplication.
        
        Args:
            layer: Architectural layer
            descriptive_name: Descriptive name from common prefix
            
        Returns:
            Suggested PR title
        """
        templates = {
            "schema": f"Schema: {descriptive_name} migrations",
            "backend": f"Backend: {descriptive_name} module",
            "frontend": f"Frontend: {descriptive_name} components",
            "tests": f"Tests: {descriptive_name} suite",
            "config": f"Config: {descriptive_name}",
            "docs": f"Docs: {descriptive_name} reference",
        }
        
        return templates.get(layer, f"Changes: {descriptive_name}")
    
    @staticmethod
    def _estimate_review_time(num_files: int, total_lines: int) -> int:
        """
        Estimate review time in minutes.
        
        Formula: 10 base + 2 min per file + 1 min per 50 lines, capped at 240 min
        
        Args:
            num_files: Number of files in sub-PR
            total_lines: Total lines changed
            
        Returns:
            Estimated review time in minutes
        """
        base_time = 10
        file_time = num_files * 2
        line_time = total_lines // 50
        
        total = base_time + file_time + line_time
        return min(240, total)
    
    @staticmethod
    def _assess_risk(layer: str, num_files: int) -> Literal["low", "medium", "high"]:
        """
        Assess risk level based on layer and size.
        
        Args:
            layer: Architectural layer
            num_files: Number of files
            
        Returns:
            Risk level: "low", "medium", or "high"
        """
        # Schema with 3+ files is high risk
        if layer == "schema" and num_files >= 3:
            return "high"
        
        # Config with 5+ files is high risk
        if layer == "config" and num_files >= 5:
            return "high"
        
        # Tests and docs are low risk
        if layer in ["tests", "docs"]:
            return "low"
        
        # Everything else is medium
        return "medium"
    
    @staticmethod
    def _generate_rationale(
        layer: str,
        num_files: int,
        top_dir: str,
        review_time: int
    ) -> str:
        """
        Generate rationale for the sub-PR grouping.
        
        Args:
            layer: Architectural layer
            num_files: Number of files
            top_dir: Top directory
            review_time: Estimated review time
            
        Returns:
            Rationale text
        """
        return (
            f"This sub-PR groups {num_files} file(s) from the {layer} layer. "
            f"Top directory: {top_dir}. "
            f"Estimated review: ~{review_time}min."
        )


# Made with Bob