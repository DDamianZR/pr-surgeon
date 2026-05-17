"""
Dependency analyzer service.
Analyzes file dependencies and detects clusters in a Pull Request.
"""

import re
from pathlib import Path
from typing import Literal, Protocol

import networkx as nx
from loguru import logger

from models.analysis import (
    AnalysisResult,
    DependencyEdge,
    DependencyGraph,
    FileCluster,
    GraphNode,
    Import,
)
from models.pr import FileChange


class Parser(Protocol):
    """Protocol for language-specific parsers."""
    
    def extract_imports(self, source: str, file_path: str) -> list[Import]:
        """Extract imports from source code."""
        ...


class DependencyAnalyzer:
    """
    Analyzes file dependencies and detects clusters in a Pull Request.
    
    Main entry point: analyze(files) -> AnalysisResult
    """
    
    # Layer detection patterns (order matters - more specific patterns first)
    LAYER_PATTERNS = {
        "docs": re.compile(r"(^docs/|README|\.md$)", re.IGNORECASE),
        "tests": re.compile(r"(tests?|__tests__|spec|\.test\.|\.spec\.)", re.IGNORECASE),
        "schema": re.compile(r"(migrations?|schema|db|database|models?/.*\.sql)", re.IGNORECASE),
        "config": re.compile(r"(config|settings?|\.env|\.ya?ml|\.json|\.toml)", re.IGNORECASE),
        "backend": re.compile(r"(backend|api|services?|controllers?|routes?|handlers?)", re.IGNORECASE),
        "frontend": re.compile(r"(frontend|components?|pages?|views?|ui|client)", re.IGNORECASE),
    }
    
    # Layer priority for topological ordering
    LAYER_PRIORITY = {
        "schema": 0,
        "backend": 1,
        "frontend": 2,
        "tests": 3,
        "config": 4,
        "docs": 5,
        "mixed": 6,
    }
    
    def __init__(self) -> None:
        """Initialize the analyzer and register parsers."""
        self.parsers: dict[str, Parser] = {}
        self._register_parsers()
    
    def _register_parsers(self) -> None:
        """Register all available language parsers."""
        from services.parsers.python_parser import PythonParser
        from services.parsers.js_parser import JSParser
        from services.parsers.generic_parser import GenericParser
        
        self.parsers["python"] = PythonParser()
        self.parsers["javascript"] = JSParser()
        self.parsers["typescript"] = JSParser()  # Same parser for TS
        
        # Generic fallback for other languages
        self.parsers["go"] = GenericParser("go")
        self.parsers["java"] = GenericParser("java")
        self.parsers["ruby"] = GenericParser("ruby")
        self.parsers["rust"] = GenericParser("rust")
        self.parsers["c"] = GenericParser("c")
        self.parsers["cpp"] = GenericParser("cpp")
        self.parsers["php"] = GenericParser("php")
        
        logger.info(f"Registered {len(self.parsers)} language parsers")
    
    def analyze(self, files: list[FileChange]) -> AnalysisResult:
        """
        Main public method: analyze dependencies and detect clusters.
        
        Args:
            files: List of changed files from a PR
            
        Returns:
            Complete analysis with graph and clusters
        """
        logger.info(f"Starting analysis of {len(files)} changed files")
        
        # Step 1: Build file lookup table for import resolution
        lookup = self._build_file_lookup(files)
        logger.debug(f"Built lookup table with {len(lookup)} entries")
        
        # Step 2: Build dependency graph
        graph = self._build_graph(files, lookup)
        logger.info(
            f"Built graph: {graph.number_of_nodes()} nodes, "
            f"{graph.number_of_edges()} edges"
        )
        
        # Step 3: Detect clusters using community detection
        raw_clusters = self._detect_clusters(graph)
        logger.info(f"Detected {len(raw_clusters)} raw clusters")
        
        # Step 4: Post-process clusters
        clusters = self._post_process_clusters(raw_clusters, graph, files)
        logger.info(f"Post-processed to {len(clusters)} final clusters")
        
        # Step 5: Identify isolated files (no dependencies)
        isolated = [
            f.filename for f in files
            if graph.degree(f.filename) == 0
        ]
        logger.debug(f"Found {len(isolated)} isolated files")
        
        # Step 6: Convert to Pydantic models
        graph_model = self._graph_to_model(graph, files)
        
        result = AnalysisResult(
            graph=graph_model,
            clusters=clusters,
            total_files=len(files),
            total_edges=graph.number_of_edges(),
            isolated_files=isolated,
        )
        
        logger.info("Analysis complete")
        return result
    
    def _build_file_lookup(self, files: list[FileChange]) -> dict[str, str]:
        """
        Build lookup table for import path resolution.
        
        Creates multiple lookup keys for each file:
        - Full path: "backend/models/user.py"
        - Module path: "backend.models.user"
        - Relative path: "models/user"
        - Stem: "user"
        
        Args:
            files: List of changed files
            
        Returns:
            Dictionary mapping various path formats to actual filenames
        """
        lookup: dict[str, str] = {}
        
        for file in files:
            filename = file.filename
            path = Path(filename)
            
            # Add full path
            lookup[filename] = filename
            
            # Add module-style path (with dots)
            module_path = str(path.with_suffix('')).replace('\\', '/').replace('/', '.')
            lookup[module_path] = filename
            
            # Add path without extension
            path_no_ext = str(path.with_suffix('')).replace('\\', '/')
            lookup[path_no_ext] = filename
            
            # Add just the stem (filename without extension)
            lookup[path.stem] = filename
            
            # For __init__.py or index.js, also map the directory
            if path.name in ('__init__.py', 'index.js', 'index.ts', 'index.tsx'):
                dir_path = str(path.parent).replace('\\', '/')
                lookup[dir_path] = filename
                lookup[dir_path.replace('/', '.')] = filename
        
        return lookup
    
    def _extract_imports(self, file: FileChange) -> list[Import]:
        """
        Extract imports from a single file using appropriate parser.
        
        Args:
            file: FileChange object with source code
            
        Returns:
            List of Import objects
        """
        if not file.patch or not file.language:
            return []
        
        # Get parser for this language
        parser = self.parsers.get(file.language)
        if not parser:
            logger.debug(f"No parser for language: {file.language}")
            return []
        
        # Extract imports
        try:
            imports = parser.extract_imports(file.patch, file.filename)
            return imports
        except Exception as e:
            logger.warning(f"Failed to extract imports from {file.filename}: {e}")
            return []
    
    def _resolve_import_path(
        self,
        import_path: str,
        importing_file: str,
        is_relative: bool,
        lookup: dict[str, str]
    ) -> str | None:
        """
        Resolve import path to actual filename in changed set.
        
        Uses Strategy B (Ground Truth Fuzzy Matching):
        1. Try exact match
        2. Try suffix match
        3. Try stem match
        4. Handle relative imports
        
        Args:
            import_path: The module path from the import statement
            importing_file: Path to the file doing the importing
            is_relative: Whether this is a relative import
            lookup: File lookup table
            
        Returns:
            Resolved filename or None if not found
        """
        # Handle relative imports
        if is_relative:
            # Resolve relative path
            file_dir = Path(importing_file).parent
            
            # Count leading dots
            level = 0
            for char in import_path:
                if char == '.':
                    level += 1
                else:
                    break
            
            # Go up directories
            target_dir = file_dir
            for _ in range(level - 1):
                target_dir = target_dir.parent
            
            # Get remaining path
            remaining = import_path[level:]
            if remaining:
                resolved = target_dir / remaining.replace('.', '/')
            else:
                resolved = target_dir
            
            import_path = str(resolved).replace('\\', '/')
        
        # Try exact match
        if import_path in lookup:
            return lookup[import_path]
        
        # Try with common extensions
        for ext in ['.py', '.js', '.ts', '.tsx', '.jsx']:
            if import_path + ext in lookup:
                return lookup[import_path + ext]
        
        # Try suffix match (find files ending with this path)
        normalized = import_path.replace('.', '/').replace('\\', '/')
        for key, filename in lookup.items():
            if key.endswith(normalized) or key.endswith(normalized + '.py'):
                return filename
        
        # Try stem match (just the filename)
        stem = Path(import_path).stem
        if stem in lookup:
            return lookup[stem]
        
        return None
    
    def _build_graph(
        self,
        files: list[FileChange],
        lookup: dict[str, str]
    ) -> nx.DiGraph:
        """
        Build directed graph from files and imports.
        
        Args:
            files: List of changed files
            lookup: File lookup table for import resolution
            
        Returns:
            NetworkX directed graph
        """
        graph = nx.DiGraph()
        
        # Add all files as nodes with attributes
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
                    imp.is_relative,
                    lookup
                )
                
                # Only create edge if target exists and is not self
                if target and target != file.filename and target in graph:
                    graph.add_edge(file.filename, target, weight=1.0)
                    logger.debug(f"Added edge: {file.filename} -> {target}")
        
        return graph
    
    def _detect_clusters(self, graph: nx.DiGraph) -> list[set[str]]:
        """
        Detect communities using greedy modularity.
        
        Args:
            graph: NetworkX directed graph
            
        Returns:
            List of clusters (sets of filenames)
        """
        # Convert to undirected for community detection
        undirected = graph.to_undirected()
        
        # Get connected components
        components = list(nx.connected_components(undirected))
        
        clusters = []
        for component in components:
            if len(component) <= 2:
                # Too small for community detection, keep as-is
                clusters.append(component)
            else:
                # Run community detection on this component
                subgraph = undirected.subgraph(component)
                try:
                    communities = nx.community.greedy_modularity_communities(subgraph)
                    clusters.extend(communities)
                except Exception as e:
                    logger.warning(f"Community detection failed: {e}, using component as cluster")
                    clusters.append(component)
        
        return clusters
    
    def _post_process_clusters(
        self,
        clusters: list[set[str]],
        graph: nx.DiGraph,
        files: list[FileChange]
    ) -> list[FileCluster]:
        """
        Post-process clusters: merge tiny, split mega, detect layers, sort.
        
        Args:
            clusters: Raw clusters from community detection
            graph: Dependency graph
            files: List of changed files
            
        Returns:
            List of FileCluster models
        """
        # Create file map for quick lookup
        file_map = {f.filename: f for f in files}
        
        # Stage 1: Merge tiny clusters (1-2 files)
        processed = []
        tiny_clusters = []
        
        for cluster in clusters:
            if len(cluster) <= 2:
                tiny_clusters.append(cluster)
            else:
                processed.append(cluster)
        
        # Merge tiny clusters with their most-connected neighbor
        for tiny in tiny_clusters:
            best_neighbor = None
            max_edges = 0
            
            for file in tiny:
                for neighbor in list(graph.predecessors(file)) + list(graph.successors(file)):
                    for other_cluster in processed:
                        if neighbor in other_cluster:
                            edges = sum(
                                1 for f in tiny
                                for n in list(graph.predecessors(f)) + list(graph.successors(f))
                                if n in other_cluster
                            )
                            if edges > max_edges:
                                max_edges = edges
                                best_neighbor = other_cluster
            
            if best_neighbor is not None:
                best_neighbor.update(tiny)
            else:
                # Isolated, keep as-is
                processed.append(tiny)
        
        # Stage 2: Split mega clusters (>30 files)
        final = []
        for cluster in processed:
            if len(cluster) > 30:
                subgraph = graph.subgraph(cluster).to_undirected()
                try:
                    sub_communities = nx.community.greedy_modularity_communities(subgraph)
                    final.extend(sub_communities)
                except Exception:
                    final.append(cluster)
            else:
                final.append(cluster)
        
        # Stage 3: Convert to FileCluster models with layer detection
        cluster_models = []
        
        for cluster in final:
            files_in_cluster = [file_map[f] for f in cluster if f in file_map]
            layer = self._detect_layer(list(cluster))
            
            # Count internal and external edges
            internal = sum(
                1 for u, v in graph.edges()
                if u in cluster and v in cluster
            )
            external = sum(
                1 for u, v in graph.edges()
                if (u in cluster and v not in cluster) or (u not in cluster and v in cluster)
            )
            
            cluster_models.append(FileCluster(
                cluster_id=FileCluster.generate_id(sorted(cluster)),
                files=sorted(cluster),
                layer=layer,
                total_additions=sum(f.additions for f in files_in_cluster),
                total_deletions=sum(f.deletions for f in files_in_cluster),
                internal_edges=internal,
                external_edges=external,
            ))
        
        # Stage 4: Sort by layer priority, then size
        cluster_models.sort(
            key=lambda c: (self.LAYER_PRIORITY.get(c.layer, 99), len(c.files))
        )
        
        return cluster_models
    
    def _detect_layer(self, files: list[str]) -> Literal["schema", "backend", "frontend", "tests", "config", "docs", "mixed"]:
        """
        Detect architectural layer from file paths.
        
        Args:
            files: List of filenames
            
        Returns:
            Layer name (schema, backend, frontend, tests, config, docs, or mixed)
        """
        layer_counts: dict[str, int] = {}
        
        for file in files:
            for layer, pattern in self.LAYER_PATTERNS.items():
                if pattern.search(file):
                    layer_counts[layer] = layer_counts.get(layer, 0) + 1
                    break
        
        if not layer_counts:
            return "mixed"
        
        # Return layer with most files
        max_layer = max(layer_counts, key=layer_counts.get)  # type: ignore
        
        # If no clear majority (less than 50%), mark as mixed
        if layer_counts[max_layer] < len(files) * 0.5:
            return "mixed"
        
        # Cast to Literal type
        return max_layer  # type: ignore
    
    def _graph_to_model(
        self,
        graph: nx.DiGraph,
        files: list[FileChange]
    ) -> DependencyGraph:
        """
        Convert NetworkX graph to Pydantic model.
        
        Args:
            graph: NetworkX directed graph
            files: List of changed files
            
        Returns:
            DependencyGraph model
        """
        # Create file map
        file_map = {f.filename: f for f in files}
        
        # Build nodes
        nodes = []
        for node_id in graph.nodes():
            file = file_map.get(node_id)
            if file:
                # Detect layer for this individual file
                layer = self._detect_layer([node_id])
                
                nodes.append(GraphNode(
                    id=node_id,
                    label=Path(node_id).name,
                    language=file.language,
                    additions=file.additions,
                    deletions=file.deletions,
                    layer=layer,
                ))
        
        # Build edges
        edges = [
            DependencyEdge(source=u, target=v, weight=data.get('weight', 1.0))
            for u, v, data in graph.edges(data=True)
        ]
        
        return DependencyGraph(nodes=nodes, edges=edges)


# Made with Bob