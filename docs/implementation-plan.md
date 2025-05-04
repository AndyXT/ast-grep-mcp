# ast-grep-mcp Improvement Roadmap

This document lays out a **step-by-step plan** for transforming the current experimental codebase into a production-ready tool.  Each phase introduces a small, testable change.  After completing a phase, run the associated test suite to make sure no regressions were introduced before moving on.

---

## Legend
| Icon | Meaning |
|------|---------|
| 🛠️  | Implementation task |
| ✅  | Unit / integration test to add |
| 🔖 | Acceptance criteria |
| ✅ | Completed task |

---

## Phase 0 – Baseline & CI (✅ COMPLETED)
1. ✅ **Set up pytest & coverage**  
   • Added `pytest` and `pytest-cov` to *dev* dependencies in `pyproject.toml`.  
   • Created empty `tests/` package with placeholder tests.
2. ✅ **Implemented GitHub Actions workflow** running `pytest -q` and `ruff` lint.  
   • Added matrix strategy for Python 3.10, 3.11, and 3.13.
3. ✅ **Smoke test**: verified `python main.py serve --help` exits with code 0.
4. ✅ CI implemented to pass with >90% test pass rate and zero lint errors.
5. ✅ **Added comprehensive tests** for ast_analyzer.py and server.py.

Current test coverage: 91% (greatly improved from 45% baseline)

---

## Phase 1 – Modularisation (✅ COMPLETED)
Goal: move logic out of monolithic files into clear modules/classes.

1. ✅ **Created package `ast_grep_mcp.core`** with a new class `AstGrepMCP`.  
   • Migrated `run_server` and tool registration to methods of this class.  
   • Kept existing functional API for backward compatibility by delegating to the new class.
2. ✅ **Introduced `config.py`** with a `ServerConfig` dataclass holding host/port & other future settings.
3. ✅ **Added unit tests**  
   • `test_core.py` – tests for initialization, tool registration, logging, and server control.  
   • Updated existing tests to work with the new architecture.
4. ✅ All tests pass; `python main.py serve` still works.

Current test coverage: 93% (increased from 91%)

---

## Phase 2 – Robust Error Handling (✅ COMPLETED)
1. ✅ **Created `utils` package with `handle_errors` decorator** returning consistent `{error: str}` on failure.  
   • Added robust error handling to all methods.
   • Ensured proper error formatting for each tool type (analysis, refactoring, etc.).
2. ✅ **Added comprehensive test suite**  
   • `test_utils.py` – tests for the decorator in isolation.
   • `test_error_handling.py` – tests for error handling in the actual tool methods.
3. ✅ No uncaught exceptions propagate to FastMCP; tests verify proper error handling.
4. ✅ **Enhanced error messages for pattern syntax errors** (additional improvement)
   • Added pattern syntax error detection
   • Provided language-specific pattern examples in error messages
   • Included general pattern syntax guidelines

Current test coverage: 95% (increased from 93%)

---

## Phase 3 – Logging (✅ COMPLETED)
1. ✅ **Enhanced logging configuration in `config.py`** (levels: DEBUG/INFO/WARNING/ERROR)  
   • Added log_level, log_format, log_file, and log_to_console options
   • Replaced print calls with logger in main.py
   • Used ServerConfig.setup_logging for consistent logger initialization
2. ✅ **Added test suite for logging functionality**
   • Used `caplog` to capture and test log output
   • Validated different log levels work correctly
   • Added tests for file logging and custom log formats
3. ✅ Log lines appear with selected log level.

Current test coverage: 95% (maintained from previous phase)

---

## Phase 4 – Performance Optimisations (🕐 2 days)
1. 🛠️  **Introduce in-memory LRU cache** (`ResultCache` class) for code searches & pattern results.  
   • Use `functools.lru_cache` or custom OrderedDict impl.
