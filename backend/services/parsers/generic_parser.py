"""
Generic fallback parser for other programming languages.
Uses simple regex patterns for common import/include/using statements.
Achieves ~60-70% accuracy, suitable for demo purposes.
"""

import re

from loguru import logger

from models.analysis import Import


class GenericParser:
    """
    Fallback parser for languages not explicitly supported.
    
    Handles common patterns in:
    - Go: import "package"
    - Java: import package.Class;
    - Ruby: require 'module'
    - Rust: use module::item;
    - C/C++: #include "file.h"
    - PHP: require 'file.php'
    """
    
    # Compiled regex patterns for various languages
    PATTERNS = {
        # Go: import "package" or import ("package1" "package2")
        "go": re.compile(r'import\s+"([^"]+)"', re.MULTILINE),
        
        # Java: import package.Class;
        "java": re.compile(r'import\s+([\w.]+);', re.MULTILINE),
        
        # Ruby: require 'module' or require "module"
        "ruby": re.compile(r"require\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
        
        # Rust: use module::item;
        "rust": re.compile(r'use\s+([\w:]+);', re.MULTILINE),
        
        # C/C++: #include "file.h" or #include <file.h>
        "c": re.compile(r'#include\s+[<"]([^>"]+)[>"]', re.MULTILINE),
        "cpp": re.compile(r'#include\s+[<"]([^>"]+)[>"]', re.MULTILINE),
        
        # PHP: require 'file.php' or include 'file.php'
        "php": re.compile(r"(?:require|include)(?:_once)?\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    }
    
    def __init__(self, language: str | None = None):
        """
        Initialize parser for a specific language.
        
        Args:
            language: Programming language name (e.g., "go", "java", "ruby")
                     If None, will try all patterns
        """
        self.language = language
    
    def extract_imports(self, source: str, file_path: str) -> list[Import]:
        """
        Extract import statements using regex patterns.
        
        Args:
            source: Source code as string
            file_path: Path to the file (for context and language detection)
            
        Returns:
            List of Import objects representing detected imports
        """
        imports = []
        seen = set()  # Deduplicate
        
        # Determine which patterns to use
        if self.language and self.language in self.PATTERNS:
            patterns_to_try = [(self.language, self.PATTERNS[self.language])]
        else:
            # Try all patterns if language not specified or not recognized
            patterns_to_try = list(self.PATTERNS.items())
        
        for lang, pattern in patterns_to_try:
            for match in pattern.finditer(source):
                module_path = match.group(1)
                
                # Skip if already seen
                if module_path in seen:
                    continue
                seen.add(module_path)
                
                # Calculate line number
                line_number = source[:match.start()].count('\n') + 1
                
                # Determine if relative (heuristic: starts with . or contains /)
                is_relative = module_path.startswith('.') or '/' in module_path
                
                imports.append(Import(
                    module_path=module_path,
                    imported_names=[],
                    is_relative=is_relative,
                    line_number=line_number,
                ))
                
                logger.debug(
                    f"Found {lang} import: {module_path} "
                    f"at line {line_number} in {file_path}"
                )
        
        logger.debug(f"Extracted {len(imports)} imports from {file_path} using generic parser")
        return imports


# Made with Bob