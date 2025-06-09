"""
Project diagnostic tool to help debug directory and language detection issues.

This addresses the user feedback about the tool analyzing the wrong directory
and misidentifying project languages.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import os

from ..utils.error_handling import handle_errors


class ProjectDiagnostic:
    """Tool to diagnose project detection and language identification issues."""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    @handle_errors
    def diagnose_directory_detection(
        self,
        directory: str,
        expected_language: Optional[str] = None,
        expected_project_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive diagnostic of directory and language detection.
        
        Args:
            directory: Directory to diagnose
            expected_language: What language you expect to find
            expected_project_type: What project type you expect
            
        Returns:
            Detailed diagnostic information
        """
        
        diagnostic = {
            "input": {
                "directory": directory,
                "expected_language": expected_language,
                "expected_project_type": expected_project_type
            },
            "environment": {
                "current_working_directory": str(Path.cwd()),
                "python_working_directory": os.getcwd(),
                "script_location": str(Path(__file__).parent)
            },
            "path_resolution": {},
            "directory_validation": {},
            "content_analysis": {},
            "language_detection": {},
            "project_type_detection": {},
            "recommendations": []
        }
        
        # Step 1: Path resolution analysis
        try:
            original_path = Path(directory)
            resolved_path = original_path.resolve()
            absolute_path = original_path.absolute()
            
            diagnostic["path_resolution"] = {
                "original": directory,
                "as_path_object": str(original_path),
                "resolved": str(resolved_path),
                "absolute": str(absolute_path),
                "is_relative": not original_path.is_absolute(),
                "exists": resolved_path.exists(),
                "is_directory": resolved_path.is_dir() if resolved_path.exists() else False,
                "relative_to_cwd": str(resolved_path.relative_to(Path.cwd())) if resolved_path.exists() and resolved_path.is_relative_to(Path.cwd()) else "outside_cwd"
            }
            
            if not resolved_path.exists():
                diagnostic["directory_validation"]["error"] = f"Directory does not exist: {resolved_path}"
                diagnostic["recommendations"].append(f"Check if directory '{directory}' exists")
                diagnostic["recommendations"].append(f"Current working directory is: {Path.cwd()}")
                return diagnostic
                
            if not resolved_path.is_dir():
                diagnostic["directory_validation"]["error"] = f"Path exists but is not a directory: {resolved_path}"
                diagnostic["recommendations"].append(f"'{directory}' is a file, not a directory")
                return diagnostic
                
            # Step 2: Directory validation
            diagnostic["directory_validation"]["status"] = "valid"
            diagnostic["directory_validation"]["permissions"] = {
                "readable": os.access(resolved_path, os.R_OK),
                "writable": os.access(resolved_path, os.W_OK),
                "executable": os.access(resolved_path, os.X_OK)
            }
            
        except Exception as e:
            diagnostic["path_resolution"]["error"] = str(e)
            diagnostic["recommendations"].append(f"Path resolution failed: {e}")
            return diagnostic
        
        # Step 3: Content analysis
        try:
            files_by_extension = {}
            total_files = 0
            total_dirs = 0
            code_files = 0
            large_files = []
            
            # Common code file extensions
            code_extensions = {
                '.py', '.rs', '.js', '.jsx', '.ts', '.tsx', '.go', '.c', '.cpp', '.h', '.hpp',
                '.java', '.kt', '.swift', '.rb', '.php', '.lua', '.hs', '.ml', '.scala',
                '.clj', '.ex', '.erl', '.dart', '.zig'
            }
            
            for item in resolved_path.rglob("*"):
                if item.is_file():
                    total_files += 1
                    ext = item.suffix.lower()
                    files_by_extension[ext] = files_by_extension.get(ext, 0) + 1
                    
                    if ext in code_extensions:
                        code_files += 1
                    
                    try:
                        size = item.stat().st_size
                        if size > 100000:  # Files larger than 100KB
                            large_files.append((str(item.relative_to(resolved_path)), size))
                    except OSError:
                        pass
                        
                elif item.is_dir():
                    total_dirs += 1
            
            # Sort extensions by frequency
            sorted_extensions = sorted(files_by_extension.items(), key=lambda x: x[1], reverse=True)
            
            diagnostic["content_analysis"] = {
                "total_files": total_files,
                "total_directories": total_dirs,
                "code_files": code_files,
                "files_by_extension": dict(sorted_extensions[:20]),  # Top 20
                "largest_files": sorted(large_files, key=lambda x: x[1], reverse=True)[:10],
                "has_hidden_files": any(f.name.startswith('.') for f in resolved_path.iterdir() if f.is_file()),
                "depth": max((len(p.relative_to(resolved_path).parts) for p in resolved_path.rglob("*") if p.is_file()), default=0)
            }
            
        except Exception as e:
            diagnostic["content_analysis"]["error"] = str(e)
            diagnostic["recommendations"].append(f"Content analysis failed: {e}")
        
        # Step 4: Language detection analysis
        try:
            # Extension-based detection
            ext_to_lang = {
                ".py": "python", ".rs": "rust", ".js": "javascript", ".jsx": "javascript",
                ".ts": "typescript", ".tsx": "typescript", ".go": "go", ".c": "c",
                ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".java": "java",
                ".kt": "kotlin", ".swift": "swift", ".rb": "ruby", ".php": "php"
            }
            
            lang_counts = {}
            for ext, count in files_by_extension.items():
                if ext in ext_to_lang:
                    lang = ext_to_lang[ext]
                    lang_counts[lang] = lang_counts.get(lang, 0) + count
            
            primary_lang_by_files = max(lang_counts.items(), key=lambda x: x[1]) if lang_counts else (None, 0)
            
            diagnostic["language_detection"] = {
                "files_by_language": lang_counts,
                "primary_by_file_count": primary_lang_by_files[0],
                "primary_file_count": primary_lang_by_files[1],
                "confidence": primary_lang_by_files[1] / code_files if code_files > 0 else 0,
                "matches_expected": primary_lang_by_files[0] == expected_language if expected_language else None
            }
            
        except Exception as e:
            diagnostic["language_detection"]["error"] = str(e)
        
        # Step 5: Project type detection
        try:
            project_indicators = {
                "rust": ["Cargo.toml", "Cargo.lock", "src/main.rs", "src/lib.rs"],
                "python": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile", "__init__.py"],
                "javascript": ["package.json", "yarn.lock", "package-lock.json"],
                "typescript": ["tsconfig.json", "tslint.json"],
                "go": ["go.mod", "go.sum", "main.go"],
                "java": ["pom.xml", "build.gradle", "build.gradle.kts"]
            }
            
            detected_indicators = {}
            for project_type, indicators in project_indicators.items():
                found_indicators = []
                for indicator in indicators:
                    if (resolved_path / indicator).exists():
                        found_indicators.append(indicator)
                if found_indicators:
                    detected_indicators[project_type] = found_indicators
            
            primary_project_type = None
            if detected_indicators:
                # Score by number of indicators found
                scored = [(ptype, len(indicators)) for ptype, indicators in detected_indicators.items()]
                primary_project_type = max(scored, key=lambda x: x[1])[0]
            
            diagnostic["project_type_detection"] = {
                "indicators_found": detected_indicators,
                "primary_project_type": primary_project_type,
                "matches_expected": primary_project_type == expected_project_type if expected_project_type else None
            }
            
        except Exception as e:
            diagnostic["project_type_detection"]["error"] = str(e)
        
        # Step 6: Generate recommendations
        recommendations = []
        
        # Check if we're analyzing the right directory
        if expected_language and diagnostic["language_detection"].get("primary_by_file_count") == expected_language:
            recommendations.append("✓ Language detection is working correctly")
        elif expected_language:
            detected = diagnostic["language_detection"].get("primary_by_file_count")
            recommendations.append(f"⚠ Expected {expected_language} but detected {detected}")
            
            if detected is None:
                recommendations.append("No code files found - check if you're in the right directory")
            else:
                recommendations.append(f"Directory contains more {detected} files than {expected_language}")
        
        # Check project type
        if expected_project_type and diagnostic["project_type_detection"].get("primary_project_type") == expected_project_type:
            recommendations.append("✓ Project type detection is working correctly")
        elif expected_project_type:
            detected = diagnostic["project_type_detection"].get("primary_project_type")
            recommendations.append(f"⚠ Expected {expected_project_type} project but detected {detected}")
        
        # General recommendations
        if total_files == 0:
            recommendations.append("Directory is empty - check if you're in the right location")
        elif code_files == 0:
            recommendations.append("No code files found - this might not be a source code directory")
        elif total_files > 10000:
            recommendations.append("Very large directory - consider using more specific subdirectories")
        
        diagnostic["recommendations"] = recommendations
        
        return diagnostic
    
    @handle_errors  
    def validate_search_directory(self, directory: str, pattern: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that a search directory and parameters are correctly configured.
        
        Args:
            directory: Directory to search
            pattern: Search pattern to use
            language: Language to search for
            
        Returns:
            Validation results with suggestions
        """
        
        validation = {
            "directory_check": {},
            "pattern_check": {},
            "language_check": {},
            "recommendations": [],
            "ready_to_search": False
        }
        
        # Check directory
        dir_diagnostic = self.diagnose_directory_detection(directory, language)
        validation["directory_check"] = {
            "exists": dir_diagnostic["path_resolution"].get("exists", False),
            "is_directory": dir_diagnostic["path_resolution"].get("is_directory", False),
            "resolved_path": dir_diagnostic["path_resolution"].get("resolved", ""),
            "code_files_found": dir_diagnostic["content_analysis"].get("code_files", 0),
            "detected_language": dir_diagnostic["language_detection"].get("primary_by_file_count")
        }
        
        # Check pattern
        validation["pattern_check"] = {
            "pattern": pattern,
            "has_metavariables": "$" in pattern,
            "appears_valid": len(pattern.strip()) > 0,
            "complexity": "simple" if pattern.count("$") <= 2 else "complex"
        }
        
        # Check language compatibility
        detected_lang = validation["directory_check"]["detected_language"]
        validation["language_check"] = {
            "specified_language": language,
            "detected_language": detected_lang,
            "language_match": language == detected_lang if language and detected_lang else None,
            "auto_detect_available": detected_lang is not None
        }
        
        # Generate recommendations
        if not validation["directory_check"]["exists"]:
            validation["recommendations"].append("Directory does not exist - check the path")
        elif not validation["directory_check"]["is_directory"]:
            validation["recommendations"].append("Path exists but is not a directory")
        elif validation["directory_check"]["code_files_found"] == 0:
            validation["recommendations"].append("No code files found in directory")
        else:
            validation["recommendations"].append("Directory validation passed")
        
        if not validation["pattern_check"]["appears_valid"]:
            validation["recommendations"].append("Pattern appears to be empty or invalid")
        elif not validation["pattern_check"]["has_metavariables"]:
            validation["recommendations"].append("Pattern has no metavariables - might be too literal")
        else:
            validation["recommendations"].append("Pattern appears valid")
        
        if language and not validation["language_check"]["language_match"]:
            validation["recommendations"].append(f"Specified language '{language}' doesn't match detected '{detected_lang}'")
        elif not language and detected_lang:
            validation["recommendations"].append(f"No language specified - will auto-detect as '{detected_lang}'")
        elif not detected_lang:
            validation["recommendations"].append("Could not auto-detect language - consider specifying explicitly")
        
        # Determine if ready to search
        validation["ready_to_search"] = (
            validation["directory_check"]["exists"] and
            validation["directory_check"]["is_directory"] and
            validation["directory_check"]["code_files_found"] > 0 and
            validation["pattern_check"]["appears_valid"]
        )
        
        if validation["ready_to_search"]:
            validation["recommendations"].append("✓ Ready to search!")
        else:
            validation["recommendations"].append("❌ Not ready to search - address issues above")
        
        return validation