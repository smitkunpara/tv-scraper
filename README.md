# TV Scraper

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/github/license/smitkunpara/tv-scraper.svg?color=brightgreen)](https://opensource.org/licenses/MIT)

**A powerful, real-time Python library for extracting financial data, indicators, and ideas from TradingView.com.**

> 🔥 New in v1.3.2: Streamer now uses TradingView session cookies for automated indicator authentication. This ensures continuous streaming by automatically renewing expiring tokens and is required for personal Pine script verification.

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


## ✨ Key Features

- **🕯️ Candle + Indicators**: Stream OHLCV candles with built-in/custom indicators via [`Streamer.get_candles()`](https://smitkunpara.github.io/tv-scraper/streaming/streamer/).
- **📈 Forecast Data**: Fetch analyst price targets and EPS/revenue estimates for stocks via [`Streamer.get_forecast()`](https://smitkunpara.github.io/tv-scraper/streaming/streamer/).
- **💡 Ideas**: Scrape community trading ideas with [`Ideas`](https://smitkunpara.github.io/tv-scraper/scrapers/ideas/).
- **🧠 Minds**: Access TradingView discussions with [`Minds`](https://smitkunpara.github.io/tv-scraper/scrapers/minds/).
- **📰 News**: Fetch market headlines and filters with [`News`](https://smitkunpara.github.io/tv-scraper/scrapers/news/).
- **📉 Options Data**: Retrieve option chains, Greeks, implied volatility, and theoretical prices via [`Options`](https://smitkunpara.github.io/tv-scraper/scrapers/options/).
- **🔎 Screener**: Run market scans with custom fields/filters via [`Screener`](https://smitkunpara.github.io/tv-scraper/scrapers/screener/).
- **🏁 Market Movers**: Track top gainers/losers and actives via [`Market Movers`](https://smitkunpara.github.io/tv-scraper/scrapers/market_movers/).
- **📊 Fundamentals**: Get financial statements and ratios via [`Fundamentals`](https://smitkunpara.github.io/tv-scraper/scrapers/fundamentals/).
- **🧩 Pine Workflow**: Manage custom scripts with [`Pine`](https://smitkunpara.github.io/tv-scraper/scrapers/pine/) and stream them through `Streamer`.
- **📋 API Contract**: Consistent `status/data/metadata/error` response envelope across modules ([API conventions](https://smitkunpara.github.io/tv-scraper/api-conventions/)).


---

## 🛠️ Development & Testing

For contributors and developers, use the Development Guide:

- [🛠️ Development Guide](https://smitkunpara.github.io/tv-scraper/contributing/)

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://smitkunpara.github.io/tv-scraper/contributing/) for details.

- **🐛 Bug Reports**: [Open an issue](https://github.com/smitkunpara/tv-scraper/issues)
- **💡 Feature Requests**: [Start a discussion](https://github.com/smitkunpara/tv-scraper/discussions)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
