"""
Comprehensive tests for the dependency analyzer.
Tests parsers, graph building, clustering, and full pipeline.
"""

import pytest

from models.analysis import Import
from models.pr import FileChange
from services.dependency_analyzer import DependencyAnalyzer
from services.parsers.python_parser import PythonParser
from services.parsers.js_parser import JSParser


class TestPythonParser:
    """Test Python import extraction."""
    
    def test_simple_import(self):
        """Test simple import statement."""
        parser = PythonParser()
        source = "import os\nimport sys"
        
        imports = parser.extract_imports(source, "test.py")
        
        assert len(imports) == 2
        assert imports[0].module_path == "os"
        assert imports[1].module_path == "sys"
        assert not imports[0].is_relative
    
    def test_from_import(self):
        """Test from...import statement."""
        parser = PythonParser()
        source = "from models.user import User, Role"
        
        imports = parser.extract_imports(source, "test.py")
        
        assert len(imports) == 1
        assert imports[0].module_path == "models.user"
        assert "User" in imports[0].imported_names
        assert "Role" in imports[0].imported_names
        assert not imports[0].is_relative
    
    def test_relative_import(self):
        """Test relative import statement."""
        parser = PythonParser()
        source = "from .models import User\nfrom ..utils import helper"
        
        imports = parser.extract_imports(source, "backend/services/auth.py")
        
        assert len(imports) == 2
        assert imports[0].module_path == ".models"
        assert imports[0].is_relative
        assert imports[1].module_path == "..utils"
        assert imports[1].is_relative
    
    def test_import_as(self):
        """Test import with alias."""
        parser = PythonParser()
        source = "import numpy as np\nfrom models import User as U"
        
        imports = parser.extract_imports(source, "test.py")
        
        assert len(imports) == 2
        assert imports[0].module_path == "numpy"
        assert imports[1].module_path == "models"
    
    def test_syntax_error(self):
        """Test handling of syntax errors with regex fallback."""
        parser = PythonParser()
        source = "import os\nthis is not valid python"
        
        imports = parser.extract_imports(source, "test.py")
        
        # Should use regex fallback and still extract the valid import
        assert len(imports) >= 1
        assert imports[0].module_path == "os"
    
    def test_real_world_python_with_modern_syntax(self):
        """Verify parser handles code with shebangs, encoding, future imports."""
        parser = PythonParser()
        source = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any
from django.http import HttpRequest
import asyncio

class AsyncHandler:
    async def __call__(self, request: HttpRequest) -> Any:
        return await self.process(request)
