"""
MCP tools for rule-based analysis.

This module provides MCP tool implementations for the rule engine.
"""

import json
from typing import Dict, Any, List, Optional

from ..utils.rule_engine import (
    RuleEngine,
    AstGrepRule,
    RuleSeverity,
    create_rule_from_pattern
)
from ..utils.error_handling import handle_errors


class RuleTools:
    """MCP tools for rule-based analysis."""
    
    def __init__(self):
        """Initialize rule tools."""
        self.rule_engine = RuleEngine()
        self.loaded_rule_files: Dict[str, List[str]] = {}
        
    @handle_errors
    def create_rule(
        self,
        rule_id: str,
        pattern: str,
        message: str,
        language: Optional[str] = None,
        severity: str = "warning",
        fix: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new rule from a pattern.
        
        Args:
            rule_id: Unique identifier for the rule
            pattern: AST pattern to match
            message: Message to display when rule matches
            language: Optional language constraint
            severity: Rule severity (error, warning, info, hint)
            fix: Optional fix pattern
            note: Optional note with more details
            
        Returns:
            Result with rule details
        """
        # Convert severity string to enum
        try:
            severity_enum = RuleSeverity(severity)
        except ValueError:
            return {
                "error": f"Invalid severity: {severity}. Must be one of: error, warning, info, hint"
            }
            
        # Create rule
        rule = create_rule_from_pattern(
            rule_id=rule_id,
            pattern=pattern,
            message=message,
            language=language,
            severity=severity_enum,
            fix=fix
        )
        
        if note:
            rule.note = note
            
        # Add to engine
        self.rule_engine.add_rule(rule)
        
        return {
            "success": True,
            "rule": rule.to_dict(),
            "message": f"Rule '{rule_id}' created successfully"
        }
        
    @handle_errors
    def load_rules(self, file_path: str) -> Dict[str, Any]:
        """
        Load rules from a YAML or JSON file.
        
        Args:
            file_path: Path to the rule file
            
        Returns:
            Result with loaded rule IDs
        """
        try:
            loaded_ids = self.rule_engine.load_rule_file(file_path)
            self.loaded_rule_files[file_path] = loaded_ids
            
            return {
                "success": True,
                "rule_ids": loaded_ids,
                "loaded_rules": loaded_ids,
                "count": len(loaded_ids),
                "message": f"Loaded {len(loaded_ids)} rules from {file_path}"
            }
        except Exception as e:
            return {
                "error": f"Failed to load rules: {str(e)}",
                "file_path": file_path
            }
            
    @handle_errors
    def run_rules(
        self,
        code: str,
        language: str,
        rule_ids: Optional[List[str]] = None,
        severities: Optional[List[str]] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run loaded rules against code.
        
        Args:
            code: Source code to analyze
            language: Programming language
            rule_ids: Optional list of specific rule IDs to run
            severities: Optional list of severities to include
            file_path: Optional file path for context
            
        Returns:
            Analysis results with rule matches
        """
        # Convert severity strings to enums
        severity_enums = None
        if severities:
            try:
                severity_enums = [RuleSeverity(s) for s in severities]
            except ValueError as e:
                return {"error": f"Invalid severity: {e}"}
                
        # Run rules
        matches = self.rule_engine.scan_code(
            code=code,
            language=language,
            file_path=file_path,
            rule_ids=rule_ids,
            severities=severity_enums
        )
        
        # Convert matches to dictionaries
        match_dicts = [match.to_dict() for match in matches]
        
        # Group by severity
        by_severity = {
            "error": [],
            "warning": [],
            "info": [],
            "hint": []
        }
        
        for match in match_dicts:
            by_severity[match["severity"]].append(match)
            
        return {
            "matches": match_dicts,
            "total_count": len(match_dicts),
            "by_severity": {
                sev: len(matches) for sev, matches in by_severity.items()
            },
            "errors": by_severity["error"],
            "warnings": by_severity["warning"],
            "info": by_severity["info"],
            "hints": by_severity["hint"]
        }
        
    @handle_errors
    def test_rule(
        self,
        rule_config: Dict[str, Any],
        test_code: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Test a rule configuration against sample code.
        
        Args:
            rule_config: Rule configuration dict
            test_code: Code to test against
            language: Programming language
            
        Returns:
            Test results with matches
        """
        # Create temporary rule
        try:
            rule = AstGrepRule.from_dict(rule_config)
        except Exception as e:
            return {"error": f"Invalid rule configuration: {e}"}
            
        # Execute rule
        matches = self.rule_engine.execute_rule(
            rule=rule,
            code=test_code,
            language=language
        )
        
        # Convert matches
        match_dicts = [match.to_dict() for match in matches]
        
        return {
            "rule_id": rule.id,
            "matches": match_dicts,
            "count": len(match_dicts),
            "test_passed": len(match_dicts) > 0 if rule_config.get("should_match", True) else len(match_dicts) == 0
        }
        
    @handle_errors
    def compose_rule(
        self,
        rule_id: str,
        message: str,
        sub_rules: List[Dict[str, Any]],
        operator: str = "all",
        language: Optional[str] = None,
        severity: str = "warning",
        fix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a composite rule using logical operators.
        
        Args:
            rule_id: Unique identifier
            message: Rule message
            sub_rules: List of sub-rule configurations
            operator: Logical operator (all, any, not)
            language: Optional language
            severity: Rule severity
            fix: Optional fix
            
        Returns:
            Result with created rule
        """
        if operator not in ["all", "any", "not"]:
            return {"error": f"Invalid operator: {operator}. Must be one of: all, any, not"}
            
        # Convert severity
        try:
            severity_enum = RuleSeverity(severity)
        except ValueError:
            return {"error": f"Invalid severity: {severity}"}
            
        # Build rule config
        rule_config = {operator: sub_rules}
        
        # Create rule
        rule = AstGrepRule(
            id=rule_id,
            message=message,
            severity=severity_enum,
            language=language,
            rule=rule_config,
            fix=fix
        )
        
        # Add to engine
        self.rule_engine.add_rule(rule)
        
        return {
            "success": True,
            "rule": rule.to_dict(),
            "message": f"Composite rule '{rule_id}' created successfully"
        }
        
    @handle_errors
    def list_rules(self) -> Dict[str, Any]:
        """
        List all loaded rules.
        
        Returns:
            List of rule summaries
        """
        rules = []
        for rule in self.rule_engine.rules.values():
            rules.append({
                "id": rule.id,
                "message": rule.message,
                "severity": rule.severity.value,
                "language": rule.language,
                "has_fix": rule.fix is not None
            })
            
        return {
            "rules": rules,
            "count": len(rules),
            "loaded_files": list(self.loaded_rule_files.keys())
        }
        
    @handle_errors
    def remove_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Remove a rule from the engine.
        
        Args:
            rule_id: ID of rule to remove
            
        Returns:
            Result of removal
        """
        if self.rule_engine.remove_rule(rule_id):
            # Update loaded files tracking
            for file_path, rule_ids in self.loaded_rule_files.items():
                if rule_id in rule_ids:
                    rule_ids.remove(rule_id)
                    
            return {
                "success": True,
                "message": f"Rule '{rule_id}' removed successfully"
            }
        else:
            return {
                "error": f"Rule '{rule_id}' not found"
            }
            
    @handle_errors
    def export_rules(self, output_format: str = "yaml") -> Dict[str, Any]:
        """
        Export all rules to YAML or JSON format.
        
        Args:
            output_format: Output format (yaml or json)
            
        Returns:
            Exported rules
        """
        if output_format not in ["yaml", "json"]:
            return {"error": "Format must be 'yaml' or 'json'"}
            
        rules = [rule.to_dict() for rule in self.rule_engine.rules.values()]
        
        if output_format == "json":
            return {
                "format": "json",
                "content": json.dumps(rules, indent=2),
                "rules": rules
            }
        else:
            # For YAML, we'll return the data structure
            # The actual YAML formatting would be done by the client
            return {
                "format": "yaml", 
                "rules": rules,
                "count": len(rules)
            }