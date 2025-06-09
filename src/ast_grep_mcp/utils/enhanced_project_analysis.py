"""
Enhanced project analysis that addresses the language detection issues.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from collections import defaultdict

from ..utils.error_handling import handle_errors


class EnhancedProjectAnalyzer:
    """Enhanced project analyzer with better language detection."""
    
    def __init__(self, logger=None):
        self.logger = logger
        
        # More comprehensive language mappings
        self.language_extensions = {
            "rust": [".rs"],
            "python": [".py", ".pyi"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx", ".d.ts"],
            "go": [".go"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".hh"],
            "java": [".java"],
            "kotlin": [".kt", ".kts"],
            "swift": [".swift"],
            "scala": [".scala"],
            "ruby": [".rb"],
            "php": [".php"],
            "lua": [".lua"],
            "clojure": [".clj", ".cljs", ".cljc"],
            "haskell": [".hs", ".lhs"],
            "ocaml": [".ml", ".mli"],
            "elixir": [".ex", ".exs"],
            "erlang": [".erl", ".hrl"],
            "dart": [".dart"],
            "zig": [".zig"],
        }
        
        # Project type indicators (more specific patterns)
        self.project_indicators = {
            "rust": {
                "required": ["Cargo.toml"],
                "optional": ["Cargo.lock", "src/main.rs", "src/lib.rs"],
                "directories": ["src", "tests", "benches", "examples"],
                "weight": 10  # Strong indicator
            },
            "python": {
                "required": [],
                "optional": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile", "__init__.py"],
                "directories": ["src", "tests", "test"],
                "weight": 5
            },
            "javascript": {
                "required": ["package.json"],
                "optional": ["yarn.lock", "package-lock.json", "npm-shrinkwrap.json"],
                "directories": ["src", "lib", "dist", "node_modules"],
                "weight": 8
            },
            "typescript": {
                "required": ["tsconfig.json"],
                "optional": ["package.json", "tslint.json", ".eslintrc.json"],
                "directories": ["src", "lib", "dist", "types"],
                "weight": 9
            },
            "go": {
                "required": ["go.mod"],
                "optional": ["go.sum", "main.go"],
                "directories": ["cmd", "pkg", "internal"],
                "weight": 10
            },
            "java": {
                "required": [],
                "optional": ["pom.xml", "build.gradle", "build.gradle.kts", "gradlew"],
                "directories": ["src/main/java", "src/test/java"],
                "weight": 7
            },
        }
        
        # Files to ignore when analyzing
        self.ignore_patterns = {
            ".git", ".svn", ".hg", "__pycache__", "node_modules", "target", 
            "build", "dist", ".venv", "venv", ".env", ".idea", ".vscode",
            "*.log", "*.tmp", "*.cache", ".DS_Store", "Thumbs.db"
        }
    
    def should_ignore_path(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        path_str = str(path)
        path_parts = path.parts
        
        for pattern in self.ignore_patterns:
            if pattern.startswith("*."):
                # File extension pattern
                if path.suffix == pattern[1:]:
                    return True
            elif pattern in path_parts or pattern in path_str:
                return True
        
        return False
    
    def detect_language_from_extension(self, file_path: Path) -> Optional[str]:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        for language, extensions in self.language_extensions.items():
            if ext in extensions:
                return language
        return None
    
    def analyze_project_type(self, directory: Path) -> Dict[str, Any]:
        """Analyze project type using multiple indicators."""
        scores = defaultdict(float)
        evidence = defaultdict(list)
        
        # Check for project indicator files
        for project_type, indicators in self.project_indicators.items():
            type_score = 0
            type_evidence = []
            
            # Check required files
            for required_file in indicators["required"]:
                if (directory / required_file).exists():
                    type_score += indicators["weight"]
                    type_evidence.append(f"Required file: {required_file}")
                else:
                    # If required file is missing, this can't be the project type
                    type_score = 0
                    break
            
            # Only check optional if required files are present (or none required)
            if type_score > 0 or not indicators["required"]:
                for optional_file in indicators["optional"]:
                    if (directory / optional_file).exists():
                        type_score += indicators["weight"] * 0.5
                        type_evidence.append(f"Optional file: {optional_file}")
                
                # Check for typical directories
                for dir_name in indicators["directories"]:
                    if (directory / dir_name).is_dir():
                        type_score += indicators["weight"] * 0.3
                        type_evidence.append(f"Directory: {dir_name}")
            
            if type_score > 0:
                scores[project_type] = type_score
                evidence[project_type] = type_evidence
        
        return {
            "scores": dict(scores),
            "evidence": dict(evidence),
            "primary_type": max(scores.keys(), key=scores.get) if scores else None,
            "confidence": max(scores.values()) if scores else 0
        }
    
    @handle_errors
    def analyze_project_structure_enhanced(self, directory: str) -> Dict[str, Any]:
        """
        Enhanced project structure analysis with better language detection.
        
        Args:
            directory: Root directory to analyze
            
        Returns:
            Dictionary with enhanced project analysis
        """
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            if not dir_path.is_dir():
                return {"error": f"Path exists but is not a directory: {directory}"}
        except Exception as e:
            return {"error": f"Invalid directory path '{directory}': {str(e)}"}
        
        # Add debugging info about which directory is being analyzed
        if self.logger:
            self.logger.info(f"Analyzing project structure in: {dir_path}")
        
        # Validate that we're analyzing the intended directory
        if str(dir_path) != str(Path(directory).resolve()):
            return {
                "error": f"Directory path mismatch: requested '{directory}' resolved to '{dir_path}'",
                "requested_path": directory,
                "resolved_path": str(dir_path)
            }
        
        # Initialize statistics
        file_stats = {
            "total_files": 0,
            "total_code_files": 0,
            "files_by_language": defaultdict(int),
            "files_by_extension": defaultdict(int),
            "directories": 0,
            "max_depth": 0,
        }
        
        size_stats = {
            "total_size_bytes": 0,
            "total_code_size_bytes": 0,
            "average_file_size": 0,
            "largest_files": [],
        }
        
        code_stats = {
            "total_lines": 0,
            "lines_by_language": defaultdict(int),
            "files_with_tests": [],
            "documentation_files": [],
        }
        
        file_sizes = []
        
        # Walk through directory
        for root_path in dir_path.rglob("*"):
            if self.should_ignore_path(root_path):
                continue
            
            if root_path.is_dir():
                file_stats["directories"] += 1
                depth = len(root_path.relative_to(dir_path).parts)
                file_stats["max_depth"] = max(file_stats["max_depth"], depth)
                continue
            
            if not root_path.is_file():
                continue
            
            file_stats["total_files"] += 1
            
            # Get file extension and size
            ext = root_path.suffix.lower()
            file_stats["files_by_extension"][ext] += 1
            
            try:
                size = root_path.stat().st_size
                size_stats["total_size_bytes"] += size
                file_sizes.append((str(root_path.relative_to(dir_path)), size))
            except OSError:
                continue
            
            # Detect language
            language = self.detect_language_from_extension(root_path)
            if language:
                file_stats["total_code_files"] += 1
                file_stats["files_by_language"][language] += 1
                size_stats["total_code_size_bytes"] += size
                
                # Count lines for code files
                try:
                    with open(root_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = len(f.readlines())
                        code_stats["total_lines"] += lines
                        code_stats["lines_by_language"][language] += lines
                except (OSError, UnicodeDecodeError):
                    pass
                
                # Identify test files
                filename = root_path.name.lower()
                if ("test" in filename or "spec" in filename or 
                    root_path.parent.name.lower() in ["test", "tests", "spec", "specs"]):
                    code_stats["files_with_tests"].append(str(root_path.relative_to(dir_path)))
            
            # Identify documentation files
            if ext in [".md", ".rst", ".txt", ".doc", ".docx"] or "readme" in root_path.name.lower():
                code_stats["documentation_files"].append(str(root_path.relative_to(dir_path)))
        
        # Calculate averages
        if file_stats["total_files"] > 0:
            size_stats["average_file_size"] = size_stats["total_size_bytes"] / file_stats["total_files"]
        
        # Get largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        size_stats["largest_files"] = file_sizes[:10]
        
        # Analyze project type
        project_analysis = self.analyze_project_type(dir_path)
        
        # Determine primary language
        if file_stats["files_by_language"]:
            primary_language = max(file_stats["files_by_language"].items(), key=lambda x: x[1])[0]
            language_confidence = file_stats["files_by_language"][primary_language] / file_stats["total_code_files"]
        else:
            primary_language = "unknown"
            language_confidence = 0
        
        # Override primary language with project type if detected with high confidence
        if (project_analysis["primary_type"] and 
            project_analysis["confidence"] > 5 and
            project_analysis["primary_type"] in file_stats["files_by_language"]):
            primary_language = project_analysis["primary_type"]
        
        # Build summary with diagnostic information
        summary = {
            "directory": str(dir_path),
            "requested_directory": directory,  # Show what was originally requested
            "directory_analysis": {
                "exists": dir_path.exists(),
                "is_directory": dir_path.is_dir(),
                "absolute_path": str(dir_path),
                "relative_from_cwd": str(dir_path.relative_to(Path.cwd())) if dir_path.is_relative_to(Path.cwd()) else "outside_cwd"
            },
            "project_type": project_analysis["primary_type"] or primary_language,
            "project_type_confidence": project_analysis["confidence"],
            "project_type_evidence": project_analysis["evidence"].get(project_analysis["primary_type"], []),
            
            "primary_language": primary_language,
            "language_confidence": language_confidence,
            "language_detection_method": "project_indicators" if project_analysis["confidence"] > 5 else "file_extensions",
            
            "file_statistics": {
                "total_files": file_stats["total_files"],
                "total_code_files": file_stats["total_code_files"],
                "files_by_language": dict(file_stats["files_by_language"]),
                "files_by_extension": dict(file_stats["files_by_extension"]),
                "directories": file_stats["directories"],
                "max_depth": file_stats["max_depth"],
            },
            
            "size_statistics": {
                "total_size_bytes": size_stats["total_size_bytes"],
                "total_code_size_bytes": size_stats["total_code_size_bytes"],
                "average_file_size": round(size_stats["average_file_size"], 2),
                "largest_files": size_stats["largest_files"][:5],  # Limit to 5 for token management
            },
            
            "code_statistics": {
                "total_lines": code_stats["total_lines"],
                "lines_by_language": dict(code_stats["lines_by_language"]),
                "files_with_tests": code_stats["files_with_tests"][:10],  # Limit for tokens
                "documentation_files": code_stats["documentation_files"][:10],  # Limit for tokens
            },
            
            "quality_indicators": {
                "has_tests": len(code_stats["files_with_tests"]) > 0,
                "test_file_ratio": len(code_stats["files_with_tests"]) / file_stats["total_code_files"] if file_stats["total_code_files"] > 0 else 0,
                "has_documentation": len(code_stats["documentation_files"]) > 0,
                "code_file_ratio": file_stats["total_code_files"] / file_stats["total_files"] if file_stats["total_files"] > 0 else 0,
            },
            
            "recommendations": self._generate_recommendations(file_stats, code_stats, project_analysis),
            
            # Diagnostic information to help debug directory/language detection issues
            "diagnostic_info": {
                "working_directory": str(Path.cwd()),
                "input_directory": directory,
                "resolved_directory": str(dir_path),
                "files_scanned": file_stats["total_files"],
                "code_files_found": file_stats["total_code_files"],
                "extensions_found": dict(list(file_stats["files_by_extension"].items())[:10]),  # Top 10 extensions
                "project_indicators_found": {
                    ptype: evidence for ptype, evidence in project_analysis["evidence"].items() if evidence
                },
                "detection_summary": f"Detected {primary_language} with {language_confidence:.1%} confidence via {('project_indicators' if project_analysis['confidence'] > 5 else 'file_extensions')}"
            }
        }
        
        return summary
    
    def _generate_recommendations(self, file_stats: Dict, code_stats: Dict, project_analysis: Dict) -> List[str]:
        """Generate recommendations based on project analysis."""
        recommendations = []
        
        # Test recommendations
        test_ratio = len(code_stats["files_with_tests"]) / file_stats["total_code_files"] if file_stats["total_code_files"] > 0 else 0
        if test_ratio < 0.1:
            recommendations.append("Consider adding more test files to improve code coverage")
        
        # Documentation recommendations  
        if not code_stats["documentation_files"]:
            recommendations.append("Add documentation files (README.md, docs/) to improve project maintainability")
        
        # Project structure recommendations
        if project_analysis["confidence"] < 5:
            recommendations.append("Consider adding project configuration files to clarify project type")
        
        # Language consistency
        if len(file_stats["files_by_language"]) > 3:
            recommendations.append("Multiple languages detected - consider language consistency for maintainability")
        
        return recommendations