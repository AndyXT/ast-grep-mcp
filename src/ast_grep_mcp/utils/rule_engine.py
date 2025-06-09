"""
Rule-based analysis engine for ast-grep.

This module provides support for complex rule definitions using ast-grep's
native rule system, including pattern composition, constraints, and
YAML-based rule management.
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from ast_grep_py import SgRoot, SgNode

from .native_metavars import NativeMetavarExtractor


logger = logging.getLogger("ast_grep_mcp.rule_engine")


class RuleSeverity(Enum):
    """Severity levels for rules."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class RuleMatch:
    """Represents a match from a rule."""
    rule_id: str
    message: str
    severity: RuleSeverity
    file_path: Optional[str]
    matched_text: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    metavariables: Dict[str, str]
    fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "message": self.message, 
            "severity": self.severity.value,
            "file_path": self.file_path,
            "matched_text": self.matched_text,
            "location": {
                "start_line": self.start_line,
                "end_line": self.end_line,
                "start_column": self.start_column,
                "end_column": self.end_column
            },
            "metavariables": self.metavariables,
            "fix": self.fix
        }


@dataclass
class AstGrepRule:
    """Represents an ast-grep rule."""
    id: str
    message: str
    severity: RuleSeverity = RuleSeverity.WARNING
    language: Optional[str] = None
    rule: Dict[str, Any] = field(default_factory=dict)
    fix: Optional[str] = None
    note: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AstGrepRule":
        """Create rule from dictionary."""
        severity = RuleSeverity(data.get("severity", "warning"))
        return cls(
            id=data["id"],
            message=data["message"],
            severity=severity,
            language=data.get("language"),
            rule=data["rule"],
            fix=data.get("fix"),
            note=data.get("note"),
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML/JSON serialization."""
        result = {
            "id": self.id,
            "message": self.message,
            "severity": self.severity.value,
            "rule": self.rule
        }
        
        if self.language:
            result["language"] = self.language
        if self.fix:
            result["fix"] = self.fix
        if self.note:
            result["note"] = self.note
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result


class RuleEngine:
    """Engine for executing ast-grep rules."""
    
    def __init__(self):
        """Initialize the rule engine."""
        self.logger = logger
        self.metavar_extractor = NativeMetavarExtractor()
        self.rules: Dict[str, AstGrepRule] = {}
        
    def add_rule(self, rule: AstGrepRule) -> None:
        """Add a rule to the engine."""
        self.rules[rule.id] = rule
        self.logger.debug(f"Added rule: {rule.id}")
        
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the engine."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.logger.debug(f"Removed rule: {rule_id}")
            return True
        return False
        
    def load_rule_file(self, file_path: Union[str, Path]) -> List[str]:
        """
        Load rules from a YAML or JSON file.
        
        Args:
            file_path: Path to the rule file
            
        Returns:
            List of loaded rule IDs
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Rule file not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            elif file_path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Handle single rule or list of rules
        rules = data if isinstance(data, list) else [data]
        loaded_ids = []
        
        for rule_data in rules:
            rule = AstGrepRule.from_dict(rule_data)
            self.add_rule(rule)
            loaded_ids.append(rule.id)
            
        self.logger.info(f"Loaded {len(loaded_ids)} rules from {file_path}")
        return loaded_ids
        
    def execute_rule(
        self,
        rule: AstGrepRule,
        code: str,
        language: str,
        file_path: Optional[str] = None
    ) -> List[RuleMatch]:
        """
        Execute a single rule on code.
        
        Args:
            rule: The rule to execute
            code: Source code to analyze
            language: Programming language
            file_path: Optional file path for context
            
        Returns:
            List of rule matches
        """
        # Use rule's language if specified, otherwise use provided language
        lang = rule.language or language
        
        # Parse code
        root = SgRoot(code, lang)
        node = root.root()
        
        # Execute rule and find matches
        matches = self._execute_rule_query(node, rule.rule)
        
        # Convert to RuleMatch objects
        results = []
        for match in matches:
            match_range = match.range()
            
            # Extract metavariables if pattern was used
            metavariables = {}
            if "pattern" in rule.rule:
                metavariables = self.metavar_extractor.extract_metavariables(
                    match, rule.rule["pattern"]
                )
            
            # Apply fix if available
            fix = None
            if rule.fix and metavariables:
                fix = self.metavar_extractor.substitute_metavariables(
                    rule.fix, metavariables
                )
            
            # Create match object
            rule_match = RuleMatch(
                rule_id=rule.id,
                message=self._format_message(rule.message, metavariables),
                severity=rule.severity,
                file_path=file_path,
                matched_text=match.text(),
                start_line=match_range.start.line + 1,
                end_line=match_range.end.line + 1,
                start_column=match_range.start.column,
                end_column=match_range.end.column,
                metavariables=metavariables,
                fix=fix
            )
            results.append(rule_match)
            
        return results
        
    def _execute_rule_query(
        self,
        node: SgNode,
        rule_config: Dict[str, Any]
    ) -> List[SgNode]:
        """
        Execute a rule query and return matches.
        
        This handles the various rule types: pattern, kind, all, any, not, etc.
        """
        matches = []
        
        # Pattern matching
        if "pattern" in rule_config:
            pattern_matches = node.find_all(pattern=rule_config["pattern"])
            matches.extend(pattern_matches)
            
        # Kind matching (node type)
        elif "kind" in rule_config:
            kind_matches = self._find_by_kind(node, rule_config["kind"])
            matches.extend(kind_matches)
            
        # Composite rules
        elif "all" in rule_config:
            # All sub-rules must match
            matches = self._execute_all_rules(node, rule_config["all"])
            
        elif "any" in rule_config:
            # Any sub-rule can match
            matches = self._execute_any_rules(node, rule_config["any"])
            
        elif "not" in rule_config:
            # Negative matching
            matches = self._execute_not_rule(node, rule_config["not"])
        
        # Apply constraints if present
        if matches and any(key in rule_config for key in ["inside", "has", "follows", "precedes"]):
            matches = self._apply_constraints(matches, rule_config)
            
        return matches
        
    def _find_by_kind(self, node: SgNode, kind: str) -> List[SgNode]:
        """Find all nodes of a specific kind."""
        results = []
        
        def visit(n: SgNode):
            if n.kind() == kind:
                results.append(n)
            for child in n.children():
                visit(child)
                
        visit(node)
        return results
        
    def _execute_all_rules(
        self,
        node: SgNode,
        sub_rules: List[Dict[str, Any]]
    ) -> List[SgNode]:
        """Execute ALL rules - all must match the same node."""
        if not sub_rules:
            return []
            
        # Get matches from first rule
        result_set = set(self._execute_rule_query(node, sub_rules[0]))
        
        # Intersect with matches from remaining rules
        for sub_rule in sub_rules[1:]:
            sub_matches = set(self._execute_rule_query(node, sub_rule))
            result_set &= sub_matches
            
        return list(result_set)
        
    def _execute_any_rules(
        self,
        node: SgNode,
        sub_rules: List[Dict[str, Any]]
    ) -> List[SgNode]:
        """Execute ANY rules - any can match."""
        result_set = set()
        
        for sub_rule in sub_rules:
            sub_matches = self._execute_rule_query(node, sub_rule)
            result_set.update(sub_matches)
            
        return list(result_set)
        
    def _execute_not_rule(
        self,
        node: SgNode,
        not_rule: Dict[str, Any]
    ) -> List[SgNode]:
        """Execute NOT rule - find nodes that don't match."""
        # Get all nodes
        all_nodes = []
        
        def collect_all(n: SgNode):
            all_nodes.append(n)
            for child in n.children():
                collect_all(child)
                
        collect_all(node)
        
        # Get nodes that match the NOT rule
        excluded = set(self._execute_rule_query(node, not_rule))
        
        # Return nodes that don't match
        return [n for n in all_nodes if n not in excluded]
        
    def _apply_constraints(
        self,
        matches: List[SgNode],
        rule_config: Dict[str, Any]
    ) -> List[SgNode]:
        """Apply constraints to filter matches."""
        filtered = matches
        
        # Inside constraint
        if "inside" in rule_config:
            inside_config = rule_config["inside"]
            filtered = [m for m in filtered if self._check_inside(m, inside_config)]
            
        # Has constraint
        if "has" in rule_config:
            has_config = rule_config["has"]
            filtered = [m for m in filtered if self._check_has(m, has_config)]
            
        # Follows constraint
        if "follows" in rule_config:
            follows_config = rule_config["follows"]
            filtered = [m for m in filtered if self._check_follows(m, follows_config)]
            
        # Precedes constraint
        if "precedes" in rule_config:
            precedes_config = rule_config["precedes"]
            filtered = [m for m in filtered if self._check_precedes(m, precedes_config)]
            
        return filtered
        
    def _check_inside(self, node: SgNode, inside_config: Dict[str, Any]) -> bool:
        """Check if node is inside a pattern."""
        parent = node.parent()
        while parent:
            parent_matches = self._execute_rule_query(parent, inside_config)
            if parent_matches and parent in parent_matches:
                return True
            parent = parent.parent()
        return False
        
    def _check_has(self, node: SgNode, has_config: Dict[str, Any]) -> bool:
        """Check if node has a pattern inside it."""
        child_matches = self._execute_rule_query(node, has_config)
        return len(child_matches) > 0
        
    def _check_follows(self, node: SgNode, follows_config: Dict[str, Any]) -> bool:
        """Check if node follows a pattern."""
        # Use ast-grep's follows method
        if "pattern" in follows_config:
            return node.follows(pattern=follows_config["pattern"])
        return False
        
    def _check_precedes(self, node: SgNode, precedes_config: Dict[str, Any]) -> bool:
        """Check if node precedes a pattern."""
        # Use ast-grep's precedes method  
        if "pattern" in precedes_config:
            return node.precedes(pattern=precedes_config["pattern"])
        return False
        
    def _format_message(self, message: str, metavariables: Dict[str, str]) -> str:
        """Format message with metavariable values."""
        formatted = message
        for var_name, value in metavariables.items():
            # Handle both $VAR and {$VAR} formats
            formatted = formatted.replace(f"{{{var_name}}}", value)
            formatted = formatted.replace(var_name, value)
        return formatted
        
    def scan_code(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None,
        rule_ids: Optional[List[str]] = None,
        severities: Optional[List[RuleSeverity]] = None
    ) -> List[RuleMatch]:
        """
        Scan code with all loaded rules.
        
        Args:
            code: Source code to scan
            language: Programming language
            file_path: Optional file path
            rule_ids: Optional list of specific rule IDs to run
            severities: Optional list of severities to include
            
        Returns:
            List of all rule matches
        """
        all_matches = []
        
        # Filter rules
        rules_to_run = self.rules.values()
        
        if rule_ids:
            rules_to_run = [r for r in rules_to_run if r.id in rule_ids]
            
        if severities:
            rules_to_run = [r for r in rules_to_run if r.severity in severities]
            
        # Execute each rule
        for rule in rules_to_run:
            try:
                matches = self.execute_rule(rule, code, language, file_path)
                all_matches.extend(matches)
            except Exception as e:
                self.logger.error(f"Error executing rule {rule.id}: {e}")
                
        # Sort by line number
        all_matches.sort(key=lambda m: (m.start_line, m.start_column))
        
        return all_matches


def create_rule_from_pattern(
    rule_id: str,
    pattern: str,
    message: str,
    language: Optional[str] = None,
    severity: RuleSeverity = RuleSeverity.WARNING,
    fix: Optional[str] = None
) -> AstGrepRule:
    """
    Create a simple rule from a pattern.
    
    This is a convenience function for creating basic pattern-based rules.
    """
    return AstGrepRule(
        id=rule_id,
        message=message,
        severity=severity,
        language=language,
        rule={"pattern": pattern},
        fix=fix
    )


# Example usage
if __name__ == "__main__":
    # Create rule engine
    engine = RuleEngine()
    
    # Create a simple rule
    rule = create_rule_from_pattern(
        rule_id="no-console-log",
        pattern="console.log($$$ARGS)",
        message="Avoid using console.log in production code",
        language="javascript",
        severity=RuleSeverity.WARNING,
        fix="// console.log($$$ARGS) // TODO: Remove before production"
    )
    
    # Add rule to engine
    engine.add_rule(rule)
    
    # Test code
    test_code = """
    function test() {
        console.log("Debug message");
        console.error("Error message");
        return true;
    }
    """
    
    # Scan code
    matches = engine.scan_code(test_code, "javascript")
    
    # Print results
    for match in matches:
        print(f"Rule: {match.rule_id}")
        print(f"Message: {match.message}")
        print(f"Location: {match.start_line}:{match.start_column}")
        print(f"Text: {match.matched_text}")
        if match.fix:
            print(f"Fix: {match.fix}")
        print()