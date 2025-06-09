"""
Pattern templates with examples for common refactoring scenarios.

This module provides pre-built pattern templates with examples
and variable explanations.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PatternTemplate:
    """Represents a pattern template with metadata."""
    
    name: str
    description: str
    pattern: str
    replacement: Optional[str]
    language: str
    example_matches: List[str]
    variables: Dict[str, str]
    category: str
    notes: Optional[str] = None
    confidence: float = 0.9


class PatternTemplateLibrary:
    """Library of pattern templates for common scenarios."""
    
    @staticmethod
    def rust_templates() -> Dict[str, PatternTemplate]:
        """Get Rust pattern templates."""
        return {
            "unwrap_to_expect": PatternTemplate(
                name="unwrap_to_expect",
                description="Convert unwrap() to expect() with message",
                pattern="$EXPR.unwrap()",
                replacement='$EXPR.expect("$MESSAGE")',
                language="rust",
                example_matches=[
                    "result.unwrap()",
                    "Some(value).unwrap()",
                    "file.read_to_string(&mut contents).unwrap()"
                ],
                variables={
                    "$EXPR": "Any expression that returns Result or Option",
                    "$MESSAGE": "Error message to use (user must provide)"
                },
                category="error_handling",
                notes="Requires user to provide meaningful error message"
            ),
            
            "unwrap_to_question_mark": PatternTemplate(
                name="unwrap_to_question_mark",
                description="Convert unwrap() to ? operator",
                pattern="$EXPR.unwrap()",
                replacement="$EXPR?",
                language="rust",
                example_matches=[
                    "file.read_to_string(&mut contents).unwrap()",
                    "parse_config().unwrap()"
                ],
                variables={
                    "$EXPR": "Any expression that returns Result"
                },
                category="error_handling",
                notes="Only works in functions that return Result"
            ),
            
            "match_to_if_let": PatternTemplate(
                name="match_to_if_let",
                description="Convert single-arm match to if let",
                pattern="match $EXPR { $PATTERN => $BODY, _ => {} }",
                replacement="if let $PATTERN = $EXPR { $BODY }",
                language="rust",
                example_matches=[
                    "match result { Some(x) => println!(\"{}\", x), _ => {} }",
                    "match event { Event::Click => handle_click(), _ => {} }"
                ],
                variables={
                    "$EXPR": "Expression being matched",
                    "$PATTERN": "Pattern to match",
                    "$BODY": "Code to execute on match"
                },
                category="refactoring"
            ),
            
            "println_to_log": PatternTemplate(
                name="println_to_log",
                description="Convert println! to proper logging",
                pattern='println!("$MESSAGE", $$$ARGS)',
                replacement='log::info!("$MESSAGE", $$$ARGS)',
                language="rust",
                example_matches=[
                    'println!("Server started")',
                    'println!("User {}: logged in", user_id)',
                    'println!("Error: {}", error)'
                ],
                variables={
                    "$MESSAGE": "The format string",
                    "$$$ARGS": "Format arguments (variadic)"
                },
                category="logging",
                notes="Requires log crate to be imported"
            ),
            
            "clone_in_loop": PatternTemplate(
                name="clone_in_loop",
                description="Detect cloning inside loops",
                pattern="for $ITEM in $ITER { $$$BODY $VAR.clone() $$$MORE }",
                replacement=None,  # Detection only
                language="rust",
                example_matches=[
                    "for item in items { process(data.clone()); }",
                    "for i in 0..10 { vec.push(string.clone()); }"
                ],
                variables={
                    "$ITEM": "Loop variable",
                    "$ITER": "Iterator",
                    "$VAR": "Variable being cloned",
                    "$$$BODY": "Code before clone",
                    "$$$MORE": "Code after clone"
                },
                category="performance",
                notes="Clone in loop may indicate performance issue"
            ),
            
            "vec_new_push": PatternTemplate(
                name="vec_new_push",
                description="Vec::new() followed by push",
                pattern="let mut $VAR = Vec::new(); $VAR.push($ITEM);",
                replacement="let mut $VAR = vec![$ITEM];",
                language="rust",
                example_matches=[
                    "let mut v = Vec::new(); v.push(1);",
                    "let mut items = Vec::new(); items.push(item);"
                ],
                variables={
                    "$VAR": "Variable name",
                    "$ITEM": "Item being pushed"
                },
                category="style"
            ),
            
            "async_block_spawn": PatternTemplate(
                name="async_block_spawn",
                description="Spawn async block patterns",
                pattern="spawn($$$ARGS)",
                replacement=None,
                language="rust",
                example_matches=[
                    "spawn(async { process().await })",
                    "spawn(async move { handle_request(req).await })",
                    "tokio::spawn(async { do_work() })"
                ],
                variables={
                    "$$$ARGS": "Arguments to spawn (usually async block)"
                },
                category="async",
                notes="General pattern that matches all spawn calls"
            )
        }
    
    @staticmethod
    def javascript_templates() -> Dict[str, PatternTemplate]:
        """Get JavaScript/TypeScript pattern templates."""
        return {
            "callback_to_promise": PatternTemplate(
                name="callback_to_promise",
                description="Convert callback to Promise",
                pattern="$FUNC($$$ARGS, function($ERR, $DATA) { $$$BODY })",
                replacement="new Promise((resolve, reject) => { $FUNC($$$ARGS, ($ERR, $DATA) => { if ($ERR) reject($ERR); else { $$$BODY } }) })",
                language="javascript",
                example_matches=[
                    "fs.readFile(path, function(err, data) { console.log(data); })",
                    "request(url, function(err, response) { handleResponse(response); })"
                ],
                variables={
                    "$FUNC": "Function name",
                    "$$$ARGS": "Function arguments",
                    "$ERR": "Error parameter",
                    "$DATA": "Data parameter",
                    "$$$BODY": "Callback body"
                },
                category="async"
            ),
            
            "var_to_const": PatternTemplate(
                name="var_to_const",
                description="Convert var to const",
                pattern="var $NAME = $VALUE;",
                replacement="const $NAME = $VALUE;",
                language="javascript",
                example_matches=[
                    "var API_KEY = 'abc123';",
                    "var config = { port: 3000 };"
                ],
                variables={
                    "$NAME": "Variable name",
                    "$VALUE": "Variable value"
                },
                category="modernization",
                notes="Only for variables that aren't reassigned"
            ),
            
            "console_to_logger": PatternTemplate(
                name="console_to_logger",
                description="Convert console.log to logger",
                pattern="console.log($$$ARGS)",
                replacement="logger.info($$$ARGS)",
                language="javascript",
                example_matches=[
                    "console.log('Server started');",
                    "console.log('User:', user, 'Action:', action);"
                ],
                variables={
                    "$$$ARGS": "Log arguments"
                },
                category="logging"
            ),
            
            "promise_then_to_async": PatternTemplate(
                name="promise_then_to_async",
                description="Convert promise.then to async/await",
                pattern="$PROMISE.then($FUNC)",
                replacement="await $PROMISE",
                language="javascript",
                example_matches=[
                    "fetchData().then(data => process(data))",
                    "api.get('/users').then(response => response.json())"
                ],
                variables={
                    "$PROMISE": "Promise expression",
                    "$FUNC": "Then callback"
                },
                category="async",
                notes="Must be inside async function"
            )
        }
    
    @staticmethod
    def python_templates() -> Dict[str, PatternTemplate]:
        """Get Python pattern templates."""
        return {
            "print_to_logging": PatternTemplate(
                name="print_to_logging",
                description="Convert print to logging",
                pattern="print($$$ARGS)",
                replacement="logging.info($$$ARGS)",
                language="python",
                example_matches=[
                    "print('Debug:', value)",
                    "print(f'User {user} logged in')"
                ],
                variables={
                    "$$$ARGS": "Print arguments"
                },
                category="logging"
            ),
            
            "dict_get_with_default": PatternTemplate(
                name="dict_get_with_default",
                description="Use dict.get() with default",
                pattern="if $KEY in $DICT: $VAR = $DICT[$KEY] else: $VAR = $DEFAULT",
                replacement="$VAR = $DICT.get($KEY, $DEFAULT)",
                language="python",
                example_matches=[
                    "if 'name' in data: name = data['name'] else: name = 'Unknown'"
                ],
                variables={
                    "$KEY": "Dictionary key",
                    "$DICT": "Dictionary",
                    "$VAR": "Variable name",
                    "$DEFAULT": "Default value"
                },
                category="pythonic"
            ),
            
            "list_comprehension": PatternTemplate(
                name="list_comprehension",
                description="Convert loop to list comprehension",
                pattern="$RESULT = []\nfor $ITEM in $ITER:\n    $RESULT.append($EXPR)",
                replacement="$RESULT = [$EXPR for $ITEM in $ITER]",
                language="python",
                example_matches=[
                    "result = []\nfor x in numbers:\n    result.append(x * 2)"
                ],
                variables={
                    "$RESULT": "Result list",
                    "$ITEM": "Loop variable",
                    "$ITER": "Iterable",
                    "$EXPR": "Expression to append"
                },
                category="pythonic"
            )
        }
    
    @classmethod
    def get_template(cls, name: str, language: str) -> Optional[PatternTemplate]:
        """Get a specific template by name and language."""
        templates = cls.get_all_templates(language)
        return templates.get(name)
    
    @classmethod
    def get_all_templates(cls, language: str) -> Dict[str, PatternTemplate]:
        """Get all templates for a language."""
        if language == "rust":
            return cls.rust_templates()
        elif language in ["javascript", "typescript"]:
            return cls.javascript_templates()
        elif language == "python":
            return cls.python_templates()
        return {}
    
    @classmethod
    def get_templates_by_category(
        cls, 
        language: str, 
        category: str
    ) -> List[PatternTemplate]:
        """Get templates filtered by category."""
        templates = cls.get_all_templates(language)
        return [
            t for t in templates.values() 
            if t.category == category
        ]
    
    @classmethod
    def suggest_templates_for_code(
        cls,
        code: str,
        language: str
    ) -> List[PatternTemplate]:
        """Suggest applicable templates based on code content."""
        templates = cls.get_all_templates(language)
        suggestions = []
        
        # Simple keyword-based matching
        code_lower = code.lower()
        
        for template in templates.values():
            # Check if pattern keywords appear in code
            pattern_keywords = set()
            
            # Extract keywords from pattern
            if language == "rust":
                if "unwrap()" in template.pattern:
                    pattern_keywords.add("unwrap")
                if "println!" in template.pattern:
                    pattern_keywords.add("println")
                if "match" in template.pattern:
                    pattern_keywords.add("match")
                if "Vec::new()" in template.pattern:
                    pattern_keywords.add("vec::new")
            
            elif language in ["javascript", "typescript"]:
                if "console.log" in template.pattern:
                    pattern_keywords.add("console.log")
                if "var " in template.pattern:
                    pattern_keywords.add("var ")
                if ".then(" in template.pattern:
                    pattern_keywords.add(".then")
            
            elif language == "python":
                if "print(" in template.pattern:
                    pattern_keywords.add("print(")
                
            # Check if any keywords match
            if any(keyword in code_lower for keyword in pattern_keywords):
                suggestions.append(template)
        
        return suggestions
    

def create_template_from_example(
    name: str,
    pattern_example: str,
    replacement_example: str,
    language: str,
    description: str = ""
) -> PatternTemplate:
    """
    Create a pattern template from before/after examples.
    
    Args:
        name: Template name
        pattern_example: Example of code to match
        replacement_example: Example of replacement
        language: Programming language
        description: Template description
        
    Returns:
        PatternTemplate created from examples
    """
    from .simple_pattern_builder import SimplePatternBuilder
    
    # Convert examples to patterns
    pattern = SimplePatternBuilder.from_example(pattern_example, language)
    replacement = SimplePatternBuilder.from_example(replacement_example, language)
    
    # Extract variables by comparing pattern and example
    variables = {}
    
    # Simple variable detection
    import re
    metavars = re.findall(r'\$\w+|\$\$\$\w+', pattern)
    for var in metavars:
        if "$$$" in var:
            variables[var] = "Multiple items (variadic)"
        else:
            variables[var] = "Single item"
    
    return PatternTemplate(
        name=name,
        description=description or f"Convert {name}",
        pattern=pattern,
        replacement=replacement,
        language=language,
        example_matches=[pattern_example],
        variables=variables,
        category="custom"
    )