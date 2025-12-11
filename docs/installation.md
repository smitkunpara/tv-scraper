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

### 3. Install Dependencies

Install the required dependencies using UV:

```bash
# Install core dependencies
uv sync

# For development with testing capabilities
uv sync --extra test
```

### 4. Verify Installation

Verify that the installation was successful:

```bash
python -c "from tradingview_scraper import __version__; print(f'TradingView Scraper v{__version__}')"
```

## Upgrading

To upgrade to the latest version:

```bash
# Pull the latest changes
git pull origin main

# Update dependencies
uv sync
```



This installation guide provides all necessary information to set up the TradingView Scraper library using UV. Refer to the specific module documentation for detailed usage instructions.