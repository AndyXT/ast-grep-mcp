# ast-grep-mcp Improvement Roadmap

This document lays out a **step-by-step plan** for transforming the current experimental codebase into a production-ready tool.  Each phase introduces a small, testable change.  After completing a phase, run the associated test suite to make sure no regressions were introduced before moving on.

---

## Legend
| Icon | Meaning |
|------|---------|
| 🛠️  | Implementation task |
| ✅  | Unit / integration test to add |
| 🔖 | Acceptance criteria |

---

## Phase 0 – Baseline & CI (🕐 ~1 day)
1. 🛠️  **Set up pytest & coverage**  
   • Add `pytest` and `pytest-cov` to *dev* dependencies in `pyproject.toml`.  
   • Create empty `tests/` package with a placeholder test that imports the project.
2. 🛠️  **Implement GitHub Actions (or other) CI workflow** running `pytest -q` and `ruff` lint.  
   • Use Python 3.10 & 3.11 matrices.
3. ✅  **Smoke test**: ensure `python main.py serve --help` exits with code 0.
4. 🔖 CI must pass with >90 % test pass rate (only smoke test for now) and zero ruff errors.

---

## Phase 1 – Modularisation (🕐 ~1–2 days)
Goal: move logic out of monolithic files into clear modules/classes.

1. 🛠️  **Create package `ast_grep_mcp.core`** with a new class `AstGrepMCP`.  
   • Migrate `run_server` and tool registration to methods of this class.  
   • Keep existing functional API for backward compatibility; just delegate to the new class.
2. 🛠️  **Introduce `config.py`** (dataclass) holding host/port & other future settings.
3. ✅  **Unit tests**  
   • `test_core_initialisation.py` – instantiating `AstGrepMCP` should register ≥5 tools.  
   • `test_run_server.py` – calling `AstGrepMCP().start()` should call `mcp.run()` once (stub with monkeypatch).
4. 🔖 All tests pass; `python main.py serve` still works.

---

## Phase 2 – Robust Error Handling (🕐 ~1 day)
1. 🛠️  **Wrap all tool bodies with structured `try/except`** returning consistent `{error: str}` on failure.  
   • Extract helper `handle_errors` decorator in `ast_grep_mcp.utils`.
2. ✅  **Tests**  
   • Simulate unsupported language => response contains `error` key.  
   • Simulate nonexistent file path for `analyze_file`.
3. 🔖 No uncaught exceptions propagate to FastMCP; tests pass.

---

## Phase 3 – Logging (🕐 <1 day)
1. 🛠️  Add `logging` configuration in `config.py` (levels: DEBUG/INFO/WARNING/ERROR).  
   • Replace `print` calls with `logger`.
2. ✅  Capture logs via `caplog` in tests.
3. 🔖 Log lines appear with selected log level.

---

## Phase 4 – Performance Optimisations (🕐 2 days)
1. 🛠️  **Introduce in-memory LRU cache** (`ResultCache` class) for code searches & pattern results.  
   • Use `functools.lru_cache` or custom OrderedDict impl.
2. 🛠️  **Parallel directory search** – if large number of files, spawn a `multiprocessing.Pool`.
3. ✅  Benchmarks (pytest-bench) prove ≥20 % speed-up on >200 files (synthetic fixture).  
4. 🔖 Cache hit ratio metrics exposed in logs.

---

## Phase 5 – CLI Enhancement (🕐 1 day)
1. 🛠️  Replace `typer` CLI with argument-rich interface (keep Typer but expand).  
   • Add `start`, `interactive`, `version` commands.  
   • Flags: `--log-level`, `--config`.
2. ✅ `pytest` tests call `typer.CliRunner().invoke()`.
3. 🔖 `python main.py --help` shows new commands with descriptions.

---

## Phase 6 – Documentation (🕐 concurrent)
1. 🛠️  Expand `README.md` usage section with CLI examples, tool list.  
2. 🛠️  Create `/docs/` with architecture diagram & demo GIF.  
3. 🔖 Docs review checklist completed.

---

## Phase 7 – Security Hardening (🕐 1 day)
1. 🛠️  Implement `sanitize_pattern` to strip shell metacharacters.  
2. 🛠️  Add directory allow-list (`SAFE_ROOTS`) to prevent arbitrary FS access.  
3. ✅  Tests attempt directory traversal & expect error.
4. 🔖 No dangerous patterns reach `subprocess` layer.

---

## Phase 8 – Extended Language Support (🕐 ongoing)
1. 🛠️  Template handler generator script (`uv run python scripts/new_language.py rust`).  
2. 🛠️  Add at least **Go** & **Rust** handlers.
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