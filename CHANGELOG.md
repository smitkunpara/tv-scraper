# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2025-12-13

### Overview
This release focuses on simplifying the Minds community discussions scraper by removing pagination and improving packaging for cleaner builds.

### Changed
- **Minds API Refactor**: Simplified `Minds.get_minds()` to fetch only the first page of discussions (removed pagination logic for better reliability and performance)
- **API Simplification**: Removed `sort` parameter and `get_all_minds()` method from Minds scraper
- **Build Backend**: Switched from setuptools to hatchling for modern packaging
- **Build Configuration**: Cleaned up `pyproject.toml` by removing setuptools-specific configuration sections and removed obsolete `MANIFEST.in`
- **Package Exclusions**: Ensured clean builds by relying on `.gitignore` for excluding unwanted files (`.vscode`, `__pycache__`, `dist`, etc.)
- **Dependencies**: Removed `setuptools` from runtime dependencies in `setup.py`
- **Documentation**: Updated MkDocs configuration to use proper icon syntax and cleaned up social links
- **Tests**: Streamlined test suite by removing pagination-related tests and sort validation

### Fixed
- **Packaging**: Ensured clean package builds by properly excluding development and cache files

**Full Changelog**: [Commits](https://github.com/smitkunpara/tv-scraper/commits/v0.5.1)

## [0.5.0] - 2025-12-11

### Overview
This is a major release marking a significant overhaul of the project structure, packaging, and documentation. It introduces modern Python tooling support, improved scraping reliability, and a comprehensive documentation rebuild.

### Added
- Modern Packaging with UV: Completely migrated from requirements.txt to pyproject.toml and uv for faster, more reliable dependency management.
- Python 3.11+ Support: Updated codebase and configuration to fully support and enforce Python 3.11+.
- Documentation Overhaul:
  - Rebuilt documentation site with mkdocs-material for a better reading experience.
  - Added comprehensive guides for Contributing, Installation, and architectural overview (CLAUDE.md).
  - Cleaned up old workflows and added new deployment pipelines.
- Ideas Scraper Refactor:
  - Refactored to use the internal JSON API for better stability.
  - Added threading support for faster data retrieval.
  - Implemented cookie authentication to handle Captcha challenges gracefully.
- Streamer Improvements: Fixed volume data handling and improved return types (returning parsed dicts instead of raw generators in specific contexts).
- News Scraper Enhancements: Improved error logging and captcha handling.

### Fixed
- Critical issues with Captcha challenges by adding proper cookie handling.
- Dependency constraints for python-dotenv.
- Documentation build pipelines.

### Changed
- Removed deprecated pkg_resources in favor of importlib.resources.
- Cleaned up codebase structure for better maintainability.

### Removed
- Outdated GitHub workflows for documentation, release, PyPI deployment, and stale issue management.

**Full Changelog**: [Commits](https://github.com/smitkunpara/tv-scraper/commits/v0.4.21)

## [0.4.20] - 2025-12-10

### Changed
- Refactored ideas scraping to use environment variable only.

### Fixed
- Updated python-dotenv version constraint to >=1.0.1 for Python 3.8 compatibility.
- Updated error message for captcha challenge and added python-dotenv dependency.

## [0.4.19]

### Fixed
- Fix raise error while fetching ideas for pages greater than 1.

## [0.4.17]

### Added
- Add Fundamental Graphs feature for comprehensive financial data.
- Support 9 field categories: income statement, balance sheet, cash flow, profitability, liquidity, leverage, margins, valuation, dividends.
- Helper methods for specific financial statements (get_income_statement, get_balance_sheet, get_cash_flow, etc.).
- Multi-symbol comparison with compare_fundamentals() method.
- Support for 60+ fundamental metrics per symbol.

## [0.4.16]

### Added
- Add Minds feature for community discussions and trading ideas.
- Support recent, popular, and trending sort options.
- Pagination support with get_all_minds() method.
- User engagement metrics (likes, comments) and author information.

## [0.4.15]

### Added
- Add Symbol Overview feature for comprehensive symbol data.
- Support for profile, statistics, financials, performance, and technical data.
- 9 field categories with 70+ data points per symbol.
- Helper methods for specific data categories.

## [0.4.14]

### Added
- Add Markets Overview feature for top stocks analysis.
- Sort by market cap, volume, change, price, volatility.
- Support 9 markets (America, Australia, Canada, Germany, India, UK, Crypto, Forex, Global).

## [0.4.13]

### Added
- Add Symbol Markets feature to find all exchanges/markets where a symbol is traded.
- Support global, regional (America, Crypto, Forex, CFD) market scanners.
- Discover stocks, crypto, derivatives across 100+ exchanges worldwide.

## [0.4.12]

### Added
- Add Screener functionality with custom filters, sorting, and column selection.
- Support 18 markets (America, Canada, Germany, India, UK, Crypto, Forex, CFD, Futures, Bonds, etc.).
- Support 15+ filter operations (greater, less, equal, in_range, crosses, etc.).

## [0.4.11]

### Added
- Add Market Movers scraper (Gainers, Losers, Penny Stocks, Pre-market/After-hours movers).
- Support multiple markets (USA, UK, India, Australia, Canada, Crypto, Forex, Bonds, Futures).

## [0.4.9]

### Added
- Add [documentation](https://mnwato.github.io/tradingview-scraper/).

## [0.4.8]

### Fixed
- Fix bug while fetching ADX+DI indicators.

### Added
- Add timeframe param for streamer export data.

## [0.4.7]

### Fixed
- Fix bug undefined RealTimeData class.

## [0.4.6]

### Added
- Add value argument to specify calendar fields.
- Add Streamer class for getting OHLCV and indicator simultaneously.
- Integrate realtime data and historical exporter into Streamer class.

## [0.4.2]

### Added
- Add calendar (Dividend, Earning).
- Make requirements non-explicit.
- Lint fix.
- Add tests (ideas, realtime_price, indicators).
- Add reconnection method for realtime price scraper.

## [0.4.0]

### Added
- Update exchange list.
- Add real-time price streaming.

## [0.3.2]

### Added
- Support timeframe to get Indicators.

## [0.3.0]

### Added
- Add news scraper.

## [0.2.9]

### Changed
- Refactor for new TradingView structure.

## [0.1.0]

### Changed
- The name of `ClassA` changed to `Ideas`.