# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Virtual environment setup: `uv venv && source .venv/bin/activate`
- Install dependencies: `uv sync`
- Run server: `python main.py serve`
- Format code: `uv run black .`
- Lint code: `uv run ruff check .`
- Type check: `uv run mypy .`
- Test: `uv run pytest`
- Run single test: `uv run pytest tests/path/to/test.py::test_function_name -v`
- Add dependency: `uv add package-name`
- Add dev dependency: `uv add --dev package-name`

## Code Style

- Use Python 3.10+ features and type hints throughout
- Follow PEP 8 conventions with 88-character line limit (Black)
- Import order: standard library → third-party → local modules
- Class naming: `PascalCase`; Functions/variables: `snake_case`
- Use concrete types (e.g., `list[str]`, not `List[str]`)
- Document public functions with docstrings (Google style)
- Handle errors with specific exceptions and helpful messages
- Prefer composition over inheritance when possible
- All new code should include appropriate tests