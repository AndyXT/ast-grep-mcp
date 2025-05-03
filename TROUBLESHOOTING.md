# Troubleshooting Guide

## Common Issues

### ast-grep-py Installation Problems

The `ast-grep-py` package is a Rust-based Python binding that requires compilation during installation. This can sometimes cause issues, especially with newer Python versions.

#### Known Issues:

1. **Python 3.13 Compatibility**: Early versions of `ast-grep-py` had issues with Python 3.13. We now use version 0.37.0 which fixes these problems.

2. **Rust Compiler Errors**: If you see errors related to `OnceLock` or other Rust features, you may need to update your Rust toolchain:

   ```bash
   rustup update stable
   ```

3. **Cached Installations**: Sometimes cached installations can cause problems. Try clearing the cache:

   ```bash
   rm -rf ~/.cache/pip ~/.cache/uv
   ```

#### Solutions:

1. **Use the helper script**: We provide a helper script that performs a clean installation:

   ```bash
   ./scripts/install_deps.sh
   ```

2. **Manual installation steps**:

   ```bash
   # Activate your virtual environment
   source .venv/bin/activate
   
   # Install ast-grep-py first, separately
   uv pip install ast-grep-py==0.37.0 --verbose
   
   # Then install remaining dependencies
   uv sync --dev
   ```

3. **Verify installation**:

   ```bash
   python -c "from ast_grep_py import SgRoot; print('Successfully imported SgRoot')"
   ```

## CI/GitHub Actions Issues

If you're seeing CI failures related to dependencies:

1. Check the CI logs for specific error messages
2. Make sure the Rust toolchain is properly set up (our workflow uses `dtolnay/rust-toolchain@stable`)
3. Ensure `ast-grep-py` is installed before other dependencies 

## Getting Help

If you continue to experience issues:

1. Check the [ast-grep GitHub repository](https://github.com/ast-grep/ast-grep) for known issues
2. Consult the [ast-grep-py PyPI page](https://pypi.org/project/ast-grep-py/) for the latest version information
3. Open an issue in our repository with detailed error logs 