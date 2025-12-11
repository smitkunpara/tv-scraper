# TradingView Scraper Documentation Guide

## 📚 Documentation Website Setup

This guide provides comprehensive instructions for setting up, serving, and deploying the TradingView Scraper documentation website.

---

## 🚀 Local Development Setup

### Prerequisites

- Python 3.11 or higher
- UV package manager
- Git (optional, for development)

### Installation Steps

```bash
# 1. Clone the repository (if not already cloned)
git clone https://github.com/smitkunpara/tradingview-scraper.git
cd tradingview-scraper

# 2. Create and activate virtual environment
uv venv
source .venv/bin/activate   # Linux/macOS
# OR
.venv\Scripts\activate      # Windows

# 3. Install documentation dependencies
uv pip install mkdocs-material mkdocs-git-revision-date-localized-plugin
```

### Serving Documentation Locally

```bash
# Start the development server
mkdocs serve

# The documentation will be available at:
# http://localhost:8000
```

### Building Documentation

```bash
# Build static site (outputs to 'site' directory)
mkdocs build
```

---

## 🌐 GitHub Pages Deployment

### Automatic Deployment

The documentation is automatically deployed to GitHub Pages using the workflow defined in `.github/workflows/gh-pages.yml`.

**Trigger Conditions:**
- Pushes to `main` or `master` branches
- Changes to documentation files (`docs/**`)
- Changes to `mkdocs.yml`
- Manual workflow dispatch

### Manual Deployment

```bash
# 1. Build the documentation
mkdocs build

# 2. Deploy to GitHub Pages
mkdocs gh-deploy
```

### Deployment Configuration

- **Branch**: `gh-pages`
- **URL**: `https://smitkunpara.github.io/tradingview-scraper/`
- **Build Directory**: `site/`

---

## 📁 Documentation Structure

```
docs/
├── assets/
│   ├── custom.css      # Custom CSS overrides
│   └── custom.js       # Custom JavaScript functionality
├── calendar.md         # Calendar module documentation
├── fundamentals.md     # Fundamental data documentation
├── ideas.md            # Ideas scraper documentation
├── index.md            # Main documentation homepage
├── indicators.md       # Technical indicators documentation
├── installation.md     # Installation guide
├── market_movers.md    # Market movers documentation
├── markets.md          # Markets module documentation
├── minds.md            # Minds community documentation
├── news.md             # News scraping documentation
├── overview.md         # Symbol overview documentation
├── quick_start.md      # Quick start guide
├── realtime.md         # Real-time streaming documentation
├── screener.md         # Screener module documentation
└── supported_data.md   # Supported data reference
```

---

## 🎨 Customization

### CSS Customization

Edit `docs/assets/custom.css` to modify:
- Code block styling
- Admonition appearance
- Table formatting
- Responsive design
- Navigation elements

### JavaScript Customization

Edit `docs/assets/custom.js` to modify:
- Copy button functionality
- Smooth scrolling behavior
- Table of contents toggle
- Interactive elements

---

## 📝 MkDocs Configuration

The main configuration file is `mkdocs.yml` with the following key features:

- **Theme**: Material for MkDocs
- **Navigation**: Left sidebar with all documentation sections
- **Features**: Dark/light mode, search, code highlighting
- **Plugins**: Search, git revision dates
- **Custom Assets**: CSS and JavaScript overrides

---

## 🔧 Troubleshooting

### Common Issues

**Issue: `mkdocs` command not found**
```bash
# Solution: Install MkDocs in your virtual environment
uv pip install mkdocs-material
```

**Issue: Missing dependencies**
```bash
# Solution: Install all required dependencies
uv sync
```

**Issue: Documentation not updating**
```bash
# Solution: Clean and rebuild
mkdocs serve --clean
```

**Issue: GitHub Pages deployment failing**
```bash
# Solution: Check workflow logs and ensure proper permissions
```

---

## 📖 Documentation Standards

All documentation follows the **GLOBAL DOCS STYLE RULES**:

1. **Structure**: Overview → Why → Input → Output → Behavior → Examples → Mistakes → Cross-links
2. **Formatting**: Clean Markdown with MkDocs Material compatibility
3. **Code Examples**: Python code blocks with expected outputs
4. **Admonitions**: Use `!!! note`, `!!! warning` for important information
5. **Environment Setup**: Include UV-based setup instructions

---

## 🔄 Continuous Integration

The GitHub Actions workflow automatically:
- Builds documentation on every push to main/master
- Deploys to GitHub Pages
- Validates documentation structure
- Ensures all dependencies are available

---

## 📈 Analytics and Monitoring

The documentation site includes:
- Search functionality with suggestions
- Navigation tracking
- Git revision dates for content
- Responsive design for all devices

---

## 🎯 Best Practices

1. **Regular Updates**: Keep documentation in sync with code changes
2. **Version Control**: Commit documentation changes with related code changes
3. **Preview Locally**: Always test documentation changes with `mkdocs serve`
4. **Cross-Linking**: Use relative links between documentation pages
5. **Accessibility**: Ensure documentation is accessible and mobile-friendly

---

## 📚 Additional Resources

- [MkDocs Material Documentation](https://squidfunk.github.io/mkdocs-material/)
- [GitHub Pages Documentation](https://pages.github.com/)
- [TradingView Scraper GitHub Repository](https://github.com/smitkunpara/tradingview-scraper)

---

This comprehensive documentation guide provides everything needed to set up, customize, and deploy the TradingView Scraper documentation website following all specified requirements and best practices.