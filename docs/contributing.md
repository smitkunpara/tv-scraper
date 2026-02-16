# Contributing to TradingView Scraper

We welcome contributions from the community! This guide will help you get started with contributing to the TradingView Scraper project.

## 🚀 Ways to Contribute

### Code Contributions
- **Bug Fixes**: Fix issues reported in the [issue tracker](https://github.com/smitkunpara/tv-scraper/issues)
- **New Features**: Implement new scraping modules or enhance existing ones
- **Performance Improvements**: Optimize code for better performance
- **Documentation**: Improve documentation, add examples, or fix typos

### Non-Code Contributions
- **Bug Reports**: Report bugs with detailed information
- **Feature Requests**: Suggest new features or improvements
- **Documentation**: Help improve or translate documentation
- **Testing**: Test the library and report issues

## 🛠️ Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- uv (for dependency management)

### Local Development

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/tv-scraper.git
   cd tv-scraper
   ```

2. **Set up Development Environment**
   ```bash
   # Install all dependencies (main + dev tools)
   uv sync --extra dev

   # Install in development mode
   uv pip install -e .
   ```

3. **Run Tests**
   ```bash
   # Run all tests
   uv run pytest

   # Run specific test file
   uv run pytest tests/test_indicators.py
   ```

4. **Build Documentation**
   ```bash
   # Serve docs locally for development
   mkdocs serve

   # Build docs for production
   mkdocs build
   ```

## 🧪 Testing

### Writing Tests
- Write tests for all new features
- Include both positive and negative test cases
- Use descriptive test names
- Mock external API calls when possible

### Test Structure
```python
import pytest
from tv_scraper import Technicals

class TestTechnicals:
    def test_scrape_valid_indicators(self):
        """Test scraping with valid indicators."""
        scraper = Technicals()
        result = scraper.scrape(
            exchange="BINANCE",
            symbol="BTCUSD",
            technical_indicators=["RSI"]
        )
        assert result["status"] == "success"
        assert "RSI" in result["data"]

    def test_scrape_invalid_exchange(self):
        """Test error handling for invalid exchange."""
        scraper = Technicals()
        result = scraper.scrape(
            exchange="INVALID",
            symbol="BTCUSD",
            technical_indicators=["RSI"]
        )
        assert result["status"] == "failed"
```

## 📋 Pull Request Process

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Run Quality Checks**
   ```bash
   # Run tests
   python -m pytest

   # Build documentation
   mkdocs build
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

### Pull Request Guidelines
- Provide a clear description of the changes
- Reference any related issues
- Include screenshots for UI changes
- Ensure all tests pass
- Update documentation if needed

## 🐛 Reporting Bugs

### Bug Report Template
When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**:
   ```python
   # Provide a minimal code example that reproduces the issue
   ```
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - Python version: 3.11
   - OS: Windows 11
   - Library version: 1.0.0

### Example Bug Report
```
**Bug: Technicals scraper fails with timeout**

**Steps to reproduce:**
```python
from tv_scraper import Technicals

scraper = Technicals()
result = scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    technical_indicators=["RSI", "MACD"]
)
```

**Expected:** Should return indicator data
**Actual:** Times out with error
**Environment:** Python 3.11, Windows 11
```

## 💡 Feature Requests

### Feature Request Template
- **Title**: Clear, descriptive title
- **Description**: Detailed description of the proposed feature
- **Use Case**: Explain why this feature would be useful
- **Implementation Ideas**: Optional suggestions for implementation

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/smitkunpara/tv-scraper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/smitkunpara/tv-scraper/discussions)
- **Documentation**: [Full Documentation](https://smitkunpara.github.io/tradingview-scraper/)

## 📜 Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## 🙏 Acknowledgments

Thank you to all contributors who help make TradingView Scraper better! Your time and effort are greatly appreciated.

---

*This contributing guide is adapted from open-source best practices and can be improved. Feel free to suggest changes!*