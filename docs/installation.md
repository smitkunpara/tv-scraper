# Installation Guide

## Overview

This guide provides step-by-step instructions for installing and setting up the TradingView Scraper library using UV, the recommended package manager for Python projects.

## Why This Installation Method Exists

The UV-based installation method exists to:

- Provide a fast, reliable dependency management system
- Ensure consistent environments across different platforms
- Simplify dependency resolution and virtual environment management
- Support modern Python development workflows
- Enable easy project setup and maintenance

## Prerequisites

Before installing the TradingView Scraper, ensure you have:

- **Python 3.11 or higher** installed
- **UV** package manager installed
- **Git** (optional, for development setup)

## Installation Steps

### 1. Install UV

If you don't have UV installed, install it first:

```bash
# On Windows
winget install --id=astral-sh.uv -e

# On macOS/Linux (using pip)
pip install uv
```

### 2. Clone the Repository (Development Setup)

For development or contribution purposes:

```bash
git clone https://github.com/smitkunpara/tradingview-scraper.git
cd tradingview-scraper
```

### 3. Create Virtual Environment

Create and activate a virtual environment using UV:

```bash
# Create virtual environment
uv venv

# Activate the environment
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 4. Install Dependencies

Install the required dependencies using UV:

```bash
# Install core dependencies
uv sync

# For development with testing capabilities
uv sync --extra test
```

### 5. Verify Installation

Verify that the installation was successful:

```bash
python -c "from tradingview_scraper import __version__; print(f'TradingView Scraper v{__version__}')"
```

## Environment Variables

The library supports several environment variables for configuration:

- `TRADINGVIEW_JWT_TOKEN`: Required for real-time streaming functionality
- Custom environment variables can be set in `.env` file

## Upgrading

To upgrade to the latest version:

```bash
# Pull the latest changes
git pull origin main

# Update dependencies
uv sync
```

## Troubleshooting

### Common Installation Issues

#### Issue: UV command not found

**Solution**: Ensure UV is properly installed and added to your PATH.

#### Issue: Python version incompatible

**Solution**: Install Python 3.11 or higher and ensure it's the default Python version.

#### Issue: Dependency conflicts

**Solution**: Create a fresh virtual environment and run `uv sync` again.

#### Issue: Missing system dependencies

**Solution**: Install required system libraries (e.g., `libssl-dev` on Linux).

## Environment Setup for Documentation

To preview the documentation locally:

```bash
# Install MkDocs and dependencies
uv add mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve
```

The documentation will be available at `http://localhost:8000`.

## Environment Setup Summary

```bash
# Complete setup commands
uv venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
uv sync
```

This installation guide provides all necessary information to set up the TradingView Scraper library using UV. Refer to the specific module documentation for detailed usage instructions.