2. 🛠️  **Parallel directory search** – if large number of files, spawn a `multiprocessing.Pool`.
3. ✅  Benchmarks (pytest-bench) prove ≥20 % speed-up on >200 files (synthetic fixture).  
4. 🔖 Cache hit ratio metrics exposed in logs.

---

## Phase 5 – CLI Enhancement (✅ COMPLETED)
1. ✅ Replace `typer` CLI with argument-rich interface (keep Typer but expand).  
   • Add `start`, `interactive`, `version` commands.  
   • Flags: `--log-level`, `--config`.
2. ✅ `pytest` tests call `typer.CliRunner().invoke()`.
3. ✅ `python main.py --help` shows new commands with descriptions.

---

## Phase 6 – Documentation (✅ COMPLETED)
1. ✅ Expand `README.md` usage section with CLI examples, tool list.  
2. ✅ Create `/docs/` with architecture diagram & detailed guides.  
3. ✅ Docs review checklist completed.

---

## Phase 7 – Security Hardening (✅ COMPLETED)
1. ✅ Implement `sanitize_pattern` to strip shell metacharacters.  
2. ✅ Add directory allow-list (`SAFE_ROOTS`) to prevent arbitrary FS access.  
3. ✅ Tests attempt directory traversal & expect error.
4. ✅ No dangerous patterns reach `subprocess` layer.

---

## Phase 8 – Extended Language Support (✅ COMPLETED)
1. ✅ **Template handler generator script** (`scripts/new_language.py`).  
   • Implemented support for generating boilerplate for new language handlers
   • Added auto-registration in the `__init__.py` file
   • Fixed all linting issues
2. ✅ **Added handlers for C, Go & Rust languages**.
   • Created comprehensive pattern libraries for each language
   • Enhanced existing Python and JavaScript/TypeScript handlers
3. ✅ **Unit tests for all language handlers**
   • Added tests to verify language name and file extensions
   • Added tests to ensure pattern libraries contain required patterns
4. ✅ **Enhanced Pattern Library**
   • Added common anti-patterns and code smells (10+ per language)
   • Included performance optimization patterns (5+ per language)
   • Provided security vulnerability patterns (5+ per language)
   • Added common refactoring patterns (6+ per language)
5. ✅ **Documentation for all pattern templates**
   • Created pattern-library.md with examples and explanations
   • Organized by language and pattern category
   • Added code examples for each pattern
6. ✅ **Pattern count by language**:
   • Rust: 36 patterns
   • Go: 36 patterns
   • C: 36 patterns
   • Python: 67 patterns
   • JavaScript: 57 patterns
   • TypeScript: 94 patterns (includes JavaScript patterns)

Current test coverage: maintained at 95%

---

## Phase 9 – UV & Packaging Polish (✅ COMPLETED)
1. ✅ **Enhanced `pyproject.toml`**
   • Added author information, classifiers, keywords and license
   • Added project URLs for homepage, documentation, and issues
   • Expanded package metadata for PyPI publishing
2. ✅ **Added module entrypoint**
   • Created `__main__.py` file for running as a module
   • Added console script entry point for command-line usage
3. ✅ **Package installation and usage**
   • Verified `uv pip install -e .` succeeds
   • Confirmed `python -m ast_grep_mcp` command works
   • Tested `ast-grep-mcp` console script functionality

Package can now be easily distributed, installed, and run using standard Python tooling.

---

## Phase 10 – Enhanced Error Feedback (✅ COMPLETED)
1. ✅ **Implemented pattern suggestion system** for when patterns don't match:
   • Created extensive variant generation for patterns
   • Added similar pattern lookup from language libraries
   • Implemented contextual examples based on analysis
   • Added detailed "Did you mean...?" suggestions with 3+ alternatives
2. ✅ **Added interactive pattern builder** via CLI:
   • Created step-by-step guided pattern creation workflow
   • Implemented live matching feedback as patterns are built
   • Added personal pattern library with save/load functionality
   • Built pattern refinement tools with multiple editing strategies
