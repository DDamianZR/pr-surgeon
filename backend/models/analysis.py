"""
Pydantic models for dependency analysis.
Defines data contracts for imports, graphs, clusters, and analysis results.
"""

import hashlib
from typing import Literal

from pydantic import BaseModel, Field


class Import(BaseModel):
    """
    Represents a single import statement extracted from source code.
    
    Attributes:
        module_path: The imported module path (e.g., "models.user" or "./utils")
        imported_names: List of specific names imported (e.g., ["User", "Role"])
        is_relative: Whether this is a relative import (starts with . or ..)
        line_number: Line number where the import appears (optional)
    """
    module_path: str
    imported_names: list[str] = Field(default_factory=list)
    is_relative: bool = False
    line_number: int | None = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "module_path": "models.user",
                "imported_names": ["User", "Role"],
                "is_relative": False,
                "line_number": 5
            }
        }
    }


class DependencyEdge(BaseModel):
    """
    Represents a directed edge in the dependency graph.
    
    Attributes:
        source: Filename of the importing file
        target: Filename of the imported file
        weight: Edge weight (default 1.0 for uniform weighting)
    """
    source: str
    target: str
    weight: float = 1.0
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "source": "backend/services/auth.py",
                "target": "backend/models/user.py",
                "weight": 1.0
            }
        }
    }


class GraphNode(BaseModel):
    """
    Represents a node in the dependency graph (a changed file).
    Serializable for frontend React Flow visualization.
    
    Attributes:
        id: Unique identifier (filename)
        label: Display name (typically basename)
        language: Detected programming language
        additions: Number of lines added
        deletions: Number of lines deleted
        layer: Architectural layer classification
    """
    id: str
    label: str
    language: str | None
    additions: int
    deletions: int
    layer: Literal["schema", "backend", "frontend", "tests", "config", "docs", "mixed"] | None = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "backend/services/auth.py",
                "label": "auth.py",
                "language": "python",
                "additions": 25,
                "deletions": 5,
                "layer": "backend"
            }
        }
    }


class DependencyGraph(BaseModel):
    """
    Complete dependency graph with nodes and edges.
    
    Attributes:
        nodes: List of graph nodes (files)
        edges: List of directed edges (dependencies)
    """
    nodes: list[GraphNode]
    edges: list[DependencyEdge]
    
    def to_react_flow(self) -> dict:
        """
        Convert to React Flow format for frontend visualization.
        
        Returns:
            Dictionary with 'nodes' and 'edges' arrays in React Flow format
        """
        return {
            "nodes": [
                {
                    "id": node.id,
                    "data": {
                        "label": node.label,
                        "language": node.language,
                        "layer": node.layer,
                    },
                    "position": {"x": 0, "y": 0},  # Frontend will compute layout
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "id": f"{edge.source}->{edge.target}",
                    "source": edge.source,
                    "target": edge.target,
                }
                for edge in self.edges
            ],
        }
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "nodes": [],
                "edges": []
            }
        }
    }


class FileCluster(BaseModel):
    """
    Represents a cluster of tightly-coupled files.
    
    Attributes:
        cluster_id: Deterministic hash of sorted file list
        files: List of filenames in this cluster
        layer: Architectural layer classification
        total_additions: Sum of additions across all files
        total_deletions: Sum of deletions across all files
        internal_edges: Number of edges within the cluster
        external_edges: Number of edges to other clusters
    """
    cluster_id: str
    files: list[str]
    layer: Literal["schema", "backend", "frontend", "tests", "config", "docs", "mixed"]
    total_additions: int
    total_deletions: int
    internal_edges: int
    external_edges: int
    
    @property
    def cohesion(self) -> float:
        """
        Calculate cluster cohesion as ratio of internal to total edges.
        
        Returns:
            Float between 0 and 1, where 1 means fully cohesive (no external edges)
        """
        total = self.internal_edges + self.external_edges
        return self.internal_edges / total if total > 0 else 0.0
    
    @staticmethod
    def generate_id(files: list[str]) -> str:
        """
        Generate deterministic cluster ID from file list.
        
        Args:
            files: List of filenames
            
        Returns:
            12-character hex hash
        """
        sorted_files = sorted(files)
        content = "".join(sorted_files).encode()
        return hashlib.sha256(content).hexdigest()[:12]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cluster_id": "a1b2c3d4e5f6",
                "files": ["backend/models/user.py", "backend/models/role.py"],
                "layer": "backend",
                "total_additions": 50,
                "total_deletions": 10,
                "internal_edges": 3,
                "external_edges": 2
            }
        }
    }


class AnalysisResult(BaseModel):
    """
    Complete output of dependency analysis.
    
    Attributes:
        graph: The dependency graph with nodes and edges
        clusters: List of detected file clusters
        total_files: Total number of files analyzed
        total_edges: Total number of dependency edges
        isolated_files: Files with no dependencies (degree 0)
    """
    graph: DependencyGraph
    clusters: list[FileCluster]
    total_files: int
    total_edges: int
    isolated_files: list[str] = Field(default_factory=list)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "graph": {"nodes": [], "edges": []},
                "clusters": [],
                "total_files": 42,
                "total_edges": 67,
                "isolated_files": ["README.md", "config.yml"]
            }
        }
    }


# Made with Bob