"""
Python import parser using stdlib ast module.
Extracts import statements with 100% accuracy for valid Python code.
Falls back to regex parsing for files with syntax errors.
"""

import ast
import re
from pathlib import Path

from loguru import logger

from models.analysis import Import


class PythonParser:
    """
    AST-based parser for Python imports.
    
    Handles:
    - import module
    - import module as alias
    - from module import name
    - from module import name as alias
    - from .relative import name (relative imports)
    - from ..parent import name (parent relative imports)
    """
    
    def extract_imports(self, source: str, file_path: str) -> list[Import]:
        """
        Extract all import statements from Python source code.
        
        Uses AST parsing for accuracy, falls back to regex on syntax errors.
        
        Args:
            source: Python source code as string
            file_path: Path to the file (for context in error messages)
            
        Returns:
            List of Import objects representing all imports in the file
        """
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            logger.warning(f"AST parse failed for {file_path}: {e}, using regex fallback")
            return self._regex_fallback(source, file_path)
        
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # Handle: import module [as alias]
                for alias in node.names:
                    imports.append(Import(
                        module_path=alias.name,
                        imported_names=[alias.asname or alias.name],
                        is_relative=False,
                        line_number=node.lineno,
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                # Handle: from module import name [as alias]
                if node.module is None:
                    # from . import name or from .. import name
                    # Use dots to represent relative level
                    module_path = "." * node.level
                else:
                    # from module import name or from .module import name
                    if node.level > 0:
                        # Relative import: from .module or from ..module
                        module_path = "." * node.level + node.module
                    else:
                        # Absolute import: from module import name
                        module_path = node.module
                
                imported_names = [alias.name for alias in node.names]
                
                imports.append(Import(
                    module_path=module_path,
                    imported_names=imported_names,
                    is_relative=node.level > 0,
                    line_number=node.lineno,
                ))
        
        logger.debug(f"Extracted {len(imports)} imports from {file_path}")
        return imports
    
    def _regex_fallback(self, source: str, file_path: str) -> list[Import]:
        """
        Fallback regex-based import extraction when AST parsing fails.
        
        Lower accuracy but always works, even with syntax errors or
        version-specific syntax issues.
        
        Args:
            source: Python source code as string
            file_path: Path to the file (for context)
            
        Returns:
            List of Import objects
        """
        imports = []
        
        # Pattern for: import module [as alias]
        import_pattern = re.compile(r'^\s*import\s+([\w.]+)(?:\s+as\s+\w+)?', re.MULTILINE)
        
        # Pattern for: from module import ...
        from_pattern = re.compile(r'^\s*from\s+([\w.]+)\s+import', re.MULTILINE)
        
        # Pattern for relative imports: from . import ... or from .. import ...
        relative_pattern = re.compile(r'^\s*from\s+(\.+[\w.]*)\s+import', re.MULTILINE)
        
        # Extract regular imports
        for match in import_pattern.finditer(source):
            module_path = match.group(1)
            imports.append(Import(
                module_path=module_path,
                imported_names=[module_path],
                is_relative=False,
                line_number=source[:match.start()].count('\n') + 1,
            ))
        
        # Extract from imports (absolute)
        for match in from_pattern.finditer(source):
            module_path = match.group(1)
            if not module_path.startswith('.'):
                imports.append(Import(
                    module_path=module_path,
                    imported_names=[],
                    is_relative=False,
                    line_number=source[:match.start()].count('\n') + 1,
                ))
        
        # Extract relative imports
        for match in relative_pattern.finditer(source):
            module_path = match.group(1)
            imports.append(Import(
                module_path=module_path,
                imported_names=[],
                is_relative=True,
                line_number=source[:match.start()].count('\n') + 1,
            ))
        
        logger.debug(f"Regex fallback extracted {len(imports)} imports from {file_path}")
        return imports
    
    @staticmethod
    def resolve_relative_import(
        import_path: str,
        importing_file: str,
        is_relative: bool
    ) -> str:
        """
        Resolve a relative import to an absolute module path.
        
        Args:
            import_path: The import module path (e.g., ".models" or "..utils")
            importing_file: Path to the file doing the importing
            is_relative: Whether this is a relative import
            
        Returns:
            Resolved absolute module path
            
        Example:
            importing_file = "backend/services/auth.py"
            import_path = "..models.user"
            returns: "backend/models/user"
        """
        if not is_relative:
            return import_path
        
        # Count leading dots
        level = 0
        for char in import_path:
            if char == '.':
                level += 1
            else:
                break
        
        # Get the directory of the importing file
        file_dir = Path(importing_file).parent
        
        # Go up 'level - 1' directories (level 1 = same dir, level 2 = parent, etc.)
        target_dir = file_dir
        for _ in range(level - 1):
            target_dir = target_dir.parent
        
        # Get the remaining module path after the dots
        remaining = import_path[level:]
        
        if remaining:
            # Combine target directory with remaining path
            resolved = target_dir / remaining.replace('.', '/')
        else:
            # Just dots, no module name (e.g., "from . import X")
            resolved = target_dir
        
        # Convert to module path notation
        return str(resolved).replace('\\', '/').replace('/', '.')


# Made with Bob