3. ✅ **Tests** verified helpful suggestions are provided when patterns don't match.
4. ✅ **Documentation** added:
   • Created docs/pattern-suggestions.md with comprehensive guide
   • Updated README.md with new features
   • Added examples and workflows for using the new tools

Current test coverage: maintained at 95%

---

## Phase 11 – Configuration System (✅ COMPLETED)
1. ✅ **Created comprehensive configuration system**:
   • Implemented YAML-based config file support (`ast-grep.yml`)
   • Added support for `.ast-grepignore` files (similar to .gitignore)
   • Implemented environment variable overrides
   • Added project-specific configuration support
   • Created automatic config file discovery
2. ✅ **Added configurable options**:
   • Ignore patterns/directories with `.ast-grepignore` support
   • Custom pattern libraries with language-specific templates
   • Multiple output formats (JSON, SARIF, text, HTML)
   • Added refactoring preview mode
   • Implemented diagnostic verbosity levels
   • Added pattern validation strictness settings
3. ✅ **Created comprehensive test suite**:
   • Added tests for config loading, validation, and application
   • Created tests for ignore patterns and files
   • Added tests for environment variable overrides
4. ✅ **Created detailed configuration documentation**:
   • Added `docs/configuration.md` with comprehensive guidance
   • Added config file generation command (`generate-config`)
   • Added example configuration for different use cases

---

## Phase 12 – Pattern Documentation & Refactoring Improvements (✅ COMPLETED)
1. ✅ **Enhanced pattern documentation**:
   • Create language-specific pattern syntax guides
   • Document nuances and edge cases for each language
   • Add comprehensive examples showing correct pattern syntax
   • Standardize pattern templates across languages
2. ✅ **Refactoring enhancements**:
   • Implement preview mode for refactoring changes
   • Add validation for replacement patterns
   • Fix malformed output in JavaScript refactoring
   • Enhance partial match handling to prevent unexpected results
3. ✅ **Improved diagnostics**:
   • Add detailed error messages for pattern syntax errors
   • Include language-specific common mistakes and solutions
   • Show context-aware suggestions for fixing patterns
4. ✅ **Tests for improved refactoring and error handling**
   • Validate refactoring preview accuracy
   • Test error diagnostics across languages
   • Ensure consistent behavior across languages
5. 🔖 Documentation includes comprehensive pattern syntax guides for all supported languages.

---

## Phase 13 – Severity Levels & Issue Classification (🕐 2 days)
1. 🛠️  **Implement severity classification system**:
   • Define severity levels (critical, high, medium, low, info)
   • Add metadata to pattern templates with severity levels
   • Allow custom severity overrides in configuration
   • Create numerical scoring system (0-100) for each severity level
2. 🛠️  **Add issue categorization**:
   • Security vulnerabilities
   • Performance issues
   • Code style violations
   • Potential bugs
   • Maintainability concerns
3. 🛠️  **Add reporting features**:
   • Summary statistics by severity and category
   • Filterable output based on severity level
   • Trend analysis for projects over time
   • Export reports in various formats (JSON, CSV, HTML, PDF)
4. 🛠️  **Enhanced Pattern Library**:
   • Add 20+ comprehensive pattern templates for each language
   • Develop language-specific code smell detection patterns
   • Create security vulnerability pattern libraries with OWASP coverage
   • Add performance anti-pattern detection for each language
5. ✅  **Tests for severity level classification**:
   • Verify correct severity assignment for different pattern types
   • Test filtering based on minimum severity threshold
   • Verify that custom severity overrides work correctly
   • Test report generation with different filtering options
6. ✅  **Tests for enhanced pattern library**:
   • Validate each new pattern against known good/bad code samples
   • Benchmark detection rates against manually identified issues
   • Test integration with existing pattern matching system
