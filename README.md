
# TV Scraper

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/github/license/smitkunpara/tv-scraper.svg?color=brightgreen)](https://opensource.org/licenses/MIT)

**A powerful, real-time Python library for extracting financial data, indicators, and ideas from TradingView.com.**

---

## Attribution

This project is based on [mnwato/tradingview-scraper](https://github.com/mnwato/tradingview-scraper). Thanks to the original author for the foundational work.

## 📚 Documentation

For complete documentation, installation guides, API references, and examples, visit:

**[📖 Full Documentation](https://smitkunpara.github.io/tv-scraper/)**

### Quick Links
- [🚀 Quick Start Guide](https://smitkunpara.github.io/tv-scraper/quick_start/)
- [📦 Installation](https://smitkunpara.github.io/tv-scraper/installation/)
- [📊 Supported Data](https://smitkunpara.github.io/tv-scraper/supported_data/)
- [🔧 API Reference](https://smitkunpara.github.io/tv-scraper/)

---

## 🚀 Quick Start

This library requires Python 3.11+ and uses `uv` for dependency management.

### Installation

```bash
# Clone the repository
git clone https://github.com/smitkunpara/tv-scraper.git
cd tv-scraper

# Install dependencies (uv auto-creates virtual environment)
uv sync
```

### Basic Usage Examples

#### Fetching Technical Indicators

Get RSI and Stochastic indicators for Bitcoin on Binance:

```python
from tv_scraper import Technicals

# Initialize scraper
technicals = Technicals()

# Scrape indicators for BTCUSD
result = technicals.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    timeframe="1d",
    technical_indicators=["RSI", "Stoch.K"]
)

if result["status"] == "success":
    print(result["data"])
```

#### Scraping Trading Ideas

Get popular trading ideas for Ethereum:

```python
from tv_scraper import Ideas

# Initialize scraper
ideas = Ideas()

# Scrape popular ideas for ETHUSD
result = ideas.scrape(
    exchange="CRYPTO",
    symbol="ETHUSD",
    start_page=1,
    end_page=1,
    sort_by="popular"
)

if result["status"] == "success":
    print(f"Found {len(result['data'])} ideas.")
```

## ✨ Key Features

- **📊 Real-Time Data**: Stream live OHLCV and indicator values via WebSocket
- **📰 Comprehensive Coverage**: Scrape Ideas, News, Market Movers, and Screener data
- **📈 Fundamental Data**: Access detailed financial statements and profitability ratios
- **🔧 Advanced Tools**: Symbol Markets lookup, Symbol Overview, and Minds Community discussions
- **📋 Structured Output**: All data returned as clean JSON/Python dictionaries
- **🌍 Multi-Market Support**: 260+ exchanges across stocks, crypto, forex, and commodities
- **⚡ Fast & Reliable**: Built with async support and robust error handling

## 📋 What's Included

### Core Modules
- **Indicators**: 81+ technical indicators (RSI, MACD, Stochastic, etc.)
- **Options**: Fetch option chains by expiration or strike price
- **Ideas**: Community trading ideas and strategies
- **News**: Financial news with provider filtering
- **Real-Time**: WebSocket streaming for live data
- **Screener**: Advanced stock screening with custom filters
- **Market Movers**: Top gainers, losers, and active stocks
- **Fundamentals**: Financial statements and ratios
- **Calendar**: Earnings and dividend events

### Data Sources
- **260+ Exchanges**: Binance, Coinbase, NASDAQ, NYSE, and more
- **16+ Markets**: Stocks, Crypto, Forex, Futures, Bonds
- **Real-Time Updates**: Live price feeds and indicators
- **Historical Data**: Backtesting and analysis support

---

## 🛠️ Development & Testing

For contributors and developers, this project includes comprehensive tooling for local testing.

### Quick Commands

```bash
# Run all quality checks before committing
make check

# Full CI simulation with coverage
make ci

# Individual checks
make lint          # Run ruff linter
make format        # Auto-format code
make type-check    # Run mypy type checker
make test          # Run tests
```

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit to enforce code quality:
```bash
# Install hooks (one-time setup)
make install-hooks
```

### Full Documentation

See [LOCAL_TESTING.md](LOCAL_TESTING.md) for complete details on:
- Makefile commands
- Pre-commit hook configuration
- Running GitHub Actions locally with act
- CI/CD workflow testing

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://smitkunpara.github.io/tv-scraper/contributing/) for details.

- **🐛 Bug Reports**: [Open an issue](https://github.com/smitkunpara/tv-scraper/issues)
- **💡 Feature Requests**: [Start a discussion](https://github.com/smitkunpara/tv-scraper/discussions)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
