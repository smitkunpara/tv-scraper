# Local Workflow Testing Guide

This guide shows you how to test your code locally before pushing to GitHub, mimicking what the CI/CD pipeline will do.

## 🎯 Quick Start

### Option 1: Use the Makefile (Recommended)

The project now includes a `Makefile` with convenient shortcuts:

```bash
# Show all available commands
make help

# Run all quality checks (lint, format, type-check, test)
make check

# Full CI simulation with coverage
make ci

# Individual commands
make lint          # Run ruff linter
make format        # Auto-format code
make format-check  # Check formatting without modifying
make type-check    # Run mypy type checker
make test          # Run unit and integration tests
make test-cov      # Tests with coverage report
make test-all      # Run all tests including live API tests
```

**Typical workflow:**
```bash
# Before committing:
make check

# Before pushing (full CI simulation):
make ci
```

### Option 2: Manual Commands

If you prefer to run commands directly:

```bash
# Linting
uv run ruff check tv_scraper/

# Formatting
uv run ruff format tv_scraper/

# Type checking
uv run mypy tv_scraper/

# Testing
uv run pytest tests/unit tests/integration -v

# Testing with coverage
uv run pytest tests/unit tests/integration -v --cov=tv_scraper --cov-report=term-missing
```

## 🪝 Pre-commit Hooks (Automatic Checks)

Pre-commit hooks are **already installed** and will run automatically on every commit!

### What happens on commit:
1. ✅ Ruff auto-fixes linting issues
2. ✅ Ruff formats your code
3. ✅ Removes trailing whitespace
4. ✅ Fixes end-of-file issues
5. ✅ Validates YAML files
6. ✅ Checks for large files

If any check fails, the commit is **blocked** until you fix the issues.

### Manual pre-commit testing:
```bash
# Run hooks on all files
uv run pre-commit run --all-files

# Run hooks only on staged files
uv run pre-commit run

# Skip hooks for a single commit (not recommended)
git commit --no-verify -m "your message"
```

## 🐳 Act - Full GitHub Actions Simulation

**Act** allows you to run your entire `.github/workflows/test.yml` workflow locally using Docker.

### Installation Status
✅ **act** is installed (v0.2.84)
⚠️ **Docker** is **NOT** installed (required for act to work)

### To install Docker:
```bash
# Option 1: Docker Desktop (recommended for ease of use)
# Download from: https://docs.docker.com/desktop/install/linux/

# Option 2: Docker Engine via apt
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER
# Then logout and login again
```

### Using act (after Docker is installed):

```bash
# List all workflows
act -l

# Run the 'test' workflow (dry-run)
act -n

# Run the actual workflow
act push

# Run with specific job
act -j test

# Run with a specific event
act pull_request
```

**Note:** act uses Docker images to simulate GitHub's runners, so the first run will download ~1GB of images.

### act Configuration
Create `.actrc` in your home directory for custom settings:
```bash
# Use a smaller Docker image (faster)
-P ubuntu-latest=catthehacker/ubuntu:act-latest
```

## 🔄 Workflow Comparison

| Method | Speed | Accuracy | Auto-runs | CI Simulation |
|--------|-------|----------|-----------|---------------|
| **Makefile** | ⚡ Fast | Good | No | 90% |
| **Pre-commit** | ⚡ Very Fast | Good | ✅ On commit | 60% |
| **Act** | 🐌 Slow | Excellent | No | 100% |

### Recommended Workflow:
1. **Code** → Let pre-commit hooks catch basic issues
2. **Before pushing** → Run `make ci` for full local validation
3. **Optional** → Run `act push` for perfect CI simulation (if Docker installed)

## 📊 Understanding Output

### Ruff Errors
```bash
104 errors found
- E501: Line too long (informational)
- RUF012: Mutable class default (should fix)
- PLR2004: Magic value comparison (style preference)
```

Most errors are **non-critical** style issues. Your CI is configured to continue even with these warnings.

### Test Coverage
Current coverage: **89%**
```
TOTAL: 1354 lines, 154 not covered
```

### Type Checking
Mypy is set to `strict = true` but `continue-on-error: true` in CI, so type issues won't block your builds initially.

## 🆘 Troubleshooting

### "Failed to spawn: pytest"
```bash
uv pip install pytest pytest-mock pytest-cov
```

### "Failed to spawn: ruff"
```bash
uv add --dev ruff mypy pre-commit
```

### Pre-commit hooks not running
```bash
# Reinstall hooks
uv run pre-commit install

# Check status
uv run pre-commit --version
```

### act "Cannot connect to Docker daemon"
Docker service is not running:
```bash
sudo systemctl start docker
```

## 📝 Summary

You now have **three layers** of quality assurance:

1. 🪝 **Pre-commit hooks** - Automatic on every commit
2. 🎯 **Makefile commands** - Fast local validation (`make check`)
3. 🐳 **Act** - Full CI simulation (requires Docker)

**Before every push, run:**
```bash
make ci
```

This ensures your code will pass GitHub Actions CI! 🚀
