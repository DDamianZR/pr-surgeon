# Dependency Analyzer Architecture Proposal

**Session**: 04  
**Date**: 2026-05-17  
**Task**: Design the core dependency analysis algorithm for PR Surgeon

---

## Executive Summary

This document proposes the architecture for `DependencyAnalyzer`, the core service that transforms a list of changed files into a dependency graph with detected clusters. The design prioritizes **pragmatic accuracy for MVP** (18-hour constraint) while maintaining extensibility for future language support.

---

## DECISION 1: AST Parsing Approach Per Language

### Recommendation: Tiered parsing strategy

**Python** (Tier 1 - High Precision):
- Use stdlib `ast` module for 100% reliable parsing
- Parse patterns:
  - `import module`
  - `import module as alias`
  - `from module import name`
  - `from module import name as alias`
  - `from .relative import name` (relative imports)
  - `from ..parent import name` (parent relative imports)
- Extract module path from `ast.Import` and `ast.ImportFrom` nodes
- Handle `__init__.py` implicit imports

**JavaScript/TypeScript** (Tier 2 - Pragmatic Regex):
- Regex-based parsing with ~85% precision (acceptable for MVP)
- Parse patterns:
  ```regex
  // ES6 imports
  import\s+.*?\s+from\s+['"]([^'"]+)['"]
  import\s+['"]([^'"]+)['"]
  
  // CommonJS
  require\s*\(\s*['"]([^'"]+)['"]\s*\)
  
  // Dynamic imports
  import\s*\(\s*['"]([^'"]+)['"]\s*\)
  
  // Re-exports
  export\s+.*?\s+from\s+['"]([^'"]+)['"]
  ```
- Capture group 1 = import path
- Skip type-only imports for TypeScript (`import type`)

**Other Languages** (Tier 3 - Best Effort):
- Generic regex patterns for common import syntax:
  - Go: `import\s+"([^"]+)"`
  - Java: `import\s+([\w.]+);`
  - Ruby: `require\s+['"]([^'"]+)['"]`
  - Rust: `use\s+([\w:]+);`
- These are "nice to have" for demo purposes
- Accuracy ~60-70%, but better than nothing

### Rationale
- Python is mission-critical (backend code) → needs 100% accuracy
- JS/TS regex is proven acceptable in AGENTS.md (85% precision)
- Other languages are stretch goals; regex is fast to implement
- All parsers return a uniform `Import` model for downstream processing

---

## DECISION 2: Import Path Resolution

### Recommendation: **Strategy B** (Ground Truth Fuzzy Matching)

**Algorithm**:
1. Build a lookup table from all changed file paths:
   ```python
   # Input: ["backend/models/user.py", "backend/services/auth.py"]
   # Output: {
   #   "models.user": "backend/models/user.py",
   #   "models/user": "backend/models/user.py",
   #   "user": "backend/models/user.py",
   #   "services.auth": "backend/services/auth.py",
   #   ...
   # }
   ```
2. For each import path (e.g., `from models.user import User`):
   - Normalize: `models.user` → `models/user`
   - Try exact match in lookup table
   - Try suffix match (e.g., `models/user` matches `backend/models/user.py`)
   - Try stem match (e.g., `user` matches `backend/models/user.py`)
3. If multiple matches, prefer shortest path (most specific)
4. If no match, skip edge (import is external or not in changed set)

**Why Strategy B over Strategy A**:
- **Robustness**: Works for arbitrary project layouts (monorepos, nested structures, non-standard paths)
- **Accuracy**: Uses actual file paths as ground truth, not assumptions
- **Simplicity**: No need to guess project structure conventions
- **Performance**: O(1) lookup after O(n) preprocessing

**Edge cases handled**:
- `__init__.py` files: map `models` → `models/__init__.py`
- Index files: map `components` → `components/index.ts`
- Relative imports: resolve against the importing file's directory
- Aliased imports: extract the actual module path, ignore the alias

---

## DECISION 3: Edge Filtering

### Recommendation: Uniform edge weights with self-import filtering

