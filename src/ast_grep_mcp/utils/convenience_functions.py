"""
High-level convenience functions for common ast-grep operations.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import re

from ..utils.error_handling import handle_errors


class ConvenienceFunctionsMixin:
    """Mixin providing high-level convenience functions."""
    
    @handle_errors
    def find_functions(
        self,
        directory: str = ".",
        language: Optional[str] = None,
        async_only: bool = False,
        public_only: bool = False,
        name_pattern: Optional[str] = None,
        return_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find function definitions with various filters.
        
        Args:
            directory: Directory to search
            language: Language to search (auto-detect if None)
            async_only: Only find async functions
            public_only: Only find public functions
            name_pattern: Regex pattern for function names
            return_type: Filter by return type
            
        Returns:
            Dictionary with found functions
        """
        # Build patterns based on language
        patterns = self._build_function_patterns(
            language, async_only, public_only, return_type
        )
        
        results = {
            "functions": [],
            "summary": {
                "total": 0,
                "async": 0,
                "public": 0,
                "by_language": {}
            }
        }
        
        # Search with each pattern
        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                try:
                    # Use search_summary for efficiency
                    summary = self.search_summary(
                        pattern=pattern,
                        directory=directory,
                        language=lang
                    )
                    
                    if summary.get("summary", {}).get("total_matches", 0) > 0:
                        # Get detailed results for top files (limit to 10 for better coverage)
                        for file_info in summary["summary"]["top_files"][:10]:
                            file_results = self._get_function_details(
                                file_info["file"],
                                pattern,
                                lang,
                                name_pattern
                            )
                            results["functions"].extend(file_results)
                            
                            # Update summary
                            results["summary"]["total"] += len(file_results)
                            if async_only:
                                results["summary"]["async"] += len(file_results)
                            if public_only:
                                results["summary"]["public"] += len(file_results)
                            
                            if lang not in results["summary"]["by_language"]:
                                results["summary"]["by_language"][lang] = 0
                            results["summary"]["by_language"][lang] += len(file_results)
                
                except Exception as e:
                    self.logger.debug(f"Error searching with pattern {pattern}: {e}")
        
        # If no results found, try simpler fallback patterns
        if results["summary"]["total"] == 0:
            self.logger.debug("No results with detailed patterns, trying simple fallback patterns...")
            fallback_patterns = self._get_fallback_function_patterns(language, async_only, public_only)
            
            for lang, simple_patterns in fallback_patterns.items():
                for pattern in simple_patterns:
                    try:
                        summary = self.search_summary(
                            pattern=pattern,
                            directory=directory,
                            language=lang
                        )
                        
                        if summary.get("summary", {}).get("total_matches", 0) > 0:
                            # Add a note about using fallback pattern
                            results["fallback_pattern_used"] = pattern
                            results["note"] = f"Used simplified pattern '{pattern}' after detailed patterns failed"
                            
                            for file_info in summary["summary"]["top_files"][:10]:
                                file_results = self._get_function_details(
                                    file_info["file"],
                                    pattern,
                                    lang,
                                    name_pattern
                                )
                                results["functions"].extend(file_results)
                                results["summary"]["total"] += len(file_results)
                                
                                if lang not in results["summary"]["by_language"]:
                                    results["summary"]["by_language"][lang] = 0
                                results["summary"]["by_language"][lang] += len(file_results)
                            
                            # Stop after first successful fallback pattern
                            if results["summary"]["total"] > 0:
                                break
                    except Exception as e:
                        self.logger.debug(f"Error with fallback pattern {pattern}: {e}")
                        
                if results["summary"]["total"] > 0:
                    break
        
        # Sort by file and function name
        results["functions"].sort(key=lambda x: (x["file"], x["name"]))
        
        # Add helpful guidance if no functions found
        if results["summary"]["total"] == 0:
            results["suggestions"] = self._get_function_search_suggestions(
                directory, language, async_only, public_only
            )
        
        return results
    
    @handle_errors
    def find_classes(
        self,
        directory: str = ".",
        language: Optional[str] = None,
        with_inheritance: bool = False,
        name_pattern: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find class/struct definitions.
        
        Args:
            directory: Directory to search
            language: Language to search
            with_inheritance: Only find classes that inherit
            name_pattern: Regex pattern for class names
            
        Returns:
            Dictionary with found classes
        """
        patterns = self._build_class_patterns(language, with_inheritance)
        
        results = {
            "classes": [],
            "summary": {
                "total": 0,
                "with_inheritance": 0,
                "by_language": {}
            }
        }
        
        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                try:
                    summary = self.search_summary(
                        pattern=pattern,
                        directory=directory,
                        language=lang
                    )
                    
                    if summary.get("summary", {}).get("total_matches", 0) > 0:
                        for file_info in summary["summary"]["top_files"][:10]:  # Increased limit for better coverage
                            class_results = self._get_class_details(
                                file_info["file"],
                                pattern,
                                lang,
                                name_pattern
                            )
                            results["classes"].extend(class_results)
                            
                            results["summary"]["total"] += len(class_results)
                            if with_inheritance:
                                results["summary"]["with_inheritance"] += len(class_results)
                            
                            if lang not in results["summary"]["by_language"]:
                                results["summary"]["by_language"][lang] = 0
                            results["summary"]["by_language"][lang] += len(class_results)
                
                except Exception as e:
                    self.logger.debug(f"Error searching with pattern {pattern}: {e}")
        
        results["classes"].sort(key=lambda x: (x["file"], x["name"]))
        
        # Add helpful guidance if no classes found
        if results["summary"]["total"] == 0:
            results["suggestions"] = self._get_class_search_suggestions(
                directory, language, with_inheritance
            )
        
        return results
    
    @handle_errors
    def find_todos_and_fixmes(
        self,
        directory: str = ".",
        include_patterns: Optional[List[str]] = None,
        case_sensitive: bool = False,
    ) -> Dict[str, Any]:
        """
        Find TODO, FIXME, and other code comments.
        
        Args:
            directory: Directory to search
            include_patterns: Additional patterns to search for
            case_sensitive: Whether to match case-sensitively
            
        Returns:
            Dictionary with found TODOs and FIXMEs
        """
        # Default patterns
        patterns = ["TODO", "FIXME", "HACK", "XXX", "BUG", "REFACTOR"]
        if include_patterns:
            patterns.extend(include_patterns)
        
        results = {
            "items": [],
            "summary": {
                "total": 0,
                "by_type": {},
                "by_file": {}
            }
        }
        
        # Build regex pattern
        if case_sensitive:
            regex_pattern = f"({'|'.join(patterns)})"
        else:
            regex_pattern = f"(?i)({'|'.join(patterns)})"
        
        # Use simple file search for comments
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            if not dir_path.is_dir():
                return {"error": f"Path is not a directory: {directory}"}
        except Exception as e:
            return {"error": f"Invalid directory path: {directory} - {str(e)}"}
            
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Skip binary files
            if file_path.suffix in ['.pyc', '.pyo', '.so', '.dylib', '.dll']:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        # CRITICAL FIX: Only look in actual comments, not code content
                        comment_text = self._extract_comment_text(line, file_path.suffix)
                        
                        if comment_text:
                            match = re.search(regex_pattern + r"[:\s]*(.+)$", comment_text)
                            if match:
                                todo_type = match.group(1).upper()
                                message = match.group(2).strip() if match.group(2) else ""
                                
                                # Skip false positives like #[derive(Debug)]
                                if self._is_false_positive_todo(line, todo_type):
                                    continue
                                
                                item = {
                                    "type": todo_type,
                                    "message": message,
                                    "file": str(file_path.relative_to(dir_path)),
                                    "line": line_num,
                                    "text": line.strip(),
                                    "comment_text": comment_text
                                }
                                results["items"].append(item)
                                
                                # Update summary
                                results["summary"]["total"] += 1
                                
                                if todo_type not in results["summary"]["by_type"]:
                                    results["summary"]["by_type"][todo_type] = 0
                                results["summary"]["by_type"][todo_type] += 1
                                
                                file_str = str(file_path.relative_to(dir_path))
                                if file_str not in results["summary"]["by_file"]:
                                    results["summary"]["by_file"][file_str] = 0
                                results["summary"]["by_file"][file_str] += 1
            
            except Exception as e:
                self.logger.debug(f"Error reading {file_path}: {e}")
        
        # Sort by type and file
        results["items"].sort(key=lambda x: (x["type"], x["file"], x["line"]))
        
        return results
    
    @handle_errors
    def find_potential_bugs(
        self,
        directory: str = ".",
        language: Optional[str] = None,
        bug_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find potential bugs and code smells.
        
        Args:
            directory: Directory to search
            language: Language to search
            bug_patterns: Custom bug patterns to search for
            
        Returns:
            Dictionary with potential bugs
        """
        # Language-specific bug patterns
        default_patterns = {
            "python": [
                # Mutable default arguments
                {"pattern": "def $FUNC($$$ARGS = [])", "issue": "mutable default argument"},
                {"pattern": "def $FUNC($$$ARGS = {})", "issue": "mutable default argument"},
                # Bare except
                {"pattern": "except:", "issue": "bare except clause"},
                # == None instead of is None
                {"pattern": "$VAR == None", "issue": "use 'is None' instead of '== None'"},
            ],
            "javascript": [
                # Using == instead of ===
                {"pattern": "$A == $B", "issue": "use === for strict equality"},
                # Missing await
                {"pattern": "$FUNC($$$ARGS).then", "issue": "possibly missing await"},
                # console.log in production
                {"pattern": "console.log($$$ARGS)", "issue": "console.log in code"},
            ],
            "rust": [
                # Unwrap without error handling
                {"pattern": "$EXPR.unwrap()", "issue": "unwrap() can panic"},
                {"pattern": "$EXPR.expect($MSG)", "issue": "expect() can panic"},
                # Clone when not needed
                {"pattern": "$VAR.clone().clone()", "issue": "multiple unnecessary clones"},
            ],
            "go": [
                # Ignoring errors
                {"pattern": "$VAR, _ := $EXPR", "issue": "ignoring error"},
                # Empty error check
                {"pattern": "if err != nil { }", "issue": "empty error handling"},
            ],
        }
        
        results = {
            "bugs": [],
            "summary": {
                "total": 0,
                "by_severity": {
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                },
                "by_type": {},
                "by_language": {}
            }
        }
        
        # Determine languages to check
        if language:
            languages = [language]
        else:
            languages = list(default_patterns.keys())
        
        # Add custom patterns if provided
        if bug_patterns:
            for pattern in bug_patterns:
                if isinstance(pattern, dict) and "pattern" in pattern:
                    for lang in languages:
                        if lang not in default_patterns:
                            default_patterns[lang] = []
                        default_patterns[lang].append(pattern)
        
        # Search for each pattern
        for lang in languages:
            if lang not in default_patterns:
                continue
            
            for bug_pattern in default_patterns[lang]:
                try:
                    pattern = bug_pattern["pattern"]
                    issue = bug_pattern.get("issue", "potential issue")
                    severity = bug_pattern.get("severity", "medium")
                    
                    # Use search_files_only for efficiency
                    try:
                        search_results = self.search_files_only(
                            pattern=pattern,
                            directory=directory,
                            language=lang
                        )
                    except Exception as e:
                        self.logger.debug(f"search_files_only failed: {e}, trying search_summary")
                        # Fallback to search_summary if search_files_only fails
                        search_results = self.search_summary(
                            pattern=pattern,
                            directory=directory,
                            language=lang
                        )
                        # Convert summary format to files format
                        if "summary" in search_results:
                            search_results = {
                                "total_matches": search_results["summary"]["total_matches"],
                                "files": [{"file": f["file"], "match_count": f["matches"]} 
                                         for f in search_results["summary"]["top_files"]]
                            }
                    
                    if search_results.get("total_matches", 0) > 0:
                        for file_info in search_results.get("files", [])[:5]:  # Limit to 5 files per pattern
                            bug = {
                                "file": file_info["file"],
                                "pattern": pattern,
                                "issue": issue,
                                "severity": severity,
                                "language": lang,
                                "matches": file_info["match_count"]
                            }
                            results["bugs"].append(bug)
                            
                            # Update summary
                            results["summary"]["total"] += file_info["match_count"]
                            results["summary"]["by_severity"][severity] += file_info["match_count"]
                            
                            if issue not in results["summary"]["by_type"]:
                                results["summary"]["by_type"][issue] = 0
                            results["summary"]["by_type"][issue] += file_info["match_count"]
                            
                            if lang not in results["summary"]["by_language"]:
                                results["summary"]["by_language"][lang] = 0
                            results["summary"]["by_language"][lang] += file_info["match_count"]
                
                except Exception as e:
                    self.logger.debug(f"Error searching for pattern {pattern}: {e}")
        
        # Sort by severity and file
        severity_order = {"high": 0, "medium": 1, "low": 2}
        results["bugs"].sort(key=lambda x: (severity_order.get(x["severity"], 1), x["file"]))
        
        return results
    
    @handle_errors
    def find_imports(
        self,
        directory: str = ".",
        language: Optional[str] = None,
        module_name: Optional[str] = None,
        unused: bool = False,
    ) -> Dict[str, Any]:
        """
        Find import statements.
        
        Args:
            directory: Directory to search
            language: Language to search
            module_name: Specific module to find imports of
            unused: Try to find potentially unused imports
            
        Returns:
            Dictionary with import information
        """
        # Language-specific import patterns
        import_patterns = {
            "python": [
                "import $MODULE",
                "from $MODULE import $NAME",
                "from $MODULE import $$$NAMES",
            ],
            "javascript": [
                "import $NAME from '$MODULE'",
                "import { $$$NAMES } from '$MODULE'",
                "import * as $NAME from '$MODULE'",
                "const $NAME = require('$MODULE')",
            ],
            "typescript": [
                "import $NAME from '$MODULE'",
                "import { $$$NAMES } from '$MODULE'",
                "import type { $$$TYPES } from '$MODULE'",
            ],
            "rust": [
                "use $PATH",
                "use $PATH as $ALIAS",
                "use $PATH::{$$$ITEMS}",
            ],
            "go": [
                "import \"$PACKAGE\"",
                "import $ALIAS \"$PACKAGE\"",
                "import ($$$IMPORTS)",
            ],
        }
        
        results = {
            "imports": [],
            "summary": {
                "total": 0,
                "by_module": {},
                "by_file": {},
                "by_language": {}
            }
        }
        
        # Determine languages
        if language:
            languages = [language]
        else:
            languages = list(import_patterns.keys())
        
        for lang in languages:
            if lang not in import_patterns:
                continue
            
            for pattern in import_patterns[lang]:
                try:
                    # If looking for specific module, modify pattern
                    if module_name:
                        # This is simplified - real implementation would be smarter
                        if "$MODULE" in pattern:
                            pattern = pattern.replace("$MODULE", module_name)
                        elif "$PACKAGE" in pattern:
                            pattern = pattern.replace("$PACKAGE", module_name)
                        elif "$PATH" in pattern and lang == "rust":
                            continue  # Skip rust use statements when looking for modules
                    
                    search_results = self.search_files_only(
                        pattern=pattern,
                        directory=directory,
                        language=lang
                    )
                    
                    if search_results.get("total_matches", 0) > 0:
                        for file_info in search_results.get("files", []):
                            import_info = {
                                "file": file_info["file"],
                                "language": lang,
                                "pattern": pattern,
                                "matches": file_info["match_count"]
                            }
                            
                            # If checking for unused imports, we'd need more analysis
                            if unused:
                                import_info["potentially_unused"] = self._check_unused_import(
                                    file_info["file"], pattern, lang
                                )
                            
                            results["imports"].append(import_info)
                            
                            # Update summary
                            results["summary"]["total"] += file_info["match_count"]
                            
                            if file_info["file"] not in results["summary"]["by_file"]:
                                results["summary"]["by_file"][file_info["file"]] = 0
                            results["summary"]["by_file"][file_info["file"]] += file_info["match_count"]
                            
                            if lang not in results["summary"]["by_language"]:
                                results["summary"]["by_language"][lang] = 0
                            results["summary"]["by_language"][lang] += file_info["match_count"]
                
                except Exception as e:
                    self.logger.debug(f"Error searching for imports: {e}")
        
        return results
    
    def _build_function_patterns(
        self,
        language: Optional[str],
        async_only: bool,
        public_only: bool,
        return_type: Optional[str]
    ) -> Dict[str, List[str]]:
        """Build function patterns based on filters."""
        patterns = {}
        
        if not language or language == "python":
            py_patterns = []
            base = "async def" if async_only else "def"
            if return_type:
                py_patterns.append(f"{base} $NAME($$$ARGS) -> {return_type}")
            else:
                py_patterns.append(f"{base} $NAME($$$ARGS)")
            patterns["python"] = py_patterns
        
        if not language or language == "javascript":
            js_patterns = []
            if async_only:
                js_patterns.extend([
                    "async function $NAME($$$ARGS)",
                    "const $NAME = async ($$$ARGS) =>",
                ])
            else:
                js_patterns.extend([
                    "function $NAME($$$ARGS)",
                    "const $NAME = ($$$ARGS) =>",
                ])
            patterns["javascript"] = js_patterns
        
        if not language or language == "rust":
            rust_patterns = []
            
            if async_only:
                # Async function patterns
                if public_only:
                    rust_patterns.extend([
                        "pub async fn $NAME()",
                        "pub async fn $NAME($$$ARGS)",
                        "pub async fn $NAME() -> $RET",
                        "pub async fn $NAME($$$ARGS) -> $RET"
                    ])
                else:
                    rust_patterns.extend([
                        "async fn $NAME()",
                        "async fn $NAME($$$ARGS)",
                        "async fn $NAME() -> $RET",
                        "async fn $NAME($$$ARGS) -> $RET",
                        "pub async fn $NAME()",
                        "pub async fn $NAME($$$ARGS)",
                        "pub async fn $NAME() -> $RET",
                        "pub async fn $NAME($$$ARGS) -> $RET"
                    ])
            else:
                # Regular function patterns (both sync and async)
                if public_only:
                    rust_patterns.extend([
                        "pub fn $NAME()",
                        "pub fn $NAME($$$ARGS)",
                        "pub fn $NAME() -> $RET", 
                        "pub fn $NAME($$$ARGS) -> $RET"
                    ])
                else:
                    rust_patterns.extend([
                        "fn $NAME()",
                        "fn $NAME($$$ARGS)",
                        "fn $NAME() -> $RET",
                        "fn $NAME($$$ARGS) -> $RET",
                        "pub fn $NAME()",
                        "pub fn $NAME($$$ARGS)",
                        "pub fn $NAME() -> $RET",
                        "pub fn $NAME($$$ARGS) -> $RET"
                    ])
            
            # Filter by return type if specified
            if return_type:
                rust_patterns = [p for p in rust_patterns if "-> $RET" in p]
                rust_patterns = [p.replace("$RET", return_type) for p in rust_patterns]
            
            patterns["rust"] = rust_patterns
        
        return patterns
    
    def _get_fallback_function_patterns(
        self,
        language: Optional[str],
        async_only: bool,
        public_only: bool
    ) -> Dict[str, List[str]]:
        """Get simple fallback patterns that are more likely to work."""
        patterns = {}
        
        if not language or language == "python":
            if async_only:
                patterns["python"] = ["async def $NAME"]
            else:
                patterns["python"] = ["def $NAME"]
        
        if not language or language == "javascript":
            if async_only:
                patterns["javascript"] = ["async function $NAME", "async $NAME"]
            else:
                patterns["javascript"] = ["function $NAME", "const $NAME ="]
        
        if not language or language == "rust":
            if async_only:
                if public_only:
                    patterns["rust"] = ["pub async fn $NAME"]
                else:
                    patterns["rust"] = ["async fn $NAME", "pub async fn $NAME"]
            else:
                if public_only:
                    patterns["rust"] = ["pub fn $NAME"]
                else:
                    patterns["rust"] = ["fn $NAME"]  # This is the pattern that worked for the user!
        
        return patterns
    
    def _get_function_search_suggestions(
        self,
        directory: str,
        language: Optional[str],
        async_only: bool,
        public_only: bool
    ) -> List[str]:
        """Provide helpful suggestions when no functions are found."""
        suggestions = []
        
        # Basic troubleshooting suggestions
        suggestions.append(f"Try using search_summary() with pattern 'fn $NAME' to verify functions exist in {directory}")
        
        if language:
            suggestions.append(f"Verify {language} files exist in the directory")
        else:
            suggestions.append("Try specifying a specific language (e.g., language='rust')")
        
        if async_only:
            suggestions.append("Try removing async_only=True to include all functions")
        
        if public_only:
            suggestions.append("Try removing public_only=True to include private functions")
        
        # Alternative approaches
        suggestions.append("Use search_directory() with pattern 'fn $NAME' for more detailed analysis")
        suggestions.append("Check if the directory contains the expected file types")
        suggestions.append("Try a broader directory search or check file permissions")
        
        return suggestions
    
    def _get_class_search_suggestions(
        self,
        directory: str,
        language: Optional[str],
        with_inheritance: bool
    ) -> List[str]:
        """Provide helpful suggestions when no classes are found."""
        suggestions = []
        
        # Basic troubleshooting suggestions
        if language == "rust":
            suggestions.append(f"Try using search_summary() with pattern 'struct $NAME' to find Rust structs in {directory}")
        else:
            suggestions.append(f"Try using search_summary() with pattern 'class $NAME' to verify classes exist in {directory}")
        
        if language:
            suggestions.append(f"Verify {language} files exist in the directory")
        else:
            suggestions.append("Try specifying a specific language (e.g., language='python')")
        
        if with_inheritance:
            suggestions.append("Try removing with_inheritance=True to include all classes")
        
        # Alternative approaches
        suggestions.append("Use search_directory() with appropriate class patterns for more detailed analysis")
        suggestions.append("For Rust: look for 'struct $NAME' or 'enum $NAME' instead of classes")
        suggestions.append("Check if the directory contains the expected file types")
        
        return suggestions
    
    def _extract_comment_text(self, line: str, file_extension: str) -> Optional[str]:
        """Extract only the comment part from a line, ignoring code."""
        line = line.strip()
        
        # Skip obviously non-comment lines
        if not line:
            return None
        
        # Skip lines that look like function/variable definitions containing TODO words
        if any(keyword in line.lower() for keyword in ['def ', 'fn ', 'function ', 'class ', 'struct ', 'enum ', 'impl ', 'trait ']):
            return None
            
        if file_extension in ['.rs', '.js', '.jsx', '.ts', '.tsx', '.c', '.cpp', '.h', '.go', '.java']:
            # C-style comments
            if '//' in line:
                comment_start = line.find('//')
                # Make sure // is not inside a string
                before_comment = line[:comment_start]
                if before_comment.count('"') % 2 == 0 and before_comment.count("'") % 2 == 0:
                    comment_text = line[comment_start + 2:].strip()
                    # Skip empty comments or ones that are just slashes
                    if comment_text and not comment_text.startswith('/'):
                        return comment_text
            # Multi-line comments (simple detection)
            elif '/*' in line and '*/' in line:
                start = line.find('/*')
                end = line.find('*/')
                if start < end:
                    comment_text = line[start + 2:end].strip()
                    if comment_text:
                        return comment_text
        
        elif file_extension in ['.py', '.rb', '.sh']:
            # Python/Ruby/Shell comments
            if '#' in line:
                # Skip Rust attributes like #[derive(...)]
                if line.strip().startswith('#[') and ']' in line:
                    return None
                
                # Skip shebang lines
                if line.strip().startswith('#!'):
                    return None
                
                comment_start = line.find('#')
                # Check if it's actually a comment (not in a string)
                before_hash = line[:comment_start]
                
                # More robust string detection
                in_single_quote = False
                in_double_quote = False
                escaped = False
                
                for char in before_hash:
                    if escaped:
                        escaped = False
                        continue
                    if char == '\\':
                        escaped = True
                        continue
                    if char == "'" and not in_double_quote:
                        in_single_quote = not in_single_quote
                    elif char == '"' and not in_single_quote:
                        in_double_quote = not in_double_quote
                
                # Only extract comment if # is not inside quotes
                if not in_single_quote and not in_double_quote:
                    comment_text = line[comment_start + 1:].strip()
                    if comment_text:
                        return comment_text
        
        return None
    
    def _is_false_positive_todo(self, line: str, todo_type: str) -> bool:
        """Check if this is a false positive TODO detection."""
        line_lower = line.lower().strip()
        todo_lower = todo_type.lower()
        
        # Skip Rust attributes like #[derive(Debug)]
        if line_lower.startswith('#[') and ']' in line_lower:
            return True
        
        # Skip shebang lines
        if line_lower.startswith('#!'):
            return True
        
        # Skip import statements containing the word
        if any(keyword in line_lower for keyword in ['import ', 'use ', 'from ', '#include', 'require(', 'require ']):
            return True
            
        # Skip function/variable/type names containing the word
        if any(pattern in line_lower for pattern in ['def ', 'fn ', 'function ', 'class ', 'struct ', 'enum ', 'type ', 'interface ', 'trait ']):
            # Check if the TODO word is part of a name, not a comment
            if '//' not in line and '/*' not in line and not line.strip().startswith('#'):
                return True
        
        # Skip if the word appears in URL or file paths
        if any(pattern in line_lower for pattern in ['http://', 'https://', 'ftp://', 'file://', '.com/', '.org/', '.net/']):
            return True
        
        # Skip configuration/metadata (common false positives)
        if any(pattern in line_lower for pattern in ['version', 'author', 'license', 'description', 'name =', 'title =']):
            return True
        
        # Skip if the word appears in a string literal (enhanced detection)
        if '"' in line or "'" in line:
            import re
            # Find all quoted strings and check if TODO is inside them
            quoted_patterns = [
                r'"[^"]*"',  # Double quotes
                r"'[^']*'",  # Single quotes
                r'`[^`]*`',  # Backticks
            ]
            
            for pattern in quoted_patterns:
                quoted_strings = re.findall(pattern, line)
                for quoted in quoted_strings:
                    if todo_lower in quoted.lower():
                        return True
        
        # Skip if it's a file extension or filename
        if any(ext in line_lower for ext in ['.todo', 'todo.', 'todos.', 'fixme.', '.fixme']):
            return True
        
        # Skip if it's part of a variable or constant name (camelCase, snake_case, UPPER_CASE)
        import re
        # Check for patterns like todoList, TODO_ITEM, fix_me_later, etc.
        name_patterns = [
            r'\b\w*' + re.escape(todo_lower) + r'\w*\s*[=:]',  # Variable assignment
            r'\b[A-Z_]*' + re.escape(todo_lower.upper()) + r'[A-Z_]*\b',  # CONSTANT_NAME
            r'\b\w*' + re.escape(todo_lower) + r'[A-Z]\w*',  # camelCase
        ]
        
        for pattern in name_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Double-check it's not in a comment
                if '//' not in line and '/*' not in line and not line.strip().startswith('#'):
                    return True
        
        return False
    
    def _build_class_patterns(
        self,
        language: Optional[str],
        with_inheritance: bool
    ) -> Dict[str, List[str]]:
        """Build class patterns based on filters."""
        patterns = {}
        
        if not language or language == "python":
            if with_inheritance:
                patterns["python"] = ["class $NAME($BASE)"]
            else:
                patterns["python"] = ["class $NAME", "class $NAME($$$BASES)"]
        
        if not language or language == "javascript":
            if with_inheritance:
                patterns["javascript"] = ["class $NAME extends $BASE"]
            else:
                patterns["javascript"] = ["class $NAME"]
        
        if not language or language == "rust":
            # Rust doesn't have classes, but has structs
            patterns["rust"] = ["struct $NAME", "pub struct $NAME"]
        
        return patterns
    
    def _get_function_details(
        self,
        file_path: str,
        pattern: str,
        language: str,
        name_pattern: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get detailed function information from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use analyzer to get actual matches
            if hasattr(self, 'analyzer') and self.analyzer:
                result = self.analyzer.analyze_code(content, language, pattern)
                if result and result.get("matches"):
                    functions = []
                    for match in result["matches"]:
                        # Extract function name if possible
                        function_name = "unknown"
                        if "metavariables" in match:
                            # Look for NAME metavariable
                            for metavar in match["metavariables"]:
                                if metavar.get("name") == "$NAME":
                                    function_name = metavar.get("value", "unknown")
                                    break
                        
                        # Apply name pattern filter if provided
                        if name_pattern:
                            import re
                            if not re.search(name_pattern, function_name):
                                continue
                        
                        function_info = {
                            "name": function_name,
                            "file": file_path,
                            "language": language,
                            "line": match.get("location", {}).get("start", {}).get("line", 0),
                            "column": match.get("location", {}).get("start", {}).get("column", 0),
                            "text": match.get("text", "").strip()[:200],  # Limit text to prevent token issues
                            "pattern_matched": pattern
                        }
                        functions.append(function_info)
                    
                    return functions
            
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(f"Error getting function details from {file_path}: {e}")
        
        return []
    
    def _get_class_details(
        self,
        file_path: str,
        pattern: str,
        language: str,
        name_pattern: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get detailed class information from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use analyzer to get actual matches
            if hasattr(self, 'analyzer') and self.analyzer:
                result = self.analyzer.analyze_code(content, language, pattern)
                if result and result.get("matches"):
                    classes = []
                    for match in result["matches"]:
                        # Extract class name if possible
                        class_name = "unknown"
                        if "metavariables" in match:
                            # Look for NAME metavariable
                            for metavar in match["metavariables"]:
                                if metavar.get("name") == "$NAME":
                                    class_name = metavar.get("value", "unknown")
                                    break
                        
                        # Apply name pattern filter if provided
                        if name_pattern:
                            import re
                            if not re.search(name_pattern, class_name):
                                continue
                        
                        class_info = {
                            "name": class_name,
                            "file": file_path,
                            "language": language,
                            "line": match.get("location", {}).get("start", {}).get("line", 0),
                            "column": match.get("location", {}).get("start", {}).get("column", 0),
                            "text": match.get("text", "").strip()[:200],  # Limit text to prevent token issues
                            "pattern_matched": pattern
                        }
                        classes.append(class_info)
                    
                    return classes
            
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(f"Error getting class details from {file_path}: {e}")
        
        return []
    
    def _check_unused_import(
        self,
        file_path: str,
        import_pattern: str,
        language: str
    ) -> bool:
        """Check if an import might be unused."""
        # Simplified implementation
        # Would need to analyze usage in the file
        return False