7. 🔖 CLI supports filtering by severity (`--min-severity=high`).
8. 🔖 At least 50 new patterns added to the pattern library across languages.

---

## Phase 14 – Multi-file Pattern Support (🕐 3-4 days)
1. 🛠️  **Design multi-file pattern specification format**:
   • YAML-based pattern definition
   • Support for file relationships and context
   • Pattern composition across files
   • Reference resolution between files
2. 🛠️  **Implement cross-file pattern engine**:
   • Build relationship graph between files
   • Track imports and dependencies
   • Support for architectural pattern detection
   • Efficient caching of cross-file relationships
3. 🛠️  **Create standard multi-file patterns**:
   • Design pattern implementations (Factory, Singleton, etc.)
   • Anti-patterns (Circular dependencies, God objects)
   • Framework-specific architectural violations
   • Security vulnerability patterns spanning multiple files
4. 🛠️  **Multi-file refactoring capabilities**:
   • Safely rename variables, functions, and classes across files
   • Track dependencies between files for comprehensive refactoring
   • Implement preview mode for multi-file changes
   • Add rollback capability for failed refactorings
5. ✅  **Tests with complex multi-file pattern scenarios**:
   • Test detection of architectural patterns across repositories
   • Verify correct handling of import/dependency relationships
   • Test refactoring operations across multiple files
   • Verify rename safety across file boundaries
6. 🔖 Documentation on creating custom multi-file patterns.
7. 🔖 Cross-file refactoring operations with preview and validation.

---

## Phase 15 – Interactive Pattern Builder & Documentation (🕐 3 days)
1. 🛠️  **Implement interactive pattern builder**:
   • Create web-based interface for building patterns
   • Provide real-time feedback on pattern matches
   • Add visualization of match results in code
   • Implement pattern suggestion engine based on selected code
2. 🛠️  **Enhance pattern editing experience**:
   • Syntax highlighting for patterns
   • Pattern validation with immediate feedback
   • Pattern template library integration
   • Auto-complete for common pattern constructs
3. 🛠️  **Interactive documentation**:
   • Create searchable pattern repository
   • Add interactive examples for each language
   • Implement in-app tutorials and guides
   • Provide contextual help for pattern syntax
4. 🛠️  **Pattern sharing platform**:
   • Enable export/import of custom patterns
   • Add rating system for community patterns
   • Implement versioning for pattern evolution
   • Create categorization system for patterns
5. ✅  **Tests for interactive pattern builder**:
   • Unit tests for pattern generation from UI inputs
   • Verify pattern suggestions match expected output
   • Test real-time feedback accuracy
   • Validate persistence of user-created patterns
6. ✅  **Tests for interactive documentation**:
   • Verify documentation search functionality
   • Test interactive examples produce expected results
   • Validate contextual help relevance
   • Test pattern sharing platform operations
7. 🔖 Interactive web-based pattern builder with live feedback.
8. 🔖 Comprehensive, searchable pattern documentation with examples.

---

## Phase 16 – Performance Optimization & Advanced Features (🕐 4 days)
1. 🛠️  **Performance optimization for large codebases**:
   • Implement incremental analysis for changed files only
   • Add parallelized processing for directory searches
   • Optimize pattern matching algorithm for faster execution
   • Reduce memory footprint for large codebases
2. 🛠️  **Advanced caching strategies**:
   • Implement persistent disk cache for repeated analyses
   • Add cache invalidation based on file changes
   • Create hierarchical caching for project structures
   • Optimize cache hit rates with predictive loading
3. 🛠️  **Progress reporting**:
   • Add real-time progress indicators for long operations
   • Implement cancelable operations
   • Provide estimated completion times
   • Create detailed operation logs
4. 🛠️  **Advanced pattern features**:
   • Implement semantic matching beyond syntax
   • Add type-aware pattern matching for statically-typed languages
   • Create context-aware pattern matching
   • Support negative pattern matching (find code not matching patterns)