**Rules**:
1. **Only intra-PR edges**: Create edge A→B only if both A and B are in the changed file set
2. **Uniform weight**: All edges have weight 1.0 (simplifies community detection)
3. **Skip self-imports**: If file A imports itself (rare but possible in Python `__init__.py`), skip the edge
4. **Bidirectional imports**: If A imports B and B imports A (circular dependency), create both edges A→B and B→A

**Rationale for uniform weights**:
- Community detection algorithms (modularity-based) work well with unweighted graphs
- Differentiating "direct" vs "indirect" imports is ambiguous (what's indirect?)
- Simplifies graph serialization for frontend
- Can add weights in v2 if needed (e.g., based on import frequency in patch)

**Why skip self-imports**:
- They don't represent inter-file dependencies
- They create self-loops that confuse some graph algorithms
- Example: `backend/models/__init__.py` importing `from . import user` is not a dependency

---

## DECISION 4: Community Detection Algorithm

### Recommendation: **`greedy_modularity_communities`**

**Comparison**:

| Algorithm | Time Complexity | Quality | Deterministic | Verdict |
|-----------|----------------|---------|---------------|---------|
| `greedy_modularity_communities` | O(n log n) | Good | Yes | ✅ **Best for MVP** |
| `louvain_communities` | O(n log n) | Better | No (random) | ❌ Non-deterministic |
| `label_propagation_communities` | O(n) | Noisy | No (random) | ❌ Too unstable |

**Why greedy_modularity**:
- **Deterministic**: Same input → same clusters (critical for stable sub-PR IDs)
- **Fast enough**: For 30-200 files, runs in <100ms
- **Good quality**: Maximizes modularity (intra-cluster density vs inter-cluster sparsity)
- **Proven**: Used in production graph analysis tools

**Fallback for disconnected graphs**:
- If the graph has multiple connected components, run community detection on each component separately
- Treat each component as a separate cluster if it's small (<5 files)

---

## DECISION 5: Cluster Post-Processing

### Recommendation: Multi-stage refinement pipeline

**Stage 1: Merge tiny clusters**
- If cluster has 1-2 files, merge with the cluster it has the most edges to
- If isolated (no edges), create a standalone cluster labeled "Isolated Changes"

**Stage 2: Split mega-clusters**
- If cluster has >30 files, recursively apply community detection within the cluster
- Stop when all sub-clusters are ≤30 files or no further splits improve modularity

**Stage 3: Layer detection**
- Assign each cluster an architectural layer based on file path heuristics:
  ```python
  LAYER_PATTERNS = {
      "schema": r"(migrations?|schema|db|database|models?/.*\.sql)",
      "backend": r"(api|services?|controllers?|routes?|handlers?)",
      "frontend": r"(components?|pages?|views?|ui|frontend|client)",
      "tests": r"(tests?|__tests__|spec|\.test\.|\.spec\.)",
      "config": r"(config|settings?|\.env|\.yml|\.json|\.toml)",
      "docs": r"(docs?|README|\.md$)",
  }
  ```
- A cluster's layer = majority layer of its files
- If no majority, label as "mixed"

**Stage 4: Topological ordering**
- Sort clusters by layer priority: `schema → backend → frontend → tests → config → docs → mixed`
- Within each layer, sort by cluster size (smaller first, easier to review)

**Rationale**:
- Tiny clusters are noise; merging reduces cognitive load
- Mega-clusters are unmanageable; splitting maintains reviewability
- Layer detection enables intelligent sub-PR ordering (DB changes before API changes)
- Topological ordering respects real-world dependency flow

---

## DECISION 6: Output Structure

### Pydantic Models

```python
# backend/models/dependency.py

from pydantic import BaseModel, Field
from typing import Literal

class Import(BaseModel):
    """
    Represents a single import statement extracted from source code.
    """
    module_path: str  # e.g., "models.user" or "./utils"
    imported_names: list[str] = Field(default_factory=list)  # e.g., ["User", "Role"]
    is_relative: bool = False
    line_number: int | None = None

class DependencyEdge(BaseModel):
    """
    Represents a directed edge in the dependency graph.
    """
    source: str  # filename of importing file
    target: str  # filename of imported file
    weight: float = 1.0

class GraphNode(BaseModel):
    """
    Represents a node in the dependency graph (a changed file).
    Serializable for frontend React Flow.
    """
    id: str  # filename (unique)
    label: str  # display name (basename)
    language: str | None
    additions: int
    deletions: int
    layer: Literal["schema", "backend", "frontend", "tests", "config", "docs", "mixed"] | None

class DependencyGraph(BaseModel):
    """
    Complete dependency graph with nodes and edges.
    """
    nodes: list[GraphNode]
    edges: list[DependencyEdge]
    
    def to_react_flow(self) -> dict:
        """Convert to React Flow format for frontend visualization."""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "data": {"label": node.label, "language": node.language},
                    "position": {"x": 0, "y": 0},  # Frontend will layout
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

class FileCluster(BaseModel):
    """
    Represents a cluster of tightly-coupled files.
    """
    cluster_id: str  # deterministic hash of sorted file list
    files: list[str]  # filenames in this cluster
    layer: Literal["schema", "backend", "frontend", "tests", "config", "docs", "mixed"]
    total_additions: int
    total_deletions: int
    internal_edges: int  # edges within cluster
    external_edges: int  # edges to other clusters
    
    @property
    def cohesion(self) -> float:
        """Ratio of internal to total edges (0-1, higher = more cohesive)."""
        total = self.internal_edges + self.external_edges
        return self.internal_edges / total if total > 0 else 0.0

class AnalysisResult(BaseModel):
    """
    Complete output of dependency analysis.
    """
    graph: DependencyGraph
    clusters: list[FileCluster]
    total_files: int
    total_edges: int
    isolated_files: list[str]  # files with no dependencies
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "graph": {"nodes": [], "edges": []},
                "clusters": [],
                "total_files": 42,
                "total_edges": 67,
                "isolated_files": ["README.md", "config.yml"],
            }
        }
    }
```

---

## Class Structure

```python
# backend/services/dependency_analyzer.py

from typing import Protocol
import networkx as nx
from loguru import logger

class Parser(Protocol):
    """Protocol for language-specific parsers."""
    def parse(self, source: str, filename: str) -> list[Import]:
        """Extract imports from source code."""
        ...

class DependencyAnalyzer:
    """
    Analyzes file dependencies and detects clusters in a Pull Request.
    
    Main entry point: analyze(files) -> AnalysisResult
    """
    
    # Registry of language parsers
    PARSERS: dict[str, Parser] = {}
    
    def __init__(self) -> None:
        self._register_parsers()
    
    def analyze(self, files: list[FileChange]) -> AnalysisResult:
        """
        Main public method: analyze dependencies and detect clusters.
        
        Args:
            files: List of changed files from a PR
            
        Returns:
            Complete analysis with graph and clusters
        """
        # Implementation in pseudocode section below
        ...
    
    # Private helper methods
    def _register_parsers(self) -> None:
        """Register all available language parsers."""
        from services.parsers.python_parser import PythonParser
        from services.parsers.javascript_parser import JavaScriptParser
        # ... other parsers
        
        self.PARSERS["python"] = PythonParser()
        self.PARSERS["javascript"] = JavaScriptParser()
        self.PARSERS["typescript"] = JavaScriptParser()  # Same parser
    
    def _build_file_lookup(self, files: list[FileChange]) -> dict[str, str]:
        """Build lookup table for import path resolution."""
        ...
    
    def _extract_imports(self, file: FileChange) -> list[Import]:
        """Extract imports from a single file using appropriate parser."""
        ...
    
    def _resolve_import_path(
        self, 
        import_path: str, 
        importing_file: str,
        lookup: dict[str, str]
    ) -> str | None:
        """Resolve import path to actual filename in changed set."""
        ...
    
    def _build_graph(
        self, 
        files: list[FileChange],
        lookup: dict[str, str]
    ) -> nx.DiGraph:
        """Build networkx directed graph from files and imports."""
        ...
    
    def _detect_clusters(self, graph: nx.DiGraph) -> list[set[str]]:
        """Detect communities using greedy modularity."""
        ...
    
    def _post_process_clusters(
        self,
        clusters: list[set[str]],
        graph: nx.DiGraph,
        files: list[FileChange]
    ) -> list[FileCluster]:
        """Merge tiny, split mega, detect layers, sort topologically."""
        ...
    
    def _detect_layer(self, files: list[str]) -> str:
        """Detect architectural layer from file paths."""
        ...
    
    def _graph_to_model(
        self,
        graph: nx.DiGraph,
        files: list[FileChange]
    ) -> DependencyGraph:
        """Convert networkx graph to Pydantic model."""
        ...
```

### Parser Structure

```python
# backend/services/parsers/python_parser.py

import ast
from models.dependency import Import

class PythonParser:
    """AST-based parser for Python imports."""
    
    def parse(self, source: str, filename: str) -> list[Import]:
        """
        Extract imports from Python source code.
        
        Args:
            source: Python source code as string
            filename: Path to the file (for relative import resolution)
            
        Returns:
            List of Import objects
        """
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Failed to parse {filename}: {e}")
            return []
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(Import(
                        module_path=alias.name,
                        imported_names=[alias.asname or alias.name],
                        is_relative=False,
                        line_number=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # from X import Y
                    imports.append(Import(
                        module_path=node.module,
                        imported_names=[a.name for a in node.names],
                        is_relative=node.level > 0,
                        line_number=node.lineno,
                    ))
        
        return imports
```

```python
# backend/services/parsers/javascript_parser.py

import re
from models.dependency import Import

class JavaScriptParser:
    """Regex-based parser for JavaScript/TypeScript imports."""
    
    # Compiled regex patterns
    ES6_IMPORT = re.compile(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]')
    ES6_IMPORT_BARE = re.compile(r'import\s+[\'"]([^\'"]+)[\'"]')
    REQUIRE = re.compile(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')
    DYNAMIC_IMPORT = re.compile(r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')
    EXPORT_FROM = re.compile(r'export\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]')
    
    def parse(self, source: str, filename: str) -> list[Import]:
        """
        Extract imports from JavaScript/TypeScript source code.
        
        Args:
            source: JS/TS source code as string
            filename: Path to the file
            
        Returns:
            List of Import objects
        """
        imports = []
        
        for pattern in [self.ES6_IMPORT, self.ES6_IMPORT_BARE, 
                       self.REQUIRE, self.DYNAMIC_IMPORT, self.EXPORT_FROM]:
            for match in pattern.finditer(source):
                module_path = match.group(1)
                imports.append(Import(
                    module_path=module_path,
                    imported_names=[],  # Don't parse individual names for MVP
                    is_relative=module_path.startswith('.'),
                    line_number=source[:match.start()].count('\n') + 1,
                ))
        
        return imports
```

---

## Pseudocode: Main `analyze()` Method

```python
def analyze(self, files: list[FileChange]) -> AnalysisResult:
    """
    Analyze dependencies and detect clusters.
    
    Algorithm:
    1. Build file lookup table for import resolution
    2. Extract imports from each file using language-specific parser
    3. Build directed graph with files as nodes, imports as edges
    4. Detect communities using greedy modularity
    5. Post-process clusters (merge/split/layer/sort)
    6. Convert to Pydantic models
    """
    
    logger.info(f"Analyzing {len(files)} changed files")
    
    # Step 1: Build lookup table
    lookup = self._build_file_lookup(files)
    logger.debug(f"Built lookup table with {len(lookup)} entries")
    
    # Step 2: Build graph
    graph = self._build_graph(files, lookup)
    logger.info(f"Built graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Step 3: Detect clusters
    raw_clusters = self._detect_clusters(graph)
    logger.info(f"Detected {len(raw_clusters)} raw clusters")
    
    # Step 4: Post-process
    clusters = self._post_process_clusters(raw_clusters, graph, files)
    logger.info(f"Post-processed to {len(clusters)} final clusters")
    
    # Step 5: Identify isolated files
    isolated = [
        f.filename for f in files 
        if graph.degree(f.filename) == 0
    ]
    
    # Step 6: Convert to models
    graph_model = self._graph_to_model(graph, files)
    
    return AnalysisResult(
        graph=graph_model,
        clusters=clusters,
        total_files=len(files),
        total_edges=graph.number_of_edges(),
        isolated_files=isolated,
    )


def _build_graph(self, files: list[FileChange], lookup: dict[str, str]) -> nx.DiGraph:
    """
    Build directed graph from files and imports.
    
    Algorithm:
    1. Create node for each file
    2. For each file, extract imports
    3. For each import, resolve to target file
    4. If target in changed set, create edge
    5. Skip self-imports
    """
    
    graph = nx.DiGraph()
    
    # Add all files as nodes
    for file in files:
        graph.add_node(
            file.filename,
            language=file.language,
            additions=file.additions,
            deletions=file.deletions,
        )
    
    # Add edges from imports
    for file in files:
        imports = self._extract_imports(file)
        
        for imp in imports:
            target = self._resolve_import_path(
                imp.module_path,
                file.filename,
                lookup
            )
            
            if target and target != file.filename:  # Skip self-imports
                graph.add_edge(file.filename, target, weight=1.0)
    
    return graph


def _detect_clusters(self, graph: nx.DiGraph) -> list[set[str]]:
    """
    Detect communities using greedy modularity.
    
    Algorithm:
    1. Convert to undirected graph (community detection needs undirected)
    2. Handle disconnected components
    3. Run greedy_modularity_communities on each component
    4. Return list of clusters (sets of filenames)
    """
    
    # Convert to undirected
    undirected = graph.to_undirected()
    
    # Get connected components
    components = list(nx.connected_components(undirected))
    
    clusters = []
    for component in components:
        subgraph = undirected.subgraph(component)
        
        if len(component) <= 2:
            # Too small for community detection
            clusters.append(component)
        else:
            # Run community detection
            communities = nx.community.greedy_modularity_communities(subgraph)
            clusters.extend(communities)
    
    return clusters


def _post_process_clusters(
    self,
    clusters: list[set[str]],
    graph: nx.DiGraph,
    files: list[FileChange]
) -> list[FileCluster]:
    """
    Post-process clusters: merge tiny, split mega, detect layers, sort.
    
    Algorithm:
    1. Merge clusters with 1-2 files into neighbors
    2. Split clusters with >30 files recursively
    3. Detect layer for each cluster
    4. Sort by layer priority, then size
    5. Convert to FileCluster models
    """
    
    # Stage 1: Merge tiny clusters
    processed = []
    for cluster in clusters:
        if len(cluster) <= 2:
            # Find neighbor with most edges
            neighbors = {}
            for file in cluster:
                for neighbor in graph.neighbors(file):
                    for other_cluster in clusters:
                        if neighbor in other_cluster and other_cluster != cluster:
                            neighbors[id(other_cluster)] = neighbors.get(id(other_cluster), 0) + 1
            
            if neighbors:
                # Merge with most-connected neighbor
                best_neighbor_id = max(neighbors, key=neighbors.get)
                best_neighbor = next(c for c in clusters if id(c) == best_neighbor_id)
                best_neighbor.update(cluster)
            else:
                # Isolated, keep as-is
                processed.append(cluster)
        else:
            processed.append(cluster)
    
    # Stage 2: Split mega clusters (recursive)
    final = []
    for cluster in processed:
        if len(cluster) > 30:
            subgraph = graph.subgraph(cluster).to_undirected()
            sub_communities = nx.community.greedy_modularity_communities(subgraph)
            final.extend(sub_communities)
        else:
            final.append(cluster)
    
    # Stage 3: Detect layers and convert to models
    file_map = {f.filename: f for f in files}
    cluster_models = []
    
    for cluster in final:
        files_in_cluster = [file_map[f] for f in cluster]
        layer = self._detect_layer(list(cluster))
        
        # Count edges
        internal = sum(
            1 for u, v in graph.edges()
            if u in cluster and v in cluster
        )
        external = sum(
            1 for u, v in graph.edges()
            if (u in cluster and v not in cluster) or (u not in cluster and v in cluster)
        )
        
        cluster_models.append(FileCluster(
            cluster_id=hashlib.sha256(
                "".join(sorted(cluster)).encode()
            ).hexdigest()[:12],
            files=sorted(cluster),
            layer=layer,
            total_additions=sum(f.additions for f in files_in_cluster),
            total_deletions=sum(f.deletions for f in files_in_cluster),
            internal_edges=internal,
            external_edges=external,
        ))
    
    # Stage 4: Sort by layer priority, then size
    LAYER_PRIORITY = {
        "schema": 0, "backend": 1, "frontend": 2,
        "tests": 3, "config": 4, "docs": 5, "mixed": 6
    }
    
    cluster_models.sort(
        key=lambda c: (LAYER_PRIORITY.get(c.layer, 99), len(c.files))
    )
    
    return cluster_models
```

---

## Testing Strategy

### Unit Tests

1. **Parser tests** (`backend/tests/test_parsers.py`):
   - Python: simple imports, relative imports, `__init__.py`, syntax errors
   - JavaScript: ES6, CommonJS, dynamic imports, TypeScript type imports
   - Edge cases: circular imports, self-imports, missing files

2. **Resolution tests** (`backend/tests/test_resolution.py`):
   - Exact matches, suffix matches, stem matches
   - Relative imports (`.`, `..`)
   - `__init__.py` and `index.ts` handling
   - Ambiguous matches (prefer shortest path)

3. **Graph tests** (`backend/tests/test_graph.py`):
   - Node creation, edge creation, self-import filtering
   - Disconnected components, isolated files
   - Circular dependencies

4. **Clustering tests** (`backend/tests/test_clustering.py`):
   - Small graphs (2-5 files), medium (10-30), large (50-100)
   - Merge tiny clusters, split mega clusters
   - Layer detection accuracy

### Integration Tests

1. **End-to-end** (`backend/tests/test_analyzer_e2e.py`):
   - Real PR data from demo_data/
   - Verify graph structure, cluster count, layer distribution
   - Performance: <1s for 100 files, <5s for 300 files

### Fixtures

```
backend/tests/fixtures/
├── python/
│   ├── simple_import.py
│   ├── relative_import.py
│   └── circular_a.py, circular_b.py
├── javascript/
│   ├── es6_import.js
│   ├── commonjs.js
│   └── dynamic_import.ts
└── sample_prs/
    ├── small_pr.json (10 files)
    ├── medium_pr.json (50 files)
    └── large_pr.json (200 files)
```

---

## Performance Targets

| PR Size | Files | Expected Time | Memory |
|---------|-------|---------------|--------|
| Small | 10-30 | <200ms | <50MB |
| Medium | 30-100 | <1s | <100MB |
| Large | 100-300 | <5s | <200MB |
| Monster | 300-500 | <15s | <500MB |

**Bottlenecks**:
- AST parsing: O(n × file_size), but Python `ast` is fast (~1ms per file)
- Graph construction: O(n × imports_per_file), typically O(n²) worst case
- Community detection: O(n log n) with greedy modularity
- Post-processing: O(n × clusters), typically O(n)

**Optimizations for v2**:
- Cache parsed imports per file (keyed by file hash)
- Parallelize parsing with `multiprocessing`
- Use `louvain_communities` with fixed seed for better quality
- Implement incremental graph updates for PR updates

---

## Open Questions for Review

1. **Should we support monorepo-specific import resolution?** (e.g., Nx, Turborepo aliases)
   - Proposal: Add optional `import_aliases` parameter to `analyze()` for custom path mappings
   
2. **How to handle binary files?** (images, PDFs, etc.)
   - Proposal: Skip parsing, add as isolated nodes with layer="assets"
   
3. **Should clusters have a "risk score"?** (based on cohesion, size, layer)
   - Proposal: Add in `FileCluster` model, compute as `1 - cohesion + log(size) / 10`
   
4. **Frontend graph layout algorithm?**
   - Proposal: Use `dagre` for hierarchical layout (layer-based), fallback to `force-directed`

---

## Next Steps

1. ✅ Review and approve this architecture
2. Switch to Code mode
3. Implement `backend/models/dependency.py` (Pydantic models)
4. Implement `backend/services/parsers/python_parser.py`
5. Implement `backend/services/parsers/javascript_parser.py`
6. Implement `backend/services/dependency_analyzer.py` (main service)
7. Write unit tests for each component
8. Write integration test with sample PR data
9. Document in `AGENTS.md` under "Common Tasks"

---

**Made with Bob** 🤖