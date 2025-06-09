"""
Main entry point for ast-grep-mcp when used as a module.
This allows the package to be run with `python -m ast_grep_mcp`.
"""

import sys
from pathlib import Path
import importlib.util

# Add the parent directory to the path to ensure main.py can be found
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Dynamically import main.py
main_path = Path(__file__).resolve().parent.parent.parent / "main.py"
spec = importlib.util.spec_from_file_location("main", main_path)
main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)


def main_entry_point():
    """
    Entry point for the console script defined in pyproject.toml.
    This function is called when the tool is run as "ast-grep-mcp" from the command line.
    """
    return main_module.main()


if __name__ == "__main__":
    main_module.main()