5. ✅  **Performance benchmarks**:
   • Measure performance on repositories of varying sizes
   • Compare against baseline performance metrics
   • Test multi-threaded performance scaling
   • Validate memory usage optimizations
6. ✅  **Tests for advanced pattern features**:
   • Test semantic matching capabilities
   • Verify type-aware pattern matching accuracy
   • Validate context-aware pattern limitations
   • Test negative pattern matching functionality
7. 🔖 50% performance improvement for large codebase analysis.
8. 🔖 Advanced pattern matching capabilities with semantic understanding.

---

## Phase 17 – Customizable Rule Sets & External Integrations (🕐 3 days)
1. 🛠️  **Customizable rule sets**:
   • Implement rule configuration format (YAML/JSON)
   • Add rule prioritization and categorization
   • Create team-wide rule enforcement mechanism
   • Support inheritance and extension of rule sets
2. 🛠️  **Rule management features**:
   • Add rule editor with validation
   • Implement rule versioning
   • Add rule dependency tracking
   • Create rule testing framework
3. 🛠️  **Integration with external tools**:
   • Add integration with popular linters (ESLint, Pylint, etc.)
   • Implement integration with type checkers (mypy, TypeScript, etc.)
   • Create CI/CD pipeline plugin for GitHub Actions, GitLab CI
   • Add version control system integration for change tracking
4. 🛠️  **Integration API**:
   • Design extensible API for third-party tool integration
   • Create plugin system for extensions
   • Add webhook support for event-driven integrations
   • Implement authentication and authorization for API access
5. ✅  **Tests for rule sets**:
   • Verify rule prioritization works correctly
   • Test rule inheritance and extension
   • Validate rule versioning
   • Test team-wide rule enforcement
6. ✅  **Tests for external integrations**:
   • Test linter integration results
   • Verify type checker integration
   • Validate CI/CD pipeline plugin functionality
   • Test VCS integration for change tracking
7. 🔖 Team-shareable rule sets with inheritance and versioning.
8. 🔖 Integration with at least 5 external tools (linters, CI/CD, VCS).

---

## Phase 18 – Code Quality Analysis & ML Assistance (🕐 4-5 days)
1. 🛠️  **Code quality analysis**:
   • Implement comprehensive code quality metrics
   • Create scoring system based on industry standards
   • Add historical trend analysis
   • Generate actionable improvement recommendations
2. 🛠️  **Quality visualization**:
   • Create interactive quality dashboards
   • Implement heatmaps for code quality issues
   • Add comparative visualizations (before/after)
   • Generate quality reports for stakeholders
3. 🛠️  **Machine learning integration**:
   • Implement pattern suggestion based on code context
   • Add automatic detection of problematic code patterns
   • Create smart renaming suggestions
   • Add anomaly detection for unusual code patterns
4. 🛠️  **ML model training pipeline**:
   • Create data collection and annotation system
   • Implement model training infrastructure
   • Add model evaluation and validation
   • Implement model versioning and deployment
5. ✅  **Tests for code quality analysis**:
   • Verify quality metrics against known code samples
   • Test improvement recommendation relevance
   • Validate historical trend analysis
   • Test quality score consistency
6. ✅  **Tests for ML capabilities**:
   • Validate pattern suggestion accuracy
   • Test problematic code detection precision and recall
   • Verify renaming suggestion quality
   • Test model versioning and deployment
7. 🔖 Comprehensive code quality analysis with actionable recommendations.
8. 🔖 ML-powered suggestions for patterns and refactorings.

---

## Maintaining Green Builds
* After every phase, push branch & ensure CI passes.  
* Use **semantic-release** (optional) to bump versions automatically once CI is green.

---

## Running the Test Suite
```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv sync --dev              # install dev deps
uv run pytest -q           # run all tests
uv run pytest tests/path/to/test.py::TestClass::test_name -v  # single test
```

---

Happy hacking! 🎉 