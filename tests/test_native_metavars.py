"""Tests for native metavariable extraction."""

from ast_grep_py import SgRoot

from src.ast_grep_mcp.utils.native_metavars import NativeMetavarExtractor


class TestNativeMetavarExtractor:
    """Test native metavariable extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = NativeMetavarExtractor()
    
    def test_extract_metavar_names(self):
        """Test extracting metavariable names from patterns."""
        # Single vars
        single, multi = self.extractor.extract_metavar_names("$NAME = $VALUE")
        assert single == {"NAME", "VALUE"}
        assert multi == set()
        
        # Multi vars
        single, multi = self.extractor.extract_metavar_names("function $NAME($$$PARAMS)")
        assert single == {"NAME"}
        assert multi == {"PARAMS"}
        
        # Mixed
        single, multi = self.extractor.extract_metavar_names(
            "def $NAME($$$PARAMS):\n    $$$BODY"
        )
        assert single == {"NAME"}
        assert multi == {"PARAMS", "BODY"}
        
        # Double dollar (should be treated as multi)
        single, multi = self.extractor.extract_metavar_names("$$ARGS")
        assert single == set()
        assert multi == {"ARGS"}
    
    def test_python_function_extraction(self):
        """Test extracting from Python functions."""
        code = """
def calculate_sum(a, b):
    result = a + b
    return result
"""
        root = SgRoot(code, "python")
        pattern = "def $NAME($$$PARAMS):\n    $$$BODY"
        matches = root.root().find_all(pattern=pattern)
        
        assert len(matches) == 1
        captures = self.extractor.extract_metavariables(matches[0], pattern)
        
        assert captures["$NAME"] == "calculate_sum"
        assert captures["$$$PARAMS"] == "a, b"
        assert "result = a + b" in captures["$$$BODY"]
        assert "return result" in captures["$$$BODY"]
    
    def test_javascript_function_extraction(self):
        """Test extracting from JavaScript functions."""
        code = """
function greet(name, message) {
    console.log(name + ": " + message);
    return true;
}
"""
        root = SgRoot(code, "javascript")
        pattern = "function $NAME($$$PARAMS) { $$$BODY }"
        matches = root.root().find_all(pattern=pattern)
        
        assert len(matches) == 1
        captures = self.extractor.extract_metavariables(matches[0], pattern)
        
        assert captures["$NAME"] == "greet"
        assert captures["$$$PARAMS"] == "name, message"
        assert "console.log" in captures["$$$BODY"]
        assert "return true" in captures["$$$BODY"]
    
    def test_arrow_function_extraction(self):
        """Test extracting from arrow functions."""
        code = "const add = (a, b) => a + b;"
        
        root = SgRoot(code, "javascript")
        pattern = "const $NAME = ($$$PARAMS) => $EXPR"
        matches = root.root().find_all(pattern=pattern)
        
        assert len(matches) == 1
        captures = self.extractor.extract_metavariables(matches[0], pattern)
        
        assert captures["$NAME"] == "add"
        assert captures["$$$PARAMS"] == "a, b"
        assert captures["$EXPR"] == "a + b"
    
    def test_class_extraction(self):
        """Test extracting from class definitions."""
        code = """
class Calculator {
    constructor(initial) {
        this.value = initial;
    }
    
    add(x) {
        this.value += x;
    }
}
"""
        root = SgRoot(code, "javascript")
        pattern = "class $NAME { $$$BODY }"
        matches = root.root().find_all(pattern=pattern)
        
        assert len(matches) == 1
        captures = self.extractor.extract_metavariables(matches[0], pattern)
        
        assert captures["$NAME"] == "Calculator"
        assert "constructor" in captures["$$$BODY"]
        assert "add" in captures["$$$BODY"]
    
    def test_substitution(self):
        """Test metavariable substitution."""
        captures = {
            "$NAME": "myFunc",
            "$$$PARAMS": "x, y, z",
            "$$$BODY": "return x + y + z;"
        }
        
        replacement = "const $NAME = ($$$PARAMS) => { $$$BODY }"
        result = self.extractor.substitute_metavariables(replacement, captures)
        
        assert result == "const myFunc = (x, y, z) => { return x + y + z; }"
    
    def test_no_matches(self):
        """Test when no metavariables match."""
        code = "let x = 5;"
        root = SgRoot(code, "javascript")
        pattern = "function $NAME() {}"
        matches = root.root().find_all(pattern=pattern)
        
        assert len(matches) == 0
    
    def test_nested_extraction(self):
        """Test extracting from nested structures."""
        code = """
if (condition) {
    doSomething();
    doAnother();
}
"""
        root = SgRoot(code, "javascript")
        pattern = "if ($COND) { $$$BODY }"
        matches = root.root().find_all(pattern=pattern)
        
        assert len(matches) == 1
        captures = self.extractor.extract_metavariables(matches[0], pattern)
        
        assert captures["$COND"] == "condition"
        assert "doSomething()" in captures["$$$BODY"]
        assert "doAnother()" in captures["$$$BODY"]
    
    def test_rust_match_extraction(self):
        """Test extracting from Rust match expressions."""
        code = """
match value {
    Some(x) => x * 2,
    None => 0,
}
"""
        root = SgRoot(code, "rust")
        pattern = "match $EXPR { $$$ARMS }"
        matches = root.root().find_all(pattern=pattern)
        
        assert len(matches) == 1
        captures = self.extractor.extract_metavariables(matches[0], pattern)
        
        assert captures["$EXPR"] == "value"
        assert "Some(x) => x * 2" in captures["$$$ARMS"]
        assert "None => 0" in captures["$$$ARMS"]
    
    def test_empty_metavariables(self):
        """Test extracting empty metavariables."""
        code = "function test() {}"
        root = SgRoot(code, "javascript")
        pattern = "function $NAME($$$PARAMS) { $$$BODY }"
        matches = root.root().find_all(pattern=pattern)
        
        assert len(matches) == 1
        captures = self.extractor.extract_metavariables(matches[0], pattern)
        
        assert captures["$NAME"] == "test"
        assert captures["$$$PARAMS"] == ""
        assert captures["$$$BODY"] == ""