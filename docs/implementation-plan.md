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

## Phase 8 – Extended Language Support (🕐 ongoing)
1. 🛠️  Template handler generator script (`uv run python scripts/new_language.py rust`).  
2. 🛠️  Add at least **C**, **Go** & **Rust** handlers.
3. ✅  Unit tests for default patterns returned by each handler.

---

## Phase 9 – UV & Packaging Polish (🕐 <1 day)
1. 🛠️  Fill out `[project]` & `[build-system]` in `pyproject.toml`.  
2. 🛠️  Add `hatchling` build backend and scripts section.  
3. ✅  `uv pip install -e .` succeeds; `python -m ast_grep_mcp` entrypoint works.

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