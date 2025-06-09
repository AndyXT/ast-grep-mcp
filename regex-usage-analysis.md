# Regex Usage Analysis in ast-grep-mcp

## Summary

This analysis identifies regex usage in the `src/ast_grep_mcp` directory to determine which uses are necessary versus which could potentially be replaced with AST-grep API.

## Files Using Regex

1. **ast_analyzer.py** - Heavy regex usage
2. **core/ast_grep_mcp.py** - Imports re module
3. **ast_analyzer_v2.py** - Imports re module
4. **utils/error_handling.py** - Imports re module
5. **utils/error_codes.py** - Imports re module
6. **utils/pattern_simplifier.py** - Pattern analysis
7. **utils/pattern_suggestions.py** - Pattern matching
8. **utils/pattern_diagnostics.py** - Pattern validation
9. **utils/pattern_autocorrect.py** - Pattern correction
10. **utils/security.py** - Security checks
11. **utils/native_metavars.py** - Metavariable extraction
12. **utils/benchmarks.py** - Performance testing
13. **utils/pattern_helpers.py** - Pattern utilities
14. **utils/ignore_handler.py** - File filtering

## Regex Uses by Category

### 1. **NECESSARY - Pattern String Parsing & Validation**

These regex uses are necessary because they parse and validate AST-grep pattern strings themselves:

#### In `pattern_diagnostics.py`:
- Extracting metavariable names from patterns: `r"\$(\${0,2})?(\w*)"`
- Validating metavariable syntax: `r"(?<!\$)\$\$(\w+)"`
- Pattern syntax validation: checking for balanced brackets, valid metavariables

#### In `native_metavars.py`:
- Extracting single metavars: `r'(?<!\$)\$([A-Z][A-Z0-9_]*)(?!\$)'`
- Extracting multi metavars: `r'\$\$\$([A-Z][A-Z0-9_]*)'`
- Finding double-dollar variables: `r'(?<!\$)\$\$([A-Z][A-Z0-9_]*)(?!\$)'`

#### In `pattern_helpers.py`:
- Finding metavariables in patterns: `r"\$(\${0,2}\w+)"`
- Validating pattern syntax elements

### 2. **NECESSARY - Error Detection & Correction**

These regex uses are for detecting and correcting common errors in pattern strings:

#### In `pattern_autocorrect.py`:
- Fixing double dollar to triple: `r"(?<!\$)\$\$(\w+)"`
- Removing spaces after dollar: `r"\$\s+(\w+)"`
- Fixing typos: `r"\bfucntion\b"` → "function"
- Fixing template literal syntax: `r"'([^']*)\$\{([^}]+)\}([^']*)'"` → backticks

#### In `pattern_diagnostics.py`:
- Detecting missing dollar signs: `r"(?<![a-zA-Z])(FUNC|NAME|TYPE|VAR|ARG|PARAM|BODY|EXPR|VALUE|MSG)(?![a-zA-Z_0-9:(){}=])"`
- Finding unclosed brackets: `r"(\{[^}]*$|\[[^\]]*$|\([^)]*$)"`

### 3. **NECESSARY - Security & Validation**

#### In `security.py`:
- Detecting JavaScript template literals: `r"`(.*?\$\{.*?\}.*?)`"`
- Finding bitwise OR patterns: `r"\b\w+\s+\|\s+\w+(?:\s+\|\s+\w+)*\b"`

### 4. **COULD BE REPLACED - Code Analysis**

These regex uses analyze actual code content and could potentially be replaced with AST-grep API:

#### In `ast_analyzer.py` - Metavariable Value Extraction:
The file contains extensive regex usage for extracting metavariable values from matched code. Examples:
- Function names: `r"function\s+([A-Za-z0-9_]+)"`
- Parameters: `r"\(([^)]*)\)"`
- Return statements: `r"return\s+(.*?);"`
- Template literals: `r"'([^']*?)'\s*\+\s*([A-Za-z0-9_]+)\s*\+\s*'([^']*?)'"`
- JSX content: `r"<[^>]*>(.*)</[^>]*>"`
- Interface names: `r"interface\s+([A-Za-z0-9_]+)"`

**These could be replaced with AST-grep's native metavariable capture API** as shown in `native_metavars.py`.

#### In `ast_analyzer.py` - JavaScript/TypeScript Fix-ups:
The `_fix_js_malformed_output` method uses regex to fix malformed refactoring output:
- Fixing template interpolations: `r'"\${([^}]+)}"'`
- Fixing arrow function spacing: `r"(\)) =>(\{|\s*[^\s{])"`
- Extracting function/interface details for substitution

**These could potentially use AST-grep to properly parse and reconstruct the code instead of regex-based string manipulation.**

### 5. **NECESSARY - Pattern Complexity Analysis**

#### In `pattern_simplifier.py`:
- Detecting complex patterns: `r'\$\w+.*\$\$\$\w+.*\$\$\$\w+'`
- Finding nested structures: `r'\{[^}]*\{[^}]*\}[^}]*\}'`
- Counting metavariables: `r'\$+\w+'`

## Recommendations

### Keep Regex For:
1. **Pattern string parsing and validation** - This is meta-level work on AST-grep patterns themselves
2. **Error detection and auto-correction** in pattern strings
3. **Security validation** of patterns
4. **Pattern complexity analysis**

### Replace with AST-grep API:
1. **Metavariable value extraction** in `ast_analyzer.py`:
   - Use `match.get_match()` and `match.get_multiple_matches()` as shown in `native_metavars.py`
   - This would be more reliable and handle edge cases better

2. **Code fix-up operations** in `_fix_js_malformed_output`:
   - Parse the refactored code with AST-grep
   - Use proper AST manipulation instead of regex substitution
   - This would prevent malformed output in the first place

### Migration Path:
1. The `native_metavars.py` already shows the correct approach using AST-grep's native API
2. Refactor `ast_analyzer.py` to use `NativeMetavarExtractor` instead of regex-based extraction
3. For code fix-ups, parse the output with AST-grep and properly reconstruct it

## Conclusion

Most regex usage in the codebase is **necessary and appropriate** for:
- Parsing and validating AST-grep pattern strings
- Pattern error detection and correction
- Security validation

However, the extensive regex usage in `ast_analyzer.py` for extracting metavariable values from matched code **should be replaced** with AST-grep's native API, which is already implemented in `native_metavars.py` but not fully utilized.