'''
        imports = parser.extract_imports(source, "test.py")
        assert len(imports) >= 3, f"Expected 3+ imports, got {len(imports)}: {[i.module_path for i in imports]}"
        
        # Verify specific imports were found
        module_paths = [imp.module_path for imp in imports]
        assert "__future__" in module_paths
        assert "typing" in module_paths
        assert "django.http" in module_paths or "asyncio" in module_paths


class TestJSParser:
    """Test JavaScript/TypeScript import extraction."""
    
    def test_es6_import(self):
        """Test ES6 import statement."""
        parser = JSParser()
        source = "import React from 'react';\nimport { useState } from 'react';"
        
        imports = parser.extract_imports(source, "test.js")
        
        assert len(imports) == 1  # Deduplicated
        assert imports[0].module_path == "react"
        assert not imports[0].is_relative
    
    def test_commonjs_require(self):
        """Test CommonJS require statement."""
        parser = JSParser()
        source = "const fs = require('fs');\nconst path = require('path');"
        
        imports = parser.extract_imports(source, "test.js")
        
        assert len(imports) == 2
        assert imports[0].module_path == "fs"
        assert imports[1].module_path == "path"
    
    def test_relative_import(self):
        """Test relative import statement."""
        parser = JSParser()
        source = "import utils from './utils';\nimport config from '../config';"
        
        imports = parser.extract_imports(source, "src/components/Button.tsx")
        
        assert len(imports) == 2
        assert imports[0].module_path == "./utils"
        assert imports[0].is_relative
        assert imports[1].module_path == "../config"
        assert imports[1].is_relative
    
    def test_dynamic_import(self):
        """Test dynamic import statement."""
        parser = JSParser()
        source = "const module = import('./module');"
        
        imports = parser.extract_imports(source, "test.js")
        
        assert len(imports) == 1
        assert imports[0].module_path == "./module"
    
    def test_export_from(self):
        """Test re-export statement."""
        parser = JSParser()
        source = "export { Button } from './Button';"
        
        imports = parser.extract_imports(source, "index.ts")
        
        assert len(imports) == 1
        assert imports[0].module_path == "./Button"


class TestDependencyAnalyzer:
    """Test full dependency analysis pipeline."""
    
    def test_simple_three_file_case(self):
        """Test simple case with 3 files in a chain."""
        analyzer = DependencyAnalyzer()
        
        # Create synthetic PR with 3 Python files
        files = [
            FileChange(
                filename="backend/models/user.py",
                status="modified",
                additions=10,
                deletions=2,
                patch="class User:\n    pass",
                language="python"
            ),
            FileChange(
                filename="backend/services/auth.py",
                status="modified",
                additions=15,
                deletions=3,
                patch="from models.user import User\n\nclass AuthService:\n    pass",
                language="python"
            ),
            FileChange(
                filename="backend/api/routes.py",
                status="modified",
                additions=20,
                deletions=5,
                patch="from services.auth import AuthService\n\ndef login():\n    pass",
                language="python"
            ),
        ]
        
        result = analyzer.analyze(files)
        
        # Verify basic structure
        assert result.total_files == 3
        assert len(result.graph.nodes) == 3
        assert result.total_edges >= 2  # At least auth->user and routes->auth
        
        # Verify nodes exist
        node_ids = {node.id for node in result.graph.nodes}
        assert "backend/models/user.py" in node_ids
        assert "backend/services/auth.py" in node_ids
        assert "backend/api/routes.py" in node_ids
        
        # Verify at least one cluster was created
        assert len(result.clusters) >= 1
    
    def test_multi_cluster_case(self):
        """Test case with 6 files forming 2 distinct clusters."""
        analyzer = DependencyAnalyzer()
        
        # Backend cluster (3 files)
        backend_files = [
            FileChange(
                filename="backend/models/user.py",
                status="modified",
                additions=10,
                deletions=2,
                patch="class User:\n    pass",
                language="python"
            ),
            FileChange(
                filename="backend/services/auth.py",
                status="modified",
                additions=15,
                deletions=3,
                patch="from models.user import User",
                language="python"
            ),
            FileChange(
                filename="backend/api/auth_routes.py",
                status="modified",
                additions=20,
                deletions=5,
                patch="from services.auth import AuthService",
                language="python"
            ),
        ]
        
        # Frontend cluster (3 files)
        frontend_files = [
            FileChange(
                filename="frontend/components/Button.tsx",
                status="modified",
                additions=8,
                deletions=1,
                patch="export const Button = () => {}",
                language="typescript"
            ),
            FileChange(
                filename="frontend/components/Form.tsx",
                status="modified",
                additions=12,
                deletions=2,
                patch="import { Button } from './Button'",
                language="typescript"
            ),
            FileChange(
                filename="frontend/pages/Login.tsx",
                status="modified",
                additions=25,
                deletions=4,
                patch="import { Form } from '../components/Form'",
                language="typescript"
            ),
        ]
        
        files = backend_files + frontend_files
        result = analyzer.analyze(files)
        
        # Verify structure
        assert result.total_files == 6
        assert len(result.graph.nodes) == 6
        
        # Should have at least 2 clusters (backend and frontend)
        assert len(result.clusters) >= 2
        
        # Verify layer detection
        layers = {cluster.layer for cluster in result.clusters}
        assert "backend" in layers or "mixed" in layers
        assert "frontend" in layers or "mixed" in layers
    
    def test_isolated_files(self):
        """Test detection of isolated files with no dependencies."""
        analyzer = DependencyAnalyzer()
        
        files = [
            FileChange(
                filename="README.md",
                status="modified",
                additions=5,
                deletions=1,
                patch="# Updated README",
                language="markdown"
            ),
            FileChange(
                filename="config.yml",
                status="modified",
                additions=3,
                deletions=0,
                patch="setting: value",
                language="yaml"
            ),
            FileChange(
                filename="backend/models/user.py",
                status="modified",
                additions=10,
                deletions=2,
                patch="class User:\n    pass",
                language="python"
            ),
        ]
        
        result = analyzer.analyze(files)
        
        # README and config should be isolated
        assert len(result.isolated_files) >= 2
        assert "README.md" in result.isolated_files
        assert "config.yml" in result.isolated_files
    
    def test_layer_detection_schema(self):
        """Test layer detection for schema/migration files."""
        analyzer = DependencyAnalyzer()
        
        files = ["migrations/001_create_users.sql", "schema/tables.sql"]
        layer = analyzer._detect_layer(files)
        
        assert layer == "schema"
    
    def test_layer_detection_backend(self):
        """Test layer detection for backend files."""
        analyzer = DependencyAnalyzer()
        
        files = ["backend/api/routes.py", "backend/services/auth.py"]
        layer = analyzer._detect_layer(files)
        
        assert layer == "backend"
    
    def test_layer_detection_frontend(self):
        """Test layer detection for frontend files."""
        analyzer = DependencyAnalyzer()
        
        files = ["frontend/components/Button.tsx", "frontend/pages/Home.tsx"]
        layer = analyzer._detect_layer(files)
        
        assert layer == "frontend"
    
    def test_layer_detection_tests(self):
        """Test layer detection for test files."""
        analyzer = DependencyAnalyzer()
        
        files = ["tests/test_auth.py", "backend/services/auth.test.ts"]
        layer = analyzer._detect_layer(files)
        
        assert layer == "tests"
    
    def test_layer_detection_config(self):
        """Test layer detection for config files."""
        analyzer = DependencyAnalyzer()
        
        files = ["config/settings.py", "app.config.json"]
        layer = analyzer._detect_layer(files)
        
        assert layer == "config"
    
    def test_layer_detection_docs(self):
        """Test layer detection for documentation files."""
        analyzer = DependencyAnalyzer()
        
        files = ["docs/api.md", "README.md"]
        layer = analyzer._detect_layer(files)
        
        assert layer == "docs"
    
    def test_layer_detection_mixed(self):
        """Test layer detection for mixed files."""
        analyzer = DependencyAnalyzer()
        
        files = [
            "backend/api/routes.py",
            "frontend/components/Button.tsx",
            "tests/test_integration.py"
        ]
        layer = analyzer._detect_layer(files)
        
        # No clear majority, should be mixed
        assert layer == "mixed"
    
    def test_topological_order(self):
        """Test that clusters are ordered by layer priority."""
        analyzer = DependencyAnalyzer()
        
        files = [
            # Schema files
            FileChange(
                filename="migrations/001_users.sql",
                status="added",
                additions=20,
                deletions=0,
                patch="CREATE TABLE users",
                language=None
            ),
            # Backend files
            FileChange(
                filename="backend/models/user.py",
                status="modified",
                additions=10,
                deletions=2,
                patch="class User:\n    pass",
                language="python"
            ),
            # Frontend files
            FileChange(
                filename="frontend/components/UserList.tsx",
                status="modified",
                additions=15,
                deletions=3,
                patch="export const UserList = () => {}",
                language="typescript"
            ),
            # Test files
            FileChange(
                filename="tests/test_user.py",
                status="added",
                additions=30,
                deletions=0,
                patch="def test_user():\n    pass",
                language="python"
            ),
        ]
        
        result = analyzer.analyze(files)
        
        # Verify clusters are ordered by layer priority
        if len(result.clusters) > 1:
            for i in range(len(result.clusters) - 1):
                current_priority = analyzer.LAYER_PRIORITY.get(result.clusters[i].layer, 99)
                next_priority = analyzer.LAYER_PRIORITY.get(result.clusters[i + 1].layer, 99)
                assert current_priority <= next_priority
    
    def test_react_flow_export(self):
        """Test conversion to React Flow format."""
        analyzer = DependencyAnalyzer()
        
        files = [
            FileChange(
                filename="backend/models/user.py",
                status="modified",
                additions=10,
                deletions=2,
                patch="class User:\n    pass",
                language="python"
            ),
            FileChange(
                filename="backend/services/auth.py",
                status="modified",
                additions=15,
                deletions=3,
                patch="from models.user import User",
                language="python"
            ),
        ]
        
        result = analyzer.analyze(files)
        react_flow = result.graph.to_react_flow()
        
        # Verify React Flow structure
        assert "nodes" in react_flow
        assert "edges" in react_flow
        assert len(react_flow["nodes"]) == 2
        
        # Verify node structure
        node = react_flow["nodes"][0]
        assert "id" in node
        assert "data" in node
        assert "position" in node
        assert "label" in node["data"]
    
    def test_cluster_cohesion(self):
        """Test cluster cohesion calculation."""
        from models.analysis import FileCluster
        
        cluster = FileCluster(
            cluster_id="test123",
            files=["a.py", "b.py"],
            layer="backend",
            total_additions=20,
            total_deletions=5,
            internal_edges=3,
            external_edges=1,
        )
        
        # Cohesion = internal / (internal + external) = 3/4 = 0.75
        assert cluster.cohesion == 0.75
    
    def test_cluster_id_generation(self):
        """Test deterministic cluster ID generation."""
        from models.analysis import FileCluster
        
        files1 = ["a.py", "b.py", "c.py"]
        files2 = ["c.py", "a.py", "b.py"]  # Same files, different order
        
        id1 = FileCluster.generate_id(files1)
        id2 = FileCluster.generate_id(files2)
        
        # Should be identical (deterministic)
        assert id1 == id2
        assert len(id1) == 12  # 12-character hex


# Made with Bob