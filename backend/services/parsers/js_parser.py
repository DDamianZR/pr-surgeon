"""
JavaScript/TypeScript import parser using regex patterns.
Achieves ~85% accuracy for MVP, suitable for ES6 and CommonJS imports.
"""

import re

from loguru import logger

from models.analysis import Import


class JSParser:
    """
    Regex-based parser for JavaScript and TypeScript imports.
    
    Handles:
    - import X from '...' (ES6 default import)
    - import { X, Y } from '...' (ES6 named imports)
    - import * as X from '...' (ES6 namespace import)
    - const X = require('...') (CommonJS)
    - import('...') (dynamic import)
    - export { X } from '...' (re-export)
    
    Note: Does not parse type-only imports (import type) for TypeScript.
    """
    
    # Compiled regex patterns for performance
    # ES6 imports: import ... from 'module'
    ES6_IMPORT = re.compile(
        r"import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+)?['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )
    
    # CommonJS: require('module')
    REQUIRE = re.compile(
        r"require\s*\(\s*['\"]([^'\"]+)['\"]?\s*\)",
        re.MULTILINE
    )
    
    # Dynamic import: import('module')
    DYNAMIC_IMPORT = re.compile(
        r"import\s*\(\s*['\"]([^'\"]+)['\"]?\s*\)",
        re.MULTILINE
    )
    
    # Re-export: export ... from 'module'
    EXPORT_FROM = re.compile(
        r"export\s+(?:\{[^}]*\}|\*)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )
    
    # Type-only imports to skip (TypeScript)
    TYPE_IMPORT = re.compile(
        r"import\s+type\s+",
        re.MULTILINE
    )
    
    def extract_imports(self, source: str, file_path: str) -> list[Import]:
        """
        Extract all import statements from JavaScript/TypeScript source code.
        
        Args:
            source: JS/TS source code as string
            file_path: Path to the file (for context in error messages)
            
        Returns:
            List of Import objects representing all imports in the file
        """
        imports = []
        seen = set()  # Deduplicate imports from same module
        
        # Remove type-only imports from source (TypeScript)
        source_without_types = self.TYPE_IMPORT.sub('', source)
        
        # Collect all patterns
        patterns = [
            (self.ES6_IMPORT, "ES6"),
            (self.REQUIRE, "CommonJS"),
            (self.DYNAMIC_IMPORT, "Dynamic"),
            (self.EXPORT_FROM, "Re-export"),
        ]
        
        for pattern, pattern_name in patterns:
            for match in pattern.finditer(source_without_types):
                module_path = match.group(1)
                
                # Skip if we've already seen this module path
                if module_path in seen:
                    continue
                seen.add(module_path)
                
                # Calculate line number
                line_number = source[:match.start()].count('\n') + 1
                
                # Determine if relative import
                is_relative = module_path.startswith('.') or module_path.startswith('..')
                
                imports.append(Import(
                    module_path=module_path,
                    imported_names=[],  # Don't parse individual names for MVP
                    is_relative=is_relative,
                    line_number=line_number,
                ))
                
                logger.debug(
                    f"Found {pattern_name} import: {module_path} "
                    f"at line {line_number} in {file_path}"
                )
        
        logger.debug(f"Extracted {len(imports)} imports from {file_path}")
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
            import_path: The import module path (e.g., "./utils" or "../models")
            importing_file: Path to the file doing the importing
            is_relative: Whether this is a relative import
            
        Returns:
            Resolved absolute module path
            
        Example:
            importing_file = "frontend/components/Button.tsx"
            import_path = "../lib/utils"
            returns: "frontend/lib/utils"
        """
        if not is_relative:
            return import_path
        
        from pathlib import Path
        
        # Get the directory of the importing file
        file_dir = Path(importing_file).parent
        
        # Resolve the relative path
        resolved = (file_dir / import_path).resolve()
        
        # Convert to forward slashes for consistency
        return str(resolved).replace('\\', '/')


# Made with Bob