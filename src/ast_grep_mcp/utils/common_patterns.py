"""
Common pattern library for frequently used AST patterns.

This module provides pre-built, tested patterns for common code analysis tasks,
addressing the complexity of manually constructing AST patterns.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class PatternCategory(Enum):
    """Categories of common patterns."""
    FUNCTIONS = "functions"
    ERROR_HANDLING = "error_handling"
    ASYNC_CODE = "async_code"
    TESTING = "testing"
    SECURITY = "security"
    REFACTORING = "refactoring"
    IMPORTS = "imports"
    LOGGING = "logging"


@dataclass
class CommonPattern:
    """Represents a common pattern with metadata."""
    name: str
    pattern: str
    description: str
    category: PatternCategory
    examples: List[str]
    variations: Optional[List[str]] = None
    notes: Optional[str] = None


class CommonPatternLibrary:
    """Library of common patterns for different languages."""
    
    @staticmethod
    def rust_patterns() -> Dict[str, List[CommonPattern]]:
        """Get common patterns for Rust."""
        return {
            PatternCategory.FUNCTIONS: [
                CommonPattern(
                    name="async_functions",
                    pattern="async fn $NAME",
                    description="Find all async function definitions",
                    category=PatternCategory.FUNCTIONS,
                    examples=["async fn process_data() { }", "pub async fn handler() -> Result<()>"],
                    variations=[
                        "pub async fn $NAME",
                        "async fn $NAME($$$PARAMS)",
                        "async fn $NAME($$$PARAMS) -> $RET"
                    ],
                    notes="Use variations for more specific matches"
                ),
                CommonPattern(
                    name="test_functions",
                    pattern="#[test]",
                    description="Find all test functions",
                    category=PatternCategory.FUNCTIONS,
                    examples=["#[test]\nfn test_something() { }"],
                    variations=["#[tokio::test]", "#[test]\nasync fn $NAME"]
                ),
                CommonPattern(
                    name="pub_functions",
                    pattern="pub fn $NAME",
                    description="Find all public functions",
                    category=PatternCategory.FUNCTIONS,
                    examples=["pub fn new() -> Self { }", "pub fn process(data: &str) { }"],
                    variations=["pub fn $NAME($$$PARAMS)", "pub fn $NAME($$$PARAMS) -> $RET"]
                ),
            ],
            PatternCategory.ERROR_HANDLING: [
                CommonPattern(
                    name="unwrap_calls",
                    pattern="unwrap()",
                    description="Find all unwrap() calls",
                    category=PatternCategory.ERROR_HANDLING,
                    examples=["result.unwrap()", "option.unwrap()"],
                    variations=[
                        "$VAR.unwrap()",
                        ".unwrap()",
                        "unwrap_or($DEFAULT)"
                    ],
                    notes="Simple pattern without metavariable works best"
                ),
                CommonPattern(
                    name="expect_calls",
                    pattern="expect($MSG)",
                    description="Find all expect() calls",
                    category=PatternCategory.ERROR_HANDLING,
                    examples=['result.expect("failed to parse")', 'opt.expect("value required")'],
                    variations=[".expect($MSG)", "$VAR.expect($MSG)"]
                ),
                CommonPattern(
                    name="question_mark",
                    pattern="$EXPR?",
                    description="Find all uses of ? operator",
                    category=PatternCategory.ERROR_HANDLING,
                    examples=["file.read_to_string(&mut contents)?", "parse_config()?"],
                    notes="Matches any expression followed by ?"
                ),
                CommonPattern(
                    name="panic_calls",
                    pattern="panic!($$$ARGS)",
                    description="Find all panic! macro calls",
                    category=PatternCategory.ERROR_HANDLING,
                    examples=['panic!("unexpected state")', 'panic!("error: {}", msg)']
                ),
            ],
            PatternCategory.ASYNC_CODE: [
                CommonPattern(
                    name="spawn_calls",
                    pattern="spawn($$$ARGS)",
                    description="Find all spawn calls (tokio or async-std)",
                    category=PatternCategory.ASYNC_CODE,
                    examples=["tokio::spawn(async { })", "spawn(async move { })"],
                    variations=[
                        "tokio::spawn($$$ARGS)",
                        "spawn(async move { $$$BODY })",
                        "spawn(async { $$$BODY })"
                    ]
                ),
                CommonPattern(
                    name="await_calls",
                    pattern=".await",
                    description="Find all .await expressions",
                    category=PatternCategory.ASYNC_CODE,
                    examples=["future.await", "async_function().await"],
                    variations=["$EXPR.await", "$EXPR.await?"]
                ),
                CommonPattern(
                    name="async_blocks",
                    pattern="async { $$$BODY }",
                    description="Find all async blocks",
                    category=PatternCategory.ASYNC_CODE,
                    examples=["async { do_work().await }", "async move { capture_var }"],
                    variations=["async move { $$$BODY }"]
                ),
            ],
            PatternCategory.SECURITY: [
                CommonPattern(
                    name="unsafe_blocks",
                    pattern="unsafe { $$$BODY }",
                    description="Find all unsafe blocks",
                    category=PatternCategory.SECURITY,
                    examples=["unsafe { *ptr }", "unsafe { transmute(value) }"]
                ),
                CommonPattern(
                    name="unsafe_functions",
                    pattern="unsafe fn $NAME",
                    description="Find all unsafe function definitions",
                    category=PatternCategory.SECURITY,
                    examples=["unsafe fn dangerous_operation() { }"],
                    variations=["pub unsafe fn $NAME", "unsafe fn $NAME($$$PARAMS)"]
                ),
            ],
            PatternCategory.LOGGING: [
                CommonPattern(
                    name="log_info",
                    pattern="log::info!($$$ARGS)",
                    description="Find all log::info! calls",
                    category=PatternCategory.LOGGING,
                    examples=['log::info!("Starting server")', 'log::info!("User {}: logged in", id)'],
                    variations=["info!($$$ARGS)", "tracing::info!($$$ARGS)"]
                ),
                CommonPattern(
                    name="println_calls",
                    pattern="println!($$$ARGS)",
                    description="Find all println! calls (often should be replaced with logging)",
                    category=PatternCategory.LOGGING,
                    examples=['println!("Debug: {}", value)', 'println!("Hello, world!")']
                ),
            ],
        }
    
    @staticmethod
    def javascript_patterns() -> Dict[str, List[CommonPattern]]:
        """Get common patterns for JavaScript/TypeScript."""
        return {
            PatternCategory.FUNCTIONS: [
                CommonPattern(
                    name="async_functions",
                    pattern="async function $NAME",
                    description="Find all async function declarations",
                    category=PatternCategory.FUNCTIONS,
                    examples=["async function fetchData() { }", "async function processUser(id) { }"],
                    variations=[
                        "async function $NAME($$$PARAMS)",
                        "const $NAME = async ($$$PARAMS) => $$$BODY",
                        "async ($$$PARAMS) => $$$BODY"
                    ]
                ),
                CommonPattern(
                    name="arrow_functions",
                    pattern="($$$PARAMS) => $BODY",
                    description="Find arrow function expressions",
                    category=PatternCategory.FUNCTIONS,
                    examples=["(x) => x * 2", "(a, b) => a + b"],
                    variations=[
                        "const $NAME = ($$$PARAMS) => $BODY",
                        "$VAR => $BODY",
                        "async ($$$PARAMS) => $BODY"
                    ]
                ),
            ],
            PatternCategory.ERROR_HANDLING: [
                CommonPattern(
                    name="try_catch",
                    pattern="try { $$$TRY } catch ($ERR) { $$$CATCH }",
                    description="Find all try-catch blocks",
                    category=PatternCategory.ERROR_HANDLING,
                    examples=["try { await fetch(url) } catch (e) { console.error(e) }"]
                ),
                CommonPattern(
                    name="promise_catch",
                    pattern=".catch($$$ARGS)",
                    description="Find all .catch() calls on promises",
                    category=PatternCategory.ERROR_HANDLING,
                    examples=["promise.catch(err => console.error(err))", "fetchData().catch(handleError)"],
                    variations=["$PROMISE.catch($$$ARGS)"]
                ),
            ],
            PatternCategory.ASYNC_CODE: [
                CommonPattern(
                    name="await_expressions",
                    pattern="await $EXPR",
                    description="Find all await expressions",
                    category=PatternCategory.ASYNC_CODE,
                    examples=["await fetchUser(id)", "const data = await response.json()"]
                ),
                CommonPattern(
                    name="promise_all",
                    pattern="Promise.all($$$ARGS)",
                    description="Find all Promise.all calls",
                    category=PatternCategory.ASYNC_CODE,
                    examples=["Promise.all([promise1, promise2])", "await Promise.all(promises)"]
                ),
            ],
            PatternCategory.LOGGING: [
                CommonPattern(
                    name="console_log",
                    pattern="console.log($$$ARGS)",
                    description="Find all console.log calls",
                    category=PatternCategory.LOGGING,
                    examples=['console.log("Debug:", value)', 'console.log(data)']
                ),
                CommonPattern(
                    name="console_error",
                    pattern="console.error($$$ARGS)",
                    description="Find all console.error calls",
                    category=PatternCategory.LOGGING,
                    examples=['console.error("Error:", err)', 'console.error(exception)']
                ),
            ],
        }
    
    @staticmethod
    def python_patterns() -> Dict[str, List[CommonPattern]]:
        """Get common patterns for Python."""
        return {
            PatternCategory.FUNCTIONS: [
                CommonPattern(
                    name="async_functions",
                    pattern="async def $NAME",
                    description="Find all async function definitions",
                    category=PatternCategory.FUNCTIONS,
                    examples=["async def fetch_data():", "async def process_request(req):"],
                    variations=[
                        "async def $NAME($$$PARAMS):",
                        "async def $NAME($$$PARAMS) -> $RET:"
                    ]
                ),
                CommonPattern(
                    name="decorated_functions",
                    pattern="@$DECORATOR\ndef $NAME",
                    description="Find all decorated functions",
                    category=PatternCategory.FUNCTIONS,
                    examples=["@property\ndef name(self):", "@staticmethod\ndef validate():"],
                    variations=["@$DECORATOR\nasync def $NAME"]
                ),
            ],
            PatternCategory.ERROR_HANDLING: [
                CommonPattern(
                    name="try_except",
                    pattern="try:\n    $$$TRY\nexcept $EXCEPTION:\n    $$$EXCEPT",
                    description="Find all try-except blocks",
                    category=PatternCategory.ERROR_HANDLING,
                    examples=["try:\n    risky_op()\nexcept ValueError:\n    handle_error()"]
                ),
                CommonPattern(
                    name="raise_statements",
                    pattern="raise $EXCEPTION",
                    description="Find all raise statements",
                    category=PatternCategory.ERROR_HANDLING,
                    examples=["raise ValueError('Invalid input')", "raise"]
                ),
            ],
            PatternCategory.LOGGING: [
                CommonPattern(
                    name="logging_info",
                    pattern="logging.info($$$ARGS)",
                    description="Find all logging.info calls",
                    category=PatternCategory.LOGGING,
                    examples=['logging.info("Processing started")', 'logging.info("User %s logged in", username)'],
                    variations=["logger.info($$$ARGS)", "log.info($$$ARGS)"]
                ),
                CommonPattern(
                    name="print_statements",
                    pattern="print($$$ARGS)",
                    description="Find all print statements",
                    category=PatternCategory.LOGGING,
                    examples=['print("Debug:", value)', 'print(f"Result: {result}")']
                ),
            ],
        }
    
    @classmethod
    def get_patterns(cls, language: str, category: Optional[PatternCategory] = None) -> List[CommonPattern]:
        """
        Get patterns for a specific language and optional category.
        
        Args:
            language: Programming language
            category: Optional category filter
            
        Returns:
            List of common patterns
        """
        # Get patterns for language
        pattern_getters = {
            "rust": cls.rust_patterns,
            "javascript": cls.javascript_patterns,
            "typescript": cls.javascript_patterns,  # Share JS patterns
            "python": cls.python_patterns,
        }
        
        getter = pattern_getters.get(language)
        if not getter:
            return []
        
        all_patterns = getter()
        
        # Filter by category if specified
        if category:
            return all_patterns.get(category, [])
        
        # Return all patterns flattened
        result = []
        for patterns in all_patterns.values():
            result.extend(patterns)
        return result
    
    @classmethod
    def find_pattern_by_name(cls, language: str, name: str) -> Optional[CommonPattern]:
        """Find a specific pattern by name."""
        all_patterns = cls.get_patterns(language)
        for pattern in all_patterns:
            if pattern.name == name:
                return pattern
        return None
    
    @classmethod
    def search_patterns(cls, language: str, query: str) -> List[CommonPattern]:
        """Search patterns by name or description."""
        all_patterns = cls.get_patterns(language)
        query_lower = query.lower()
        
        results = []
        for pattern in all_patterns:
            if (query_lower in pattern.name.lower() or 
                query_lower in pattern.description.lower()):
                results.append(pattern)
        
        return results


class PatternRecommender:
    """Recommends patterns based on natural language queries."""
    
    # Keywords mapped to pattern names
    KEYWORD_MAP = {
        "rust": {
            # Functions
            "async function": ["async_functions"],
            "async fn": ["async_functions"],
            "test": ["test_functions"],
            "tests": ["test_functions"],
            "public function": ["pub_functions"],
            "pub fn": ["pub_functions"],
            
            # Error handling
            "unwrap": ["unwrap_calls"],
            "expect": ["expect_calls"],
            "error handling": ["unwrap_calls", "expect_calls", "question_mark"],
            "?": ["question_mark"],
            "panic": ["panic_calls"],
            
            # Async
            "spawn": ["spawn_calls"],
            "tokio spawn": ["spawn_calls"],
            "await": ["await_calls"],
            "async block": ["async_blocks"],
            
            # Security
            "unsafe": ["unsafe_blocks", "unsafe_functions"],
            
            # Logging
            "log": ["log_info"],
            "logging": ["log_info"],
            "println": ["println_calls"],
            "print": ["println_calls"],
        },
        "javascript": {
            "async function": ["async_functions"],
            "arrow function": ["arrow_functions"],
            "=>": ["arrow_functions"],
            "try catch": ["try_catch"],
            "catch": ["try_catch", "promise_catch"],
            "await": ["await_expressions"],
            "promise.all": ["promise_all"],
            "console.log": ["console_log"],
            "console": ["console_log", "console_error"],
        },
        "python": {
            "async def": ["async_functions"],
            "decorator": ["decorated_functions"],
            "@": ["decorated_functions"],
            "try except": ["try_except"],
            "raise": ["raise_statements"],
            "logging": ["logging_info"],
            "print": ["print_statements"],
        }
    }
    
    @classmethod
    def recommend_patterns(cls, language: str, query: str) -> List[CommonPattern]:
        """
        Recommend patterns based on a natural language query.
        
        Args:
            language: Programming language
            query: Natural language query
            
        Returns:
            List of recommended patterns
        """
        query_lower = query.lower()
        keyword_map = cls.KEYWORD_MAP.get(language, {})
        
        recommended_names = set()
        
        # Check each keyword
        for keyword, pattern_names in keyword_map.items():
            if keyword in query_lower:
                recommended_names.update(pattern_names)
        
        # Get the actual patterns
        library = CommonPatternLibrary()
        patterns = []
        
        for name in recommended_names:
            pattern = library.find_pattern_by_name(language, name)
            if pattern:
                patterns.append(pattern)
        
        # If no specific recommendations, do a general search
        if not patterns:
            patterns = library.search_patterns(language, query)
        
        